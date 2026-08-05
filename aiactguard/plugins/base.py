from __future__ import annotations

from typing import Any, Optional, Protocol, runtime_checkable

from ..core.audit_logger import AuditLogger
from ..core.questionnaire import Questionnaire


@runtime_checkable
class Plugin(Protocol):
    """The contract a community module implements to plug into AIActGuard.

    Matches the shape every built-in report/mapping already has (an
    AuditLogger + an optional questionnaire in, Markdown out), so an
    existing generator can be adapted into a Plugin with a thin wrapper —
    see `examples/plugins/example_gxp_plugin.py`.
    """

    name: str
    description: str

    def generate(
        self,
        logger: AuditLogger,
        *,
        questionnaire: Optional[Questionnaire] = None,
        **kwargs: Any,
    ) -> str: ...
