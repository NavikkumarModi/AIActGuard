from aiactguard.core.approval import ApprovalContext, ApprovalDecision, ApprovalGate
from aiactguard.core.risk_classifier import RiskTier


def _context() -> ApprovalContext:
    return ApprovalContext(action="check_loan_eligibility", category="essential_services", risk_tier=RiskTier.HIGH)


def test_first_approver_that_responds_wins():
    def declines(ctx):
        return None

    def approves(ctx):
        return ApprovalDecision(approved=True, approver_id="compliance_officer")

    gate = ApprovalGate([declines, approves])
    decision = gate.decide(_context())

    assert decision.approved is True
    assert decision.approver_id == "compliance_officer"


def test_earlier_approver_in_chain_takes_precedence():
    def denies(ctx):
        return ApprovalDecision(approved=False, approver_id="team_lead")

    def would_approve(ctx):
        return ApprovalDecision(approved=True, approver_id="compliance_officer")

    gate = ApprovalGate([denies, would_approve])
    decision = gate.decide(_context())

    assert decision.approved is False
    assert decision.approver_id == "team_lead"


def test_empty_chain_denies_by_default():
    gate = ApprovalGate([])
    decision = gate.decide(_context())

    assert decision.approved is False
    assert decision.approver_id == "none"


def test_chain_exhausted_without_response_denies():
    def declines(ctx):
        return None

    gate = ApprovalGate([declines, declines])
    decision = gate.decide(_context())

    assert decision.approved is False
    assert decision.approver_id == "none"
