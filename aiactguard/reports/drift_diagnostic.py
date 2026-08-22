from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..audit_priority.bins import bin_index
from ..audit_priority.findings import AuditFindingStore
from ..core.audit_logger import AuditLogger
from ..core.markdown import MarkdownReport
from ..core.questionnaire import Questionnaire, render_field

_HIGH_EXPOSURE_CLASSES = {"irreversible_financial", "irreversible_data", "irreversible_external_comms"}
_MIN_FINDINGS_FOR_RATE = 5


@dataclass
class _BinStats:
    bin: int
    p_bin: float
    n_records: int
    n_findings: int
    true_risk_rate: Optional[float] = None
    miss_rate: Optional[float] = None
    p_high_exposure: Optional[float] = None
    silent_risk_mass: Optional[float] = None

    @property
    def insufficient_data(self) -> bool:
        return self.n_findings < _MIN_FINDINGS_FOR_RATE


def _compute_bin_stats(records: list, outcomes_by_record_id: dict, total: int, n_bins: int) -> list[_BinStats]:
    grouped: dict[int, list] = {i: [] for i in range(n_bins)}
    for record in records:
        if record.classifier_confidence is not None:
            grouped[bin_index(record.classifier_confidence, n_bins)].append(record)

    stats = []
    for b in range(n_bins):
        bin_records = grouped[b]
        if not bin_records:
            continue

        findings = [(r, outcomes_by_record_id[r.record_id]) for r in bin_records if r.record_id in outcomes_by_record_id]
        p_bin = len(bin_records) / total if total else 0.0
        entry = _BinStats(bin=b, p_bin=p_bin, n_records=len(bin_records), n_findings=len(findings))

        if len(findings) >= _MIN_FINDINGS_FOR_RATE:
            true_violations = [r for r, is_violation in findings if is_violation]
            entry.true_risk_rate = len(true_violations) / len(findings)
            missed = [r for r in true_violations if not r.gated]
            entry.miss_rate = (len(missed) / len(true_violations)) if true_violations else 0.0
            high_exposure_count = sum(1 for r in bin_records if r.action_exposure_class in _HIGH_EXPOSURE_CLASSES)
            entry.p_high_exposure = high_exposure_count / len(bin_records)
            entry.silent_risk_mass = entry.p_bin * entry.true_risk_rate * entry.miss_rate * entry.p_high_exposure

        stats.append(entry)

    return stats


def generate_drift_diagnostic(
    logger: AuditLogger,
    findings_store: AuditFindingStore,
    *,
    questionnaire: Optional[Questionnaire] = None,
    category: Optional[str] = None,
    n_bins: int = 10,
) -> str:
    """A monitoring report, not a gate: decomposes where "silent risk mass"
    concentrates across confidence bins, and checks whether the agent shows
    an elevated preference for high-exposure actions specifically in bins
    where the classifier tends to miss true violations.

    Based on the violation-rate decomposition from the user's own research
    on adaptively-routed agent systems:

        ViolationRate = P(bin) x true_risk_rate(bin) x classifier_miss_rate(bin)
                        x P(high_exposure_action | bin)

    `true_risk_rate` and `classifier_miss_rate` need ground-truth findings
    (see `aiactguard.audit_priority.findings.AuditFindingStore`) to compute
    — a bin with fewer than 5 findings is marked insufficient data rather
    than given a fabricated rate. This is a diagnostic signal for a
    compliance team to review periodically; it doesn't block, gate, or
    determine anything on its own.
    """
    records = logger.query(category=category, limit=10_000)
    outcomes_by_record_id = findings_store.outcomes_by_record_id()
    stats = _compute_bin_stats(records, outcomes_by_record_id, total=len(records), n_bins=n_bins)

    out = MarkdownReport("Drift diagnostic (research-backed, monitoring only)")
    out.note(
        "This decomposes where 'silent risk mass' concentrates across confidence "
        "bins — it's a monitoring signal for a compliance team to look at "
        "periodically, not a gate and not a guarantee. A bin with too few "
        "ground-truth findings is marked insufficient data rather than given a "
        "fabricated rate."
    )
    out.field("System", render_field(questionnaire, "system_name", "System name"))
    out.blank()

    out.heading("Per-bin decomposition")
    out.line("`ViolationRate = P(bin) x true_risk_rate(bin) x classifier_miss_rate(bin) x P(high_exposure | bin)`")
    out.blank()
    if not stats:
        out.bullet("No audit records with classifier_confidence found yet.")
    for entry in stats:
        if entry.insufficient_data:
            out.bullet(
                f"bin {entry.bin}: {entry.n_records} record(s), {entry.p_bin:.0%} of traffic — "
                f"insufficient data ({entry.n_findings}/{_MIN_FINDINGS_FOR_RATE} findings needed)"
            )
        else:
            out.bullet(
                f"bin {entry.bin}: {entry.n_records} record(s), {entry.p_bin:.0%} of traffic — "
                f"true_risk_rate={entry.true_risk_rate:.0%}, miss_rate={entry.miss_rate:.0%}, "
                f"P(high_exposure)={entry.p_high_exposure:.0%} — "
                f"silent_risk_mass={entry.silent_risk_mass:.4f}"
            )
    out.blank()

    scored = [e for e in stats if not e.insufficient_data]
    if scored:
        top = sorted(scored, key=lambda e: e.silent_risk_mass, reverse=True)[:3]
        out.heading("Bins concentrating the most silent risk mass")
        for entry in top:
            out.bullet(f"bin {entry.bin}: silent_risk_mass={entry.silent_risk_mass:.4f}")
        out.blank()

        high_miss = [e for e in scored if e.miss_rate > 0.3]
        low_miss = [e for e in scored if e.miss_rate <= 0.3]
        out.heading("Blind-spot alignment check")
        if high_miss and low_miss:
            high_miss_exposure = sum(e.p_high_exposure for e in high_miss) / len(high_miss)
            low_miss_exposure = sum(e.p_high_exposure for e in low_miss) / len(low_miss)
            out.field("Avg P(high_exposure) in high-miss-rate bins (>30% missed)", f"{high_miss_exposure:.0%}")
            out.field("Avg P(high_exposure) in lower-miss-rate bins", f"{low_miss_exposure:.0%}")
            if high_miss_exposure > low_miss_exposure:
                out.note(
                    "The agent shows a higher rate of high-exposure actions specifically in bins "
                    "where the classifier tends to miss true violations — worth a closer look, not "
                    "an automatic conclusion of anything."
                )
        else:
            out.bullet("Not enough scored bins in both groups yet to compare.")
    else:
        out.bullet("No bins have enough ground-truth findings yet to compute the decomposition.")

    return out.build()
