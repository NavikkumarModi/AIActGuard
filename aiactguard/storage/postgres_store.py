from __future__ import annotations

import json
from typing import Any, Optional

try:
    import psycopg
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "PostgresAuditStore requires the 'postgres' extra: pip install aiactguard[postgres]"
    ) from exc

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
    approved BOOLEAN NOT NULL,
    gated BOOLEAN NOT NULL,
    error TEXT,
    approver_id TEXT,
    override BOOLEAN NOT NULL DEFAULT FALSE,
    reason TEXT,
    rationale TEXT
);
"""


class PostgresAuditStore(AuditStore):
    """Postgres-backed audit trail — the production storage backend the
    original architecture calls for (SQLite's single-writer lock doesn't
    scale to high-volume concurrent agents). Mirrors `SQLiteAuditStore`'s
    schema and behavior exactly so the two backends are interchangeable.

    Opens a new connection per operation, same simplicity level as
    `SQLiteAuditStore` — for high-throughput production use, wrap this
    with a connection pool (e.g. `psycopg_pool`) rather than using it
    as-is under heavy concurrent load.
    """

    def __init__(self, conninfo: str):
        self._conninfo = conninfo
        with psycopg.connect(self._conninfo) as conn:
            conn.execute(_SCHEMA)
            conn.commit()

    def write(self, record: AuditRecord) -> None:
        with psycopg.connect(self._conninfo) as conn:
            conn.execute(
                """
                INSERT INTO audit_log
                    (record_id, timestamp, action, category, risk_tier,
                     inputs, outputs, model_version, approved, gated, error,
                     approver_id, override, reason, rationale)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                    record.approved,
                    record.gated,
                    record.error,
                    record.approver_id,
                    record.override,
                    record.reason,
                    json.dumps(record.rationale) if record.rationale is not None else None,
                ),
            )
            conn.commit()

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
            clauses.append("category = %s")
            params.append(category)
        if risk_tier:
            clauses.append("risk_tier = %s")
            params.append(risk_tier)

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"""
            SELECT record_id, timestamp, action, category, risk_tier,
                   inputs, outputs, model_version, approved, gated, error,
                   approver_id, override, reason, rationale
            FROM audit_log
            {where}
            ORDER BY timestamp DESC
            LIMIT %s
        """
        params.append(limit)

        with psycopg.connect(self._conninfo) as conn:
            rows = conn.execute(sql, params).fetchall()

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
                approved=row[8],
                gated=row[9],
                error=row[10],
                approver_id=row[11],
                override=row[12],
                reason=row[13],
                rationale=json.loads(row[14]) if row[14] is not None else None,
            )
            for row in rows
        ]
