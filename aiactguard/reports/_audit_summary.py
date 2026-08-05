from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Optional

from ..storage.base import AuditRecord


@dataclass
class AuditSummary:
    """Aggregate stats over a slice of the audit trail — the numbers every
    Phase 2 report draws from instead of re-querying/re-counting records."""

    total_actions: int
    gated_count: int
    approved_count: int
    denied_count: int
    override_count: int
    by_risk_tier: dict[str, int] = field(default_factory=dict)
    by_category: dict[str, int] = field(default_factory=dict)
    earliest_timestamp: Optional[str] = None
    latest_timestamp: Optional[str] = None


def summarize(records: list[AuditRecord]) -> AuditSummary:
    if not records:
        return AuditSummary(total_actions=0, gated_count=0, approved_count=0, denied_count=0, override_count=0)

    timestamps = sorted(r.timestamp for r in records)

    return AuditSummary(
        total_actions=len(records),
        gated_count=sum(1 for r in records if r.gated),
        approved_count=sum(1 for r in records if r.approved),
        denied_count=sum(1 for r in records if not r.approved),
        override_count=sum(1 for r in records if r.override),
        by_risk_tier=dict(Counter(r.risk_tier for r in records)),
        by_category=dict(Counter(r.category for r in records)),
        earliest_timestamp=timestamps[0],
        latest_timestamp=timestamps[-1],
    )
