"""Rule base class, context object and small text helpers shared by rules."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import ClassVar

from .._chars import LETTER_RANGES, MARK_RANGES, ZWNJ, is_persian_letter
from ..config import Config
from ..models import Finding, Severity

__all__ = [
    "Context",
    "Example",
    "RegexRule",
    "Rule",
    "line_bounds",
    "next_char",
    "next_nonspace",
    "prev_char",
    "prev_nonspace",
    "word_before",
]

_PERSIAN_CONTEXT_RE = re.compile(f"[{LETTER_RANGES}{MARK_RANGES}{ZWNJ}]")


@dataclass(frozen=True)
class Context:
    """Information available to a rule while it inspects a prose chunk.

    Attributes:
        config: Effective configuration.
        syntax: Document syntax (``plain``, ``markdown``, ``html``, ``latex``).
        before: Document text on the same line *before* the chunk (may
            include protected text such as inline code).
        after: Document text on the same line *after* the chunk.
        spelling: Effective spelling dictionary (built-in + user entries).
    """

    config: Config = field(default_factory=Config)
    syntax: str = "plain"
    before: str = ""
    after: str = ""
    spelling: tuple[tuple[str, str], ...] = ()

    def full_line(self, text: str, index: int) -> str:
        """The complete document line containing chunk position *index*."""
        start, end = line_bounds(text, index)
        line = text[start:end]
        if start == 0:
            line = self.before + line
        if end == len(text):
            line = line + self.after
        return line


@dataclass(frozen=True)
class Example:
    """A before/after example shown in docs, ``paknevis explain`` and tests."""

    before: str
    after: str


class Rule(ABC):
    """Base class for all rules.

    Subclasses set the class attributes and implement :meth:`find`, which
    yields :class:`~paknevis.models.Finding` objects with offsets relative to
    the chunk of prose text it receives. Rules never see protected regions
    such as code, URLs or LaTeX math.
    """

    code: ClassVar[str]
    name: ClassVar[str]
    category: ClassVar[str]
    severity: ClassVar[Severity] = Severity.WARNING
    fixable: ClassVar[bool] = True
    default_enabled: ClassVar[bool] = True
    title_en: ClassVar[str]
    title_fa: ClassVar[str]
    description_en: ClassVar[str]
    description_fa: ClassVar[str]
    message_en: ClassVar[str]
    message_fa: ClassVar[str]
    examples: ClassVar[tuple[Example, ...]] = ()
    options: ClassVar[tuple[str, ...]] = ()

    @abstractmethod
    def find(self, text: str, ctx: Context) -> Iterator[Finding]:
        """Yield findings for *text* (a chunk of prose)."""

    def __repr__(self) -> str:
        return f"<Rule {self.code} {self.name}>"


class RegexRule(Rule):
    """A rule driven by a regular expression.

    Subclasses define :attr:`pattern` and override :meth:`replace`, returning
    the replacement for a match, a full :class:`Finding`, or ``None`` to skip
    the match (e.g. when context makes it a false positive).
    """

    pattern: ClassVar[re.Pattern[str]]

    def find(self, text: str, ctx: Context) -> Iterator[Finding]:
        for match in self.pattern.finditer(text):
            result = self.replace(match, text, ctx)
            if result is None:
                continue
            if isinstance(result, Finding):
                yield result
            elif result != match.group(0):
                yield Finding(match.start(), match.end(), result)

    def replace(self, match: re.Match[str], text: str, ctx: Context) -> str | Finding | None:
        """Return the replacement for *match* (default: no fix, report only)."""
        return Finding(match.start(), match.end(), None)


# ---------------------------------------------------------------------- #
# Helpers
# ---------------------------------------------------------------------- #
def prev_char(text: str, index: int) -> str:
    """Character before *index* or ``""``."""
    return text[index - 1] if index > 0 else ""


def next_char(text: str, index: int) -> str:
    """Character at *index* or ``""``."""
    return text[index] if index < len(text) else ""


def prev_nonspace(text: str, index: int) -> tuple[str, int]:
    """Nearest non-space/tab character before *index* on the same line."""
    i = index - 1
    while i >= 0 and text[i] in " \t":
        i -= 1
    if i < 0 or text[i] in "\r\n":
        return "", -1
    return text[i], i


def next_nonspace(text: str, index: int) -> tuple[str, int]:
    """Nearest non-space/tab character at or after *index* on the same line."""
    i = index
    while i < len(text) and text[i] in " \t":
        i += 1
    if i >= len(text) or text[i] in "\r\n":
        return "", -1
    return text[i], i


def is_persian_context_char(char: str) -> bool:
    """A Persian letter, combining mark or ZWNJ."""
    return bool(char) and _PERSIAN_CONTEXT_RE.fullmatch(char) is not None


def word_before(text: str, index: int) -> str:
    """The Persian word (letters, marks, ZWNJ) ending right before *index*."""
    i = index
    while i > 0 and is_persian_context_char(text[i - 1]):
        i -= 1
    return text[i:index]


def word_after(text: str, index: int) -> str:
    """The Persian word starting at *index*."""
    i = index
    while i < len(text) and is_persian_context_char(text[i]):
        i += 1
    return text[index:i]


def line_bounds(text: str, index: int) -> tuple[int, int]:
    """Return ``(start, end)`` of the line containing *index* (end excludes newline)."""
    start = text.rfind("\n", 0, index) + 1
    end = text.find("\n", index)
    if end == -1:
        end = len(text)
    return start, end


def persian_before(text: str, index: int) -> bool:
    """Whether the nearest non-space char before *index* is a Persian letter."""
    char, _ = prev_nonspace(text, index)
    return is_persian_letter(char) or one_of(char, "\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652")


def one_of(char: str, chars: str) -> bool:
    """``char in chars`` that is ``False`` for the empty string."""
    return bool(char) and char in chars
