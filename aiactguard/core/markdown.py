from __future__ import annotations

from typing import Any


class MarkdownReport:
    """Builder for the Markdown reports every generator in this project
    produces. Every report module used to hand-roll its own `lines = [...]`
    list and `"\\n".join(lines)` at the end — this factors that out so each
    module's `generate_*`/`to_markdown` function reads as its actual content
    logic rather than string-formatting boilerplate."""

    def __init__(self, title: str | None = None):
        self._lines: list[str] = [f"# {title}", ""] if title else []

    def note(self, text: str) -> "MarkdownReport":
        """A blockquote callout — used throughout for the honesty
        disclaimers ("drafts, doesn't certify") every generator carries."""
        self._lines.append(f"> {text}")
        self._lines.append("")
        return self

    def heading(self, text: str, level: int = 2) -> "MarkdownReport":
        self._lines.append(f"{'#' * level} {text}")
        self._lines.append("")
        return self

    def field(self, label: str, value: Any) -> "MarkdownReport":
        self._lines.append(f"- **{label}:** {value}")
        return self

    def bullet(self, text: str) -> "MarkdownReport":
        self._lines.append(f"- {text}")
        return self

    def sub_bullet(self, text: str) -> "MarkdownReport":
        self._lines.append(f"  - {text}")
        return self

    def line(self, text: str = "") -> "MarkdownReport":
        self._lines.append(text)
        return self

    def blank(self) -> "MarkdownReport":
        self._lines.append("")
        return self

    def build(self) -> str:
        return "\n".join(self._lines)
