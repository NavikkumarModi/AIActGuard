from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Optional, Union

from .base import AuditRecord, AuditStore

_SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_log (
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
    rationale TEXT,
    classifier_confidence REAL,
    action_exposure_class TEXT,
    selected_route TEXT,
    audit_sampled INTEGER,
    outcome_reward_proxy REAL
);
"""

# Columns added after the initial release. Migrated in via ALTER TABLE for
# any pre-existing database that predates them, so old rows survive
# untouched (NULL for these) rather than requiring a backfill.
_MIGRATED_COLUMNS = {
    "classifier_confidence": "REAL",
    "action_exposure_class": "TEXT",
    "selected_route": "TEXT",
    "audit_sampled": "INTEGER",
    "outcome_reward_proxy": "REAL",
}


class SQLiteAuditStore(AuditStore):
    """Append-only SQLite-backed audit trail. Default storage backend —
    swap in a Postgres-backed AuditStore for production multi-writer use."""

    def __init__(self, db_path: Union[str, Path] = "aiactguard_audit.db"):
        self._db_path = str(db_path)
        conn = self._connect()
        try:
            conn.execute(_SCHEMA)
            self._migrate(conn)
            conn.commit()
        finally:
            conn.close()

    def _migrate(self, conn: sqlite3.Connection) -> None:
        existing = {row[1] for row in conn.execute("PRAGMA table_info(audit_log)").fetchall()}
        for name, col_type in _MIGRATED_COLUMNS.items():
            if name not in existing:
                conn.execute(f"ALTER TABLE audit_log ADD COLUMN {name} {col_type}")

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def write(self, record: AuditRecord) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO audit_log
                    (record_id, timestamp, action, category, risk_tier,
                     inputs, outputs, model_version, approved, gated, error,
                     approver_id, override, reason, rationale,
                     classifier_confidence, action_exposure_class, selected_route,
                     audit_sampled, outcome_reward_proxy)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.record_id,
                    record.timestamp,
                    record.action,
                    record.category,
                    record.risk_tier,
                    json.dumps(record.inputs),
                    record.outputs,
                    record.model_version,
                    int(record.approved),
                    int(record.gated),
                    record.error,
                    record.approver_id,
                    int(record.override),
                    record.reason,
                    json.dumps(record.rationale) if record.rationale is not None else None,
                    record.classifier_confidence,
                    record.action_exposure_class,
                    record.selected_route,
                    None if record.audit_sampled is None else int(record.audit_sampled),
                    record.outcome_reward_proxy,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def query(
        self,
        *,
        category: Optional[str] = None,
        risk_tier: Optional[str] = None,
        limit: int = 100,
    ) -> list[AuditRecord]:
        clauses = []
        params: list[Any] = []
        if category:
            clauses.append("category = ?")
            params.append(category)
        if risk_tier:
            clauses.append("risk_tier = ?")
            params.append(risk_tier)

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"""
            SELECT record_id, timestamp, action, category, risk_tier,
                   inputs, outputs, model_version, approved, gated, error,
                   approver_id, override, reason, rationale,
                   classifier_confidence, action_exposure_class, selected_route,
                   audit_sampled, outcome_reward_proxy
            FROM audit_log
            {where}
            ORDER BY timestamp DESC
            LIMIT ?
        """
        params.append(limit)

        conn = self._connect()
        try:
            rows = conn.execute(sql, params).fetchall()
        finally:
            conn.close()

        return [
            AuditRecord(
                record_id=row[0],
                timestamp=row[1],
                action=row[2],
                category=row[3],
                risk_tier=row[4],
                inputs=json.loads(row[5]),
                outputs=row[6],
                model_version=row[7],
                approved=bool(row[8]),
                gated=bool(row[9]),
                error=row[10],
                approver_id=row[11],
                override=bool(row[12]),
                reason=row[13],
                rationale=json.loads(row[14]) if row[14] is not None else None,
                classifier_confidence=row[15],
                action_exposure_class=row[16],
                selected_route=row[17],
                audit_sampled=None if row[18] is None else bool(row[18]),
                outcome_reward_proxy=row[19],
            )
            for row in rows
        ]
