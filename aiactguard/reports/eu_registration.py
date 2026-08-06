from __future__ import annotations

from dataclasses import dataclass, field

from ..core.audit_logger import AuditLogger
from ..core.audit_summary import summarize
from ..core.markdown import MarkdownReport
from ..core.questionnaire import Questionnaire, missing_fields

REQUIRED_FIELDS = (
    ("provider_name", "Provider name"),
    ("system_name", "System name"),
    ("intended_purpose", "Intended purpose"),
    ("contact_email", "Contact email"),
)


@dataclass
class RegistrationData:
    """The metadata fields the Art. 71 EU database registration form
    requires, compiled from the questionnaire + the system's own risk
    classification. Filing stays manual — this only preps the data."""

    provider_name: str
    system_name: str
    intended_purpose: str
    contact_email: str
    risk_categories: list[str] = field(default_factory=list)
    missing_fields: list[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        out = MarkdownReport("EU database registration data (Art. 71 draft)")
        if self.missing_fields:
            out.note(f"**{len(self.missing_fields)} required field(s) missing:** {', '.join(self.missing_fields)}.")
        out.field("Provider name", self.provider_name or "_missing_")
        out.field("System name", self.system_name or "_missing_")
        out.field("Intended purpose", self.intended_purpose or "_missing_")
        out.field("Contact email", self.contact_email or "_missing_")
        out.field("Risk categories touched", ", ".join(self.risk_categories) or "none logged yet")
        out.blank()
        out.note("Data prep only — submit via the actual EU database registration process.")
        return out.build()


def compile_registration_data(logger: AuditLogger, *, questionnaire: Questionnaire) -> RegistrationData:
    records = logger.query(limit=10_000)
    summary = summarize(records)

    gaps = missing_fields(questionnaire, list(REQUIRED_FIELDS))

    return RegistrationData(
        provider_name=questionnaire.get("provider_name", ""),
        system_name=questionnaire.get("system_name", ""),
        intended_purpose=questionnaire.get("intended_purpose", ""),
        contact_email=questionnaire.get("contact_email", ""),
        risk_categories=sorted(summary.by_category),
        missing_fields=gaps,
    )
