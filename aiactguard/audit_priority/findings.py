from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Union

_SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_findings (
    finding_id TEXT PRIMARY KEY,
    record_id TEXT NOT NULL,
    is_true_violation INTEGER NOT NULL,
    timestamp TEXT NOT NULL
);
"""


@dataclass
class AuditFinding:
    """The ground-truth outcome of a human audit review: was this action,
    on inspection, actually a violation? Distinct from `AuditRecord.approved`
    (the gate's decision at the time, not a post-hoc finding) and from
    `outcome_reward_proxy` (task-success/utility, not a risk label)."""

    record_id: str
    is_true_violation: bool
    finding_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AuditFindingStore:
    """Records ground-truth audit findings, keyed to `AuditRecord.record_id`.
    Point this at the same SQLite file as your `SQLiteAuditStore` — it adds
    its own `audit_findings` table alongside `audit_log`, not a change to
    that table's schema."""

    def __init__(self, db_path: Union[str, Path]):
        self._db_path = str(db_path)
        conn = sqlite3.connect(self._db_path)
        try:
            conn.execute(_SCHEMA)
            conn.commit()
        finally:
            conn.close()

    def record(self, record_id: str, is_true_violation: bool) -> AuditFinding:
        finding = AuditFinding(record_id=record_id, is_true_violation=is_true_violation)
        conn = sqlite3.connect(self._db_path)
        try:
            conn.execute(
                "INSERT INTO audit_findings (finding_id, record_id, is_true_violation, timestamp) VALUES (?, ?, ?, ?)",
                (finding.finding_id, finding.record_id, int(finding.is_true_violation), finding.timestamp),
            )
            conn.commit()
        finally:
            conn.close()
        return finding

    def outcomes_by_record_id(self) -> dict[str, bool]:
        """Every recorded finding, keyed by record_id. If a record_id was
        reviewed more than once, the most recent finding wins."""
        conn = sqlite3.connect(self._db_path)
        try:
            rows = conn.execute(
                "SELECT record_id, is_true_violation FROM audit_findings ORDER BY timestamp ASC"
            ).fetchall()
        finally:
            conn.close()
        return {record_id: bool(is_true_violation) for record_id, is_true_violation in rows}
