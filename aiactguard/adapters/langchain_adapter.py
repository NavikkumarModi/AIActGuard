from __future__ import annotations

from typing import Any, Callable, Optional

try:
    from langchain_core.callbacks.base import BaseCallbackHandler
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "The LangChain adapter requires the 'langchain' extra: "
        "pip install aiactguard[langchain]"
    ) from exc

from ..core.audit_logger import AuditLogger
from ..core.risk_classifier import RiskClassifier
from ..policy.schema import ApprovalRequired, PolicyConfig


class AIActGuardCallbackHandler(BaseCallbackHandler):
    """LangChain callback that routes every tool call through AIActGuard's
    risk classifier, audit logger, and policy-as-code approval gates —
    no changes to the underlying agent or its tools required.

    Usage:
        guard = AIActGuardCallbackHandler(category="essential_services")
        agent_executor.invoke({"input": "..."}, config={"callbacks": [guard]})
    """

    def __init__(
        self,
        *,
        category: str = "general_assistance",
        classifier: Optional[RiskClassifier] = None,
        logger: Optional[AuditLogger] = None,
        policy: Optional[PolicyConfig] = None,
        approver: Optional[Callable[[dict], bool]] = None,
        model_version: Optional[str] = None,
    ):
        self.category = category
        self.classifier = classifier or RiskClassifier.default()
        self.logger = logger or AuditLogger.default()
        self.policy = policy or PolicyConfig.default()
        self.approver = approver
        self.model_version = model_version

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        **kwargs: Any,
    ) -> None:
        tool_name = serialized.get("name", "unknown_tool")
        risk_tier = self.classifier.classify(self.category, text=f"{tool_name} {input_str}")
        requires_approval = self.policy.requires_approval(category=self.category, risk_tier=risk_tier)

        approved = True
        if requires_approval:
            if self.approver is None:
                self.logger.log(
                    action=tool_name,
                    category=self.category,
                    risk_tier=risk_tier,
                    inputs={"input_str": input_str},
                    model_version=self.model_version,
                    approved=False,
                    gated=True,
                    error="No approver configured for a gated action.",
                )
                raise ApprovalRequired(
                    f"Tool '{tool_name}' (risk_tier={risk_tier.value}) requires human approval "
                    "but no approver was configured on AIActGuardCallbackHandler."
                )
            approved = self.approver(
                {"tool": tool_name, "input": input_str, "risk_tier": risk_tier.value}
            )

        self.logger.log(
            action=tool_name,
            category=self.category,
            risk_tier=risk_tier,
            inputs={"input_str": input_str},
            model_version=self.model_version,
            approved=approved,
            gated=requires_approval,
        )

        if not approved:
            raise ApprovalRequired(f"Tool '{tool_name}' was not approved by the configured approver.")

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        # Phase 1 logs the gate decision on tool start; correlating the
        # tool's output back to that record is part of explainability
        # capture, landing later in Phase 1.
        pass
