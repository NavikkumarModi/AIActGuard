import pytest

from aiactguard.policy.schema import ActionExposureClass, PolicyConfig


def test_register_action_with_valid_exposure_class():
    policy = PolicyConfig(gate_rules=[])
    policy.register_action("check_loan_eligibility", "irreversible_financial")

    assert policy.exposure_class_for("check_loan_eligibility") == ActionExposureClass.IRREVERSIBLE_FINANCIAL


def test_register_action_without_exposure_class_raises():
    policy = PolicyConfig(gate_rules=[])

    with pytest.raises(TypeError):
        policy.register_action("check_loan_eligibility")  # type: ignore[call-arg]


def test_register_action_with_invalid_exposure_class_raises_clear_error():
    policy = PolicyConfig(gate_rules=[])

    with pytest.raises(ValueError) as exc_info:
        policy.register_action("check_loan_eligibility", "somewhat_risky")

    message = str(exc_info.value)
    assert "check_loan_eligibility" in message
    assert "somewhat_risky" in message
    assert "irreversible_financial" in message  # lists the allowed values


def test_unregistered_action_returns_none_not_a_default():
    policy = PolicyConfig(gate_rules=[])
    assert policy.exposure_class_for("never_registered") is None


def test_from_yaml_loads_actions_section(tmp_path):
    policy_file = tmp_path / "policy.yaml"
    policy_file.write_text(
        """
gate_rules:
  - min_risk_tier: high
    categories: []

actions:
  check_loan_eligibility: irreversible_financial
  summarize_document: reversible_read
"""
    )

    policy = PolicyConfig.from_yaml(policy_file)

    assert policy.exposure_class_for("check_loan_eligibility") == ActionExposureClass.IRREVERSIBLE_FINANCIAL
    assert policy.exposure_class_for("summarize_document") == ActionExposureClass.REVERSIBLE_READ


def test_from_yaml_with_invalid_actions_entry_raises(tmp_path):
    policy_file = tmp_path / "policy.yaml"
    policy_file.write_text(
        """
gate_rules: []

actions:
  check_loan_eligibility: not_a_real_exposure_class
"""
    )

    with pytest.raises(ValueError):
        PolicyConfig.from_yaml(policy_file)


def test_default_policy_has_no_actions_registered():
    # The shipped default_policy.yaml only documents the actions: section
    # in a comment — nothing should be silently pre-registered.
    policy = PolicyConfig.default()
    assert policy.exposure_class_for("anything") is None
