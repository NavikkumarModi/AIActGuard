from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from .risk_classifier import RiskTier


@dataclass
class ApprovalContext:
    """What an approver sees when deciding whether a gated action may proceed."""

    action: str
    category: str
    risk_tier: RiskTier
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class ApprovalDecision:
    """An approver's decision. `override=True` marks a decision that
    consciously overrides the gate's default-deny posture and should carry
    a `reason` (enforced by policy — see GateRule.require_reason_on_override)."""

    approved: bool
    approver_id: str
    reason: Optional[str] = None
    override: bool = False


Approver = Callable[[ApprovalContext], Optional[ApprovalDecision]]


class ApprovalGate:
    """An ordered escalation chain of approvers (Art. 14). `decide()` tries
    each approver in turn; the first to return a non-None decision wins.
    An approver returning None means "not my call" — e.g. out of hours,
    outside their authority — and escalates to the next in the chain.
    If nobody in the chain responds, the action is denied.
    """

    def __init__(self, approvers: Optional[list[Approver]] = None):
        self._approvers = approvers or []

    def decide(self, context: ApprovalContext) -> ApprovalDecision:
        for approver in self._approvers:
            decision = approver(context)
            if decision is not None:
                return decision

        return ApprovalDecision(
            approved=False,
            approver_id="none",
            reason="No approver in the escalation chain responded.",
        )
