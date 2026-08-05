from __future__ import annotations

from typing import Any, Optional

from ..storage.base import AuditRecord, AuditStore
from ..storage.sqlite_store import SQLiteAuditStore
from .risk_classifier import RiskTier


class AuditLogger:
    """Immutable audit trail for agent actions (Art. 12). Wraps a pluggable
    AuditStore — SQLite by default, swap in Postgres or any other backend
    by implementing AuditStore."""

    def __init__(self, store: Optional[AuditStore] = None):
        self._store = store or SQLiteAuditStore()

    @classmethod
    def default(cls) -> "AuditLogger":
        return cls()

    def log(
        self,
        *,
        action: str,
        category: str,
        risk_tier: RiskTier,
        inputs: Optional[dict[str, Any]] = None,
        outputs: Optional[str] = None,
        model_version: Optional[str] = None,
        approved: bool = True,
        gated: bool = False,
        error: Optional[str] = None,
    ) -> AuditRecord:
        record = AuditRecord(
            action=action,
            category=category,
            risk_tier=risk_tier.value if isinstance(risk_tier, RiskTier) else str(risk_tier),
            inputs=inputs or {},
            outputs=outputs,
            model_version=model_version,
            approved=approved,
            gated=gated,
            error=error,
        )
        self._store.write(record)
        return record

    def query(
        self,
        *,
        category: Optional[str] = None,
        risk_tier: Optional[str] = None,
        limit: int = 100,
    ) -> list[AuditRecord]:
        return self._store.query(category=category, risk_tier=risk_tier, limit=limit)
