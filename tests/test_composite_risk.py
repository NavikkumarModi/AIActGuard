from aiactguard.core.audit_logger import AuditLogger
from aiactguard.core.composite_risk import PipelineStep, analyze_pipeline, pipeline_steps_from_records
from aiactguard.core.risk_classifier import RiskTier
from aiactguard.storage.sqlite_store import SQLiteAuditStore


def test_empty_pipeline_returns_minimal_result():
    result = analyze_pipeline([])
    assert result.composite_tier == RiskTier.MINIMAL
    assert result.escalated is False


def test_single_category_pipeline_is_not_escalated():
    steps = [
        PipelineStep(name="a", category="employment", risk_tier=RiskTier.HIGH),
        PipelineStep(name="b", category="employment", risk_tier=RiskTier.HIGH),
    ]
    result = analyze_pipeline(steps)
    assert result.escalated is False
    assert result.composite_tier == RiskTier.HIGH


def test_multi_category_pipeline_escalates_one_tier():
    steps = [
        PipelineStep(name="a", category="biometrics", risk_tier=RiskTier.HIGH),
        PipelineStep(name="b", category="employment", risk_tier=RiskTier.HIGH),
    ]
    result = analyze_pipeline(steps)
    assert result.escalated is True
    assert result.composite_tier == RiskTier.UNACCEPTABLE
    assert result.max_individual_tier == RiskTier.HIGH


def test_multi_category_pipeline_at_lower_tiers_escalates_from_limited_to_high():
    steps = [
        PipelineStep(name="a", category="general_assistance", risk_tier=RiskTier.LIMITED),
        PipelineStep(name="b", category="employment", risk_tier=RiskTier.MINIMAL),
        PipelineStep(name="c", category="biometrics", risk_tier=RiskTier.MINIMAL),
    ]
    result = analyze_pipeline(steps)
    assert result.max_individual_tier == RiskTier.LIMITED
    assert result.composite_tier == RiskTier.HIGH
    assert result.escalated is True


def test_already_at_top_tier_is_not_further_escalated():
    steps = [
        PipelineStep(name="a", category="law_enforcement", risk_tier=RiskTier.UNACCEPTABLE),
        PipelineStep(name="b", category="migration", risk_tier=RiskTier.MINIMAL),
    ]
    result = analyze_pipeline(steps)
    assert result.composite_tier == RiskTier.UNACCEPTABLE
    assert result.escalated is False


def test_pipeline_steps_from_records_roundtrip(tmp_path):
    logger = AuditLogger(store=SQLiteAuditStore(tmp_path / "audit.db"))
    logger.log(action="a", category="employment", risk_tier=RiskTier.HIGH)
    logger.log(action="b", category="biometrics", risk_tier=RiskTier.HIGH)

    records = logger.query(limit=10)
    steps = pipeline_steps_from_records(records)
    result = analyze_pipeline(steps)

    assert len(steps) == 2
    assert result.escalated is True
