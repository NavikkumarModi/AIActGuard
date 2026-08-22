from __future__ import annotations

from dataclasses import dataclass

from ..storage.base import AuditRecord
from ._predmix import predmix_empbern_twosided_cs
from .bins import bin_index
from .findings import AuditFindingStore

_MIN_FINDINGS_FOR_ESTIMATE = 5


def compute_bin_ucb(outcomes: list[bool], *, alpha: float = 0.1) -> float:
    """Anytime-valid upper confidence bound on the true violation rate
    given the ground-truth outcomes observed so far for one confidence
    bin. Fewer than 5 findings returns 1.0 (maximal uncertainty) rather
    than a bound computed from too little evidence to mean anything —
    the same conservative default the reference implementation uses.
    Valid to check after every new finding, not just at a pre-planned
    sample size — that's what "anytime-valid" buys here."""
    if len(outcomes) < _MIN_FINDINGS_FOR_ESTIMATE:
        return 1.0
    x = [1.0 if outcome else 0.0 for outcome in outcomes]
    _, upper = predmix_empbern_twosided_cs(x, alpha=alpha)
    return float(upper[-1])


@dataclass
class PriorityItem:
    record: AuditRecord
    bin: int
    ucb: float
    already_reviewed: bool


def prioritize_for_review(
    records: list[AuditRecord],
    findings_store: AuditFindingStore,
    *,
    n_bins: int = 10,
    alpha: float = 0.1,
) -> list[PriorityItem]:
    """Rank `records` by how uncertain we are about their confidence bin's
    true violation rate — highest first. A bin with no or sparse ground-
    truth findings ranks at the top (maximal uncertainty); as findings
    accumulate showing a bin is actually safe, its bound tightens and its
    records fall in priority automatically. Records without a
    `classifier_confidence` (e.g. pre-upgrade rows) are skipped — there's
    no bin to place them in.

    This ranks; it never approves, blocks, or removes anything from
    review. A record with the highest ucb still requires a human to
    actually look at it — this just says which ones to look at first.
    """
    outcomes_by_record_id = findings_store.outcomes_by_record_id()

    bin_outcomes: dict[int, list[bool]] = {i: [] for i in range(n_bins)}
    for record in records:
        if record.classifier_confidence is None:
            continue
        outcome = outcomes_by_record_id.get(record.record_id)
        if outcome is not None:
            bin_outcomes[bin_index(record.classifier_confidence, n_bins)].append(outcome)

    bin_ucb = {i: compute_bin_ucb(outcomes, alpha=alpha) for i, outcomes in bin_outcomes.items()}

    items = [
        PriorityItem(
            record=record,
            bin=bin_index(record.classifier_confidence, n_bins),
            ucb=bin_ucb[bin_index(record.classifier_confidence, n_bins)],
            already_reviewed=record.record_id in outcomes_by_record_id,
        )
        for record in records
        if record.classifier_confidence is not None
    ]
    items.sort(key=lambda item: item.ucb, reverse=True)
    return items
