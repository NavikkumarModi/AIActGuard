"""Verifies opening a pre-existing database (created before
classifier_confidence/action_exposure_class/selected_route/audit_sampled/
outcome_reward_proxy existed) transparently migrates in the new columns
without disturbing old rows.
"""

import sqlite3

from aiactguard.storage.sqlite_store import SQLiteAuditStore

_OLD_SCHEMA = """
CREATE TABLE audit_log (
    record_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    action TEXT NOT NULL,
    category TEXT NOT NULL,
    risk_tier TEXT NOT NULL,
    inputs TEXT NOT NULL,
    outputs TEXT,
    model_version TEXT,
    approved INTEGER NOT NULL,
    gated INTEGER NOT NULL,
    error TEXT,
    approver_id TEXT,
    override INTEGER NOT NULL DEFAULT 0,
    reason TEXT,
    rationale TEXT
);
"""


def _seed_old_database(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute(_OLD_SCHEMA)
    conn.execute(
        """
        INSERT INTO audit_log
            (record_id, timestamp, action, category, risk_tier, inputs,
             outputs, model_version, approved, gated, error, approver_id,
             override, reason, rationale)
        VALUES ('r1', '2026-01-01T00:00:00', 'legacy_action', 'employment',
                'high', '{}', 'ok', NULL, 1, 0, NULL, NULL, 0, NULL, NULL)
        """
    )
    conn.commit()
    conn.close()


def test_opening_pre_existing_database_adds_new_columns(tmp_path):
    db_path = tmp_path / "audit.db"
    _seed_old_database(db_path)

    store = SQLiteAuditStore(db_path)

    columns = {row[1] for row in sqlite3.connect(db_path).execute("PRAGMA table_info(audit_log)").fetchall()}
    for new_column in (
        "classifier_confidence",
        "action_exposure_class",
        "selected_route",
        "audit_sampled",
        "outcome_reward_proxy",
    ):
        assert new_column in columns


def test_pre_existing_row_reads_back_with_new_fields_as_none(tmp_path):
    db_path = tmp_path / "audit.db"
    _seed_old_database(db_path)

    store = SQLiteAuditStore(db_path)
    records = store.query(category="employment")

    assert len(records) == 1
    record = records[0]
    assert record.action == "legacy_action"
    assert record.outputs == "ok"
    assert record.classifier_confidence is None
    assert record.action_exposure_class is None
    assert record.selected_route is None
    assert record.audit_sampled is None
    assert record.outcome_reward_proxy is None


def test_newly_written_row_round_trips_all_new_fields(tmp_path):
    from aiactguard.storage.base import AuditRecord

    db_path = tmp_path / "audit.db"
    _seed_old_database(db_path)

    store = SQLiteAuditStore(db_path)
    store.write(
        AuditRecord(
            action="new_action",
            category="essential_services",
            risk_tier="high",
            classifier_confidence=0.65,
            action_exposure_class="irreversible_financial",
            selected_route="gpt-4o-mini",
            audit_sampled=True,
            outcome_reward_proxy=0.92,
        )
    )

    records = store.query(category="essential_services")
    assert len(records) == 1
    record = records[0]
    assert record.classifier_confidence == 0.65
    assert record.action_exposure_class == "irreversible_financial"
    assert record.selected_route == "gpt-4o-mini"
    assert record.audit_sampled is True
    assert record.outcome_reward_proxy == 0.92

    # the pre-existing row from the old schema is still there, untouched
    all_records = store.query(limit=10)
    assert len(all_records) == 2


def test_migration_is_idempotent_across_repeated_opens(tmp_path):
    db_path = tmp_path / "audit.db"
    _seed_old_database(db_path)

    SQLiteAuditStore(db_path)
    SQLiteAuditStore(db_path)  # opening again should not error on already-added columns
    store = SQLiteAuditStore(db_path)

    records = store.query(category="employment")
    assert len(records) == 1
