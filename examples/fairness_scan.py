"""Run a disparate-impact fairness scan over a synthetic set of decisions.

Requires: pip install aiactguard
"""

from aiactguard.testing.fairness_scan import GroupOutcome, compute_disparate_impact

# A synthetic dataset: region_a is approved far more often than region_b —
# a proxy grouping you'd normally derive from `AuditRecord.inputs` via
# `scan_audit_trail(logger, group_key=...)` on real data.
outcomes = (
    [GroupOutcome(group="region_a", approved=True) for _ in range(18)]
    + [GroupOutcome(group="region_a", approved=False) for _ in range(2)]
    + [GroupOutcome(group="region_b", approved=True) for _ in range(9)]
    + [GroupOutcome(group="region_b", approved=False) for _ in range(11)]
)

result = compute_disparate_impact(outcomes, threshold=0.8)
print(result.to_markdown())
