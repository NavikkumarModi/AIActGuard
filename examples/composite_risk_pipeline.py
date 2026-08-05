"""Show composite risk aggregation: three individually limited/high-tier
steps in different Annex III categories composing into an escalated
system-level risk tier.

Requires: pip install aiactguard
"""

from aiactguard.core.composite_risk import PipelineStep, analyze_pipeline
from aiactguard.core.risk_classifier import RiskTier

pipeline = [
    PipelineStep(name="collect_biometric_signal", category="biometrics", risk_tier=RiskTier.HIGH),
    PipelineStep(name="score_employment_fit", category="employment", risk_tier=RiskTier.HIGH),
    PipelineStep(name="summarize_result", category="general_assistance", risk_tier=RiskTier.LIMITED),
]

result = analyze_pipeline(pipeline)
print(result.to_markdown())
