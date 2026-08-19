from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Union

import yaml

DEFAULT_TAXONOMY_PATH = Path(__file__).parent / "default_taxonomy.yaml"

ANNEX_III_CATEGORIES = (
    "biometrics",
    "critical_infrastructure",
    "education",
    "employment",
    "essential_services",
    "law_enforcement",
    "migration",
    "justice_democracy",
)


class RiskTier(str, Enum):
    MINIMAL = "minimal"
    LIMITED = "limited"
    HIGH = "high"
    UNACCEPTABLE = "unacceptable"


@dataclass
class TaxonomyEntry:
    category: str
    risk_tier: RiskTier
    keywords: list[str] = field(default_factory=list)


class RiskClassifier:
    """Classifies an agent action/tool call against an EU AI Act Annex III
    risk taxonomy. The taxonomy is YAML-driven so orgs can extend or
    override it without touching code — this is tooling to support a risk
    assessment, not the assessment itself.
    """

    def __init__(self, entries: list[TaxonomyEntry], default_tier: RiskTier = RiskTier.MINIMAL):
        self._entries = entries
        self._default_tier = default_tier

    @classmethod
    def from_yaml(cls, path: Optional[Union[str, Path]] = None) -> "RiskClassifier":
        path = Path(path) if path else DEFAULT_TAXONOMY_PATH
        with open(path, "r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}

        entries = [
            TaxonomyEntry(
                category=item["category"],
                risk_tier=RiskTier(item["risk_tier"]),
                keywords=item.get("keywords", []),
            )
            for item in raw.get("categories", [])
        ]
        default_tier = RiskTier(raw.get("default_tier", "minimal"))
        return cls(entries, default_tier=default_tier)

    @classmethod
    def default(cls) -> "RiskClassifier":
        return cls.from_yaml()

    def classify(self, category: str, text: Optional[str] = None) -> RiskTier:
        """Classify by explicit Annex III category, falling back to keyword
        matching in `text` when the category isn't in the taxonomy."""
        _, tier = self.classify_with_confidence(category, text)
        return tier

    def classify_with_confidence(self, category: str, text: Optional[str] = None) -> tuple[float, RiskTier]:
        """Same classification as `classify()`, plus a confidence score for
        which rule fired. This is rule-match strength, NOT a calibrated
        probability that the action is actually risky — this classifier is
        pure keyword/category matching with no trained model behind it, and
        the score should never be presented as one:

        - Explicit category match: 1.0 — a deterministic, declared rule,
          not a guess.
        - Keyword substring match: 0.6, +0.05 per additional distinct
          keyword matched, capped at 0.85 — weaker evidence than an
          explicit declaration (a substring can false-positive), so it's
          bounded below that ceiling regardless of how many keywords hit.
        - No rule fired at all (fell through to the default tier): 0.0 —
          the classifier found no evidence either way. This is the
          important case to keep honest: a confident-looking default here
          would hide exactly the blind spot worth flagging for review.
        """
        for entry in self._entries:
            if entry.category == category:
                return 1.0, entry.risk_tier

        if text:
            lowered = text.lower()
            for entry in self._entries:
                matched = [kw for kw in entry.keywords if kw.lower() in lowered]
                if matched:
                    confidence = min(0.85, 0.6 + 0.05 * (len(matched) - 1))
                    return confidence, entry.risk_tier

        return 0.0, self._default_tier

    def categories(self) -> list[str]:
        return [entry.category for entry in self._entries]
