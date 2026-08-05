from __future__ import annotations

from typing import Optional

Questionnaire = dict[str, str]

NEEDS_INPUT = "_[NEEDS INPUT: {label}]_"


def render_field(questionnaire: Optional[Questionnaire], key: str, label: str) -> str:
    """Return the questionnaire's answer for `key`, or a visible placeholder
    if it's missing — reports must show what they couldn't infer instead of
    silently omitting or fabricating it."""
    value = (questionnaire or {}).get(key)
    if value:
        return value
    return NEEDS_INPUT.format(label=label)


def missing_fields(questionnaire: Optional[Questionnaire], required: list[tuple[str, str]]) -> list[str]:
    questionnaire = questionnaire or {}
    return [label for key, label in required if not questionnaire.get(key)]
