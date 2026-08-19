from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Union

import yaml

from ..core.risk_classifier import RiskTier

DEFAULT_POLICY_PATH = Path(__file__).parent / "default_policy.yaml"

_TIER_ORDER = {
    RiskTier.MINIMAL: 0,
    RiskTier.LIMITED: 1,
    RiskTier.HIGH: 2,
    RiskTier.UNACCEPTABLE: 3,
}


class ApprovalRequired(RuntimeError):
    """Raised when an action requires human approval but no approver is configured."""


class ActionExposureClass(str, Enum):
    """How consequential an action's effects are if it turns out to have
    been wrong — set once per action at registration time, never inferred
    at runtime. Distinct from risk_tier: a `reversible_read` action can
    still classify as `high` risk (e.g. reading biometric data), and an
    `irreversible_financial` action can classify as `minimal` risk if it's
    outside every configured Annex III category — the two axes answer
    different questions (how sensitive is this category vs. how bad is it
    if this specific action was a mistake)."""

    REVERSIBLE_READ = "reversible_read"
    REVERSIBLE_WRITE = "reversible_write"
    IRREVERSIBLE_FINANCIAL = "irreversible_financial"
    IRREVERSIBLE_DATA = "irreversible_data"
    IRREVERSIBLE_EXTERNAL_COMMS = "irreversible_external_comms"


@dataclass
class GateRule:
    min_risk_tier: RiskTier
    categories: list[str] = field(default_factory=list)  # empty = applies to all categories
    require_reason_on_override: bool = True


@dataclass
class PolicyConfig:
    """Policy-as-code: defines what counts as high-risk for an org and what
    triggers a human-approval gate (Art. 14)."""

    gate_rules: list[GateRule]
    action_exposure_classes: dict[str, ActionExposureClass] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: Optional[Union[str, Path]] = None) -> "PolicyConfig":
        path = Path(path) if path else DEFAULT_POLICY_PATH
        with open(path, "r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}

        rules = [
            GateRule(
                min_risk_tier=RiskTier(rule["min_risk_tier"]),
                categories=rule.get("categories", []),
                require_reason_on_override=rule.get("require_reason_on_override", True),
            )
            for rule in raw.get("gate_rules", [])
        ]
        config = cls(gate_rules=rules)
        for action, exposure_class in (raw.get("actions") or {}).items():
            config.register_action(action, exposure_class)
        return config

    def register_action(self, action: str, exposure_class: str) -> None:
        """Register an action's exposure class. `exposure_class` has no
        default — omitting it is a TypeError, and an unrecognized value
        raises ValueError, by design: there is no safe silent default for
        how consequential an action's effects are."""
        try:
            parsed = ActionExposureClass(exposure_class)
        except ValueError:
            allowed = ", ".join(e.value for e in ActionExposureClass)
            raise ValueError(
                f"Action '{action}' must be registered with a valid exposure_class, "
                f"one of: {allowed}. Got: {exposure_class!r}"
            ) from None
        self.action_exposure_classes[action] = parsed

    def exposure_class_for(self, action: str) -> Optional[ActionExposureClass]:
        """None means the action was never registered — an honest 'not
        declared', not a silently-assumed default."""
        return self.action_exposure_classes.get(action)

    @classmethod
    def default(cls) -> "PolicyConfig":
        return cls.from_yaml()

    def matching_rule(self, *, category: str, risk_tier: RiskTier) -> Optional[GateRule]:
        for rule in self.gate_rules:
            applies_to_category = not rule.categories or category in rule.categories
            meets_threshold = _TIER_ORDER[risk_tier] >= _TIER_ORDER[rule.min_risk_tier]
            if applies_to_category and meets_threshold:
                return rule
        return None

    def requires_approval(self, *, category: str, risk_tier: RiskTier) -> bool:
        return self.matching_rule(category=category, risk_tier=risk_tier) is not None
