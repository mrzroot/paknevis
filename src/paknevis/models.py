"""Public data types: severities, findings and diagnostics."""

from __future__ import annotations

import enum
from dataclasses import asdict, dataclass, field
from typing import Any

__all__ = ["Diagnostic", "Finding", "Severity", "Span"]

Span = tuple[int, int]
"""A half-open ``(start, end)`` range of character offsets."""


class Severity(str, enum.Enum):
    """How serious a diagnostic is. Ordered: ``info < warning < error``."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

    @property
    def rank(self) -> int:
        """Numeric rank used for comparisons and ``--fail-on`` thresholds."""
        return _RANKS[self]

    @classmethod
    def parse(cls, value: str | Severity) -> Severity:
        """Parse a severity name (case-insensitive), raising ``ValueError``."""
        if isinstance(value, Severity):
            return value
        try:
            return cls(value.strip().lower())
        except ValueError:
            names = ", ".join(s.value for s in cls)
            raise ValueError(f"unknown severity {value!r} (expected one of: {names})") from None


_RANKS = {Severity.INFO: 0, Severity.WARNING: 1, Severity.ERROR: 2}


@dataclass(frozen=True)
class Finding:
    """A raw match produced by a rule, relative to the text the rule received.

    ``replacement`` is ``None`` when the issue cannot be fixed automatically.
    ``message``/``message_fa`` override the rule's default messages.
    """

    start: int
    end: int
    replacement: str | None
    message: str | None = None
    message_fa: str | None = None


@dataclass(frozen=True)
class Diagnostic:
    """A problem found in a document, with absolute positions.

    Lines and columns are 1-based; columns count Unicode code points.
    ``offset``/``end_offset`` are 0-based code-point offsets into the text, so
    ``text[d.offset:d.end_offset] == d.original`` always holds.
    """

    code: str
    rule: str
    severity: Severity
    message: str
    message_fa: str
    offset: int
    end_offset: int
    line: int
    column: int
    end_line: int
    end_column: int
    original: str
    replacement: str | None = None
    path: str | None = field(default=None, compare=False)

    @property
    def fixable(self) -> bool:
        """Whether paknevis can fix this diagnostic automatically."""
        return self.replacement is not None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable dictionary representation."""
        data = asdict(self)
        data["severity"] = self.severity.value
        data["fixable"] = self.fixable
        return data

    def format(self, *, lang: str = "en") -> str:
        """Render as ``path:line:col: CODE [rule] message``."""
        location = f"{self.path or '<text>'}:{self.line}:{self.column}"
        message = self.message_fa if lang == "fa" else self.message
        return f"{location}: {self.code} [{self.rule}] {message}"
