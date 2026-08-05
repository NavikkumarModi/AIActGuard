from __future__ import annotations

from dataclasses import dataclass, field
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
        return cls(gate_rules=rules)

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
