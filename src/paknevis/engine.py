"""The linting and fixing engine."""

from __future__ import annotations

import bisect
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from functools import lru_cache

from .config import Config
from .dictionary import builtin_dictionary
from .formats import normalize_syntax, prose_chunks, protected_spans
from .models import Diagnostic, Finding, Severity, Span
from .rules import ALL_RULES, Context, Rule, resolve_rule_name

__all__ = ["FixResult", "Linter", "apply_findings"]

MAX_PASSES = 10


@dataclass(frozen=True)
class FixResult:
    """Result of :meth:`Linter.fix_with_report`."""

    text: str
    """The fixed text."""
    diagnostics: tuple[Diagnostic, ...]
    """Diagnostics of the *original* text."""
    remaining: tuple[Diagnostic, ...]
    """Diagnostics still present after fixing (unfixable ones)."""
    changed: bool
    """Whether fixing changed the text."""


def apply_findings(text: str, findings: Iterable[Finding]) -> str:
    """Apply fixable, non-overlapping findings to *text* (first one wins)."""
    pieces: list[str] = []
    cursor = 0
    for finding in sorted(findings, key=lambda f: (f.start, f.end)):
        if finding.replacement is None or finding.start < cursor:
            continue
        pieces.append(text[cursor : finding.start])
        pieces.append(finding.replacement)
        cursor = finding.end
    pieces.append(text[cursor:])
    return "".join(pieces)


class Linter:
    """A configured linter. Cheap to reuse; use :func:`get_linter` to cache."""

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config()
        disabled = {resolve_rule_name(key) for key in self.config.disable}
        enabled = {resolve_rule_name(key) for key in self.config.enable}
        self.rules: tuple[Rule, ...] = tuple(
            rule for rule in ALL_RULES if (rule.default_enabled or rule.name in enabled) and rule.name not in disabled
        )
        spelling = builtin_dictionary()
        spelling.update(self.config.spelling_entries())
        self._spelling = tuple(sorted(spelling.items()))
        self._severity = {
            rule.name: self.config.severity_for(rule.name, rule.code, rule.severity) for rule in ALL_RULES
        }

    # ------------------------------------------------------------------ #
    def _context(self, syntax: str, document: str, start: int, end: int) -> Context:
        line_start = document.rfind("\n", 0, start) + 1
        line_end = document.find("\n", end)
        if line_end == -1:
            line_end = len(document)
        before = document[line_start:start] if line_start < start else ""
        after = document[end:line_end] if end < line_end else ""
        return Context(
            config=self.config,
            syntax=syntax,
            before=before.rstrip("\r"),
            after=after.rstrip("\r"),
            spelling=self._spelling,
        )

    def _chunks(self, text: str, syntax: str) -> list[Span]:
        spans = protected_spans(text, syntax, latex_text_commands=self.config.latex_text_commands)
        return prose_chunks(text, spans)

    def lint(self, text: str, *, syntax: str = "plain", path: str | None = None) -> list[Diagnostic]:
        """Return diagnostics for *text*, sorted by position."""
        syntax = normalize_syntax(syntax)
        line_starts = _line_starts(text)
        diagnostics: list[Diagnostic] = []
        for start, end in self._chunks(text, syntax):
            chunk = text[start:end]
            ctx = self._context(syntax, text, start, end)
            for rule in self.rules:
                for finding in rule.find(chunk, ctx):
                    diagnostics.append(self._diagnostic(rule, finding, text, start, line_starts, path))
        diagnostics.sort(key=lambda d: (d.offset, d.end_offset, d.code))
        return diagnostics

    def fix(self, text: str, *, syntax: str = "plain") -> str:
        """Return *text* with every safe fix applied (idempotent)."""
        syntax = normalize_syntax(syntax)
        for _ in range(MAX_PASSES):
            fixed = self._fix_once(text, syntax)
            if fixed == text:
                return fixed
            text = fixed
        return text

    def fix_with_report(self, text: str, *, syntax: str = "plain", path: str | None = None) -> FixResult:
        """Fix *text* and return diagnostics before and after."""
        before = self.lint(text, syntax=syntax, path=path)
        fixed = self.fix(text, syntax=syntax)
        after = self.lint(fixed, syntax=syntax, path=path) if fixed != text else before
        return FixResult(fixed, tuple(before), tuple(after), fixed != text)

    def _fix_once(self, text: str, syntax: str) -> str:
        pieces: list[str] = []
        cursor = 0
        for start, end in self._chunks(text, syntax):
            pieces.append(text[cursor:start])
            pieces.append(self._fix_chunk(text, start, end, syntax))
            cursor = end
        pieces.append(text[cursor:])
        return "".join(pieces)

    def _fix_chunk(self, document: str, start: int, end: int, syntax: str) -> str:
        chunk = document[start:end]
        ctx = self._context(syntax, document, start, end)
        for _ in range(MAX_PASSES):
            before = chunk
            for rule in self.rules:
                if not rule.fixable:
                    continue
                findings = [f for f in rule.find(chunk, ctx) if f.replacement is not None]
                if findings:
                    chunk = apply_findings(chunk, findings)
            if chunk == before:
                break
        return chunk

    def _diagnostic(
        self,
        rule: Rule,
        finding: Finding,
        text: str,
        base: int,
        line_starts: Sequence[int],
        path: str | None,
    ) -> Diagnostic:
        start, end = base + finding.start, base + finding.end
        original = text[start:end]
        replacement = finding.replacement
        message = finding.message or rule.message_en.format(original, replacement or "")
        message_fa = finding.message_fa or rule.message_fa.format(original, replacement or "")
        line, column = _position(line_starts, start)
        end_line, end_column = _position(line_starts, end)
        return Diagnostic(
            code=rule.code,
            rule=rule.name,
            severity=self._severity[rule.name],
            message=message,
            message_fa=message_fa,
            offset=start,
            end_offset=end,
            line=line,
            column=column,
            end_line=end_line,
            end_column=end_column,
            original=original,
            replacement=replacement,
            path=path,
        )


def _line_starts(text: str) -> list[int]:
    starts = [0]
    index = text.find("\n")
    while index != -1:
        starts.append(index + 1)
        index = text.find("\n", index + 1)
    return starts


def _position(line_starts: Sequence[int], offset: int) -> tuple[int, int]:
    line = bisect.bisect_right(line_starts, offset) - 1
    return line + 1, offset - line_starts[line] + 1


@lru_cache(maxsize=16)
def get_linter(config: Config | None = None) -> Linter:
    """Return a cached :class:`Linter` for *config*."""
    return Linter(config)


def max_severity(diagnostics: Iterable[Diagnostic]) -> Severity | None:
    """Highest severity among *diagnostics*, or ``None`` if empty."""
    best: Severity | None = None
    for diagnostic in diagnostics:
        if best is None or diagnostic.severity.rank > best.rank:
            best = diagnostic.severity
    return best
