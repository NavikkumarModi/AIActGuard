from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class AuditRecord:
    """A single immutable entry in the audit trail (Art. 12)."""

    action: str
    category: str
    risk_tier: str
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: Optional[str] = None
    model_version: Optional[str] = None
    approved: bool = True
    gated: bool = False
    error: Optional[str] = None
    approver_id: Optional[str] = None
    override: bool = False
    reason: Optional[str] = None
    rationale: Optional[list[dict[str, Any]]] = None
    classifier_confidence: Optional[float] = None
    action_exposure_class: Optional[str] = None
    selected_route: Optional[str] = None
    audit_sampled: Optional[bool] = None
    outcome_reward_proxy: Optional[float] = None
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AuditStore(ABC):
    """Pluggable backend for the append-only audit trail. Implement this to
    swap in Postgres, an event stream, etc. instead of the SQLite default."""

    @abstractmethod
    def write(self, record: AuditRecord) -> None: ...

    @abstractmethod
    def query(
        self,
        *,
        category: Optional[str] = None,
        risk_tier: Optional[str] = None,
        limit: int = 100,
    ) -> list[AuditRecord]: ...
