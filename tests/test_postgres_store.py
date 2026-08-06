"""Live tests against a real Postgres database — set AIACTGUARD_TEST_POSTGRES_DSN
to point at one (defaults to "postgresql:///aiactguard_test", a local
throwaway database, never one of your actual project databases). Skips
cleanly if no Postgres is reachable, rather than failing the whole suite
in environments (like most CI runners without a Postgres service) that
don't have one.
"""

import os

import pytest

psycopg = pytest.importorskip("psycopg")

from aiactguard.core.risk_classifier import RiskTier  # noqa: E402
from aiactguard.storage.postgres_store import PostgresAuditStore  # noqa: E402

_DSN = os.environ.get("AIACTGUARD_TEST_POSTGRES_DSN", "postgresql:///aiactguard_test")


@pytest.fixture
def store():
    try:
        conn = psycopg.connect(_DSN)
    except psycopg.OperationalError:
        pytest.skip(f"No Postgres reachable at {_DSN!r} — set AIACTGUARD_TEST_POSTGRES_DSN or skip this file.")
    conn.execute("DROP TABLE IF EXISTS audit_log")
    conn.commit()
    conn.close()

    yield PostgresAuditStore(_DSN)

    conn = psycopg.connect(_DSN)
    conn.execute("DROP TABLE IF EXISTS audit_log")
    conn.commit()
    conn.close()


def _record(**overrides):
    from aiactguard.storage.base import AuditRecord

    defaults = dict(action="check_loan_eligibility", category="essential_services", risk_tier=RiskTier.HIGH.value)
    defaults.update(overrides)
    return AuditRecord(**defaults)


def test_write_and_query_round_trip(store):
    store.write(_record(inputs={"applicant_id": "A123"}, outputs="eligible"))

    records = store.query(category="essential_services")
    assert len(records) == 1
    assert records[0].action == "check_loan_eligibility"
    assert records[0].inputs == {"applicant_id": "A123"}
    assert records[0].outputs == "eligible"


def test_query_filters_by_category_and_risk_tier(store):
    store.write(_record(category="essential_services", risk_tier=RiskTier.HIGH.value))
    store.write(_record(category="general_assistance", risk_tier=RiskTier.MINIMAL.value))

    assert len(store.query(category="essential_services")) == 1
    assert len(store.query(risk_tier=RiskTier.MINIMAL.value)) == 1


def test_override_and_rationale_fields_round_trip(store):
    store.write(
        _record(
            approver_id="compliance_officer",
            override=True,
            reason="Manually verified applicant identity via phone call.",
            rationale=[{"source": "agent_scratchpad", "text": "Applicant matched KYC record."}],
        )
    )

    record = store.query(category="essential_services")[0]
    assert record.approver_id == "compliance_officer"
    assert record.override is True
    assert record.reason == "Manually verified applicant identity via phone call."
    assert record.rationale == [{"source": "agent_scratchpad", "text": "Applicant matched KYC record."}]


def test_append_only_across_store_instances(store):
    from aiactguard.storage.postgres_store import PostgresAuditStore as _Store

    _Store(_DSN).write(_record(action="a"))
    _Store(_DSN).write(_record(action="b"))

    records = _Store(_DSN).query(category="essential_services")
    assert len(records) == 2
