from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from ..policy.schema import ApprovalRequired, PolicyConfig
from .approval import ApprovalContext, ApprovalDecision, ApprovalGate, Approver
from .audit_logger import AuditLogger
from .risk_classifier import RiskClassifier, RiskTier


@dataclass
class GuardEvaluation:
    """The result of a classify -> gate decision, before anything is logged."""

    approved: bool
    gated: bool
    risk_tier: RiskTier
    decision: Optional[ApprovalDecision] = None

    @property
    def denial_reason(self) -> Optional[str]:
        if self.approved:
            return None
        return self.decision.reason if self.decision else "no approver responded"


@dataclass
class GuardOutcome(GuardEvaluation):
    record: Any = None  # AuditRecord, set once logged


class GuardCore:
    """Shared classify -> gate -> log pipeline used by every integration
    surface (the `watch` decorator, and each framework adapter) so the
    approval/audit behavior is defined once and stays consistent.

    Two entry points, for two shapes of integration:
    - `evaluate()` only classifies + gates (no logging) — use this when you
      still need to run the action and want a single audit record covering
      both the gate decision and the execution result (see `watch()`).
    - `evaluate_and_log()` classifies, gates, and logs immediately, raising
      on denial — use this when the integration only observes a "before the
      action fires" event and has no way to merge in a result afterward
      (framework adapters hooking a pre-tool-call callback).
    """

    def __init__(
        self,
        *,
        category: str,
        classifier: Optional[RiskClassifier] = None,
        logger: Optional[AuditLogger] = None,
        policy: Optional[PolicyConfig] = None,
        gate: Optional[ApprovalGate] = None,
        approvers: Optional[list[Approver]] = None,
        model_version: Optional[str] = None,
    ):
        self.category = category
        self.classifier = classifier or RiskClassifier.default()
        self.logger = logger or AuditLogger.default()
        self.policy = policy or PolicyConfig.default()
        self.gate = gate or ApprovalGate(approvers)
        self.model_version = model_version

    def evaluate(
        self,
        *,
        action: str,
        text_for_classification: Optional[str] = None,
        inputs: Optional[dict[str, Any]] = None,
    ) -> GuardEvaluation:
        risk_tier = self.classifier.classify(self.category, text=text_for_classification)
        rule = self.policy.matching_rule(category=self.category, risk_tier=risk_tier)

        if rule is None:
            return GuardEvaluation(approved=True, gated=False, risk_tier=risk_tier)

        context = ApprovalContext(
            action=action, category=self.category, risk_tier=risk_tier, payload=inputs or {}
        )
        decision = self.gate.decide(context)
        approved = decision.approved

        if decision.override and rule.require_reason_on_override and not decision.reason:
            approved = False
            decision = ApprovalDecision(
                approved=False,
                approver_id=decision.approver_id,
                reason="Override rejected: a reason is required to override this gate.",
                override=True,
            )

        return GuardEvaluation(approved=approved, gated=True, risk_tier=risk_tier, decision=decision)

    def log(
        self,
        evaluation: GuardEvaluation,
        *,
        action: str,
        inputs: Optional[dict[str, Any]] = None,
        outputs: Optional[str] = None,
        rationale: Optional[list[dict[str, Any]]] = None,
    ) -> GuardOutcome:
        decision = evaluation.decision
        record = self.logger.log(
            action=action,
            category=self.category,
            risk_tier=evaluation.risk_tier,
            inputs=inputs or {},
            outputs=outputs if evaluation.approved else None,
            model_version=self.model_version,
            approved=evaluation.approved,
            gated=evaluation.gated,
            error=None if evaluation.approved else evaluation.denial_reason,
            approver_id=decision.approver_id if decision else None,
            override=decision.override if decision else False,
            reason=decision.reason if decision else None,
            rationale=rationale,
        )
        return GuardOutcome(
            approved=evaluation.approved,
            gated=evaluation.gated,
            risk_tier=evaluation.risk_tier,
            decision=decision,
            record=record,
        )

    def evaluate_and_log(
        self,
        *,
        action: str,
        text_for_classification: Optional[str] = None,
        inputs: Optional[dict[str, Any]] = None,
        outputs: Optional[str] = None,
        rationale: Optional[list[dict[str, Any]]] = None,
        raise_on_denied: bool = True,
    ) -> GuardOutcome:
        evaluation = self.evaluate(action=action, text_for_classification=text_for_classification, inputs=inputs)
        outcome = self.log(evaluation, action=action, inputs=inputs, outputs=outputs, rationale=rationale)

        if evaluation.gated and not evaluation.approved and raise_on_denied:
            raise ApprovalRequired(
                f"Action '{action}' (category={self.category}, risk_tier={evaluation.risk_tier.value}) "
                f"was denied: {evaluation.denial_reason}"
            )

        return outcome
