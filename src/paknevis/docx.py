"""Optional Microsoft Word (.docx) support via ``python-docx``.

Install with ``pip install "paknevis[docx]"``. Text is processed paragraph by
paragraph (body, tables, headers and footers). Fixes are mapped back onto the
original *runs*, so bold/italic formatting is preserved wherever an edit does
not cross a run boundary.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path
from typing import Any

from .engine import Linter
from .models import Diagnostic

__all__ = ["DocxUnavailableError", "fix_docx", "lint_docx"]


class DocxUnavailableError(RuntimeError):
    """Raised when python-docx is not installed."""


def _load(path: Path) -> Any:
    try:
        import docx
    except ImportError:  # pragma: no cover - depends on environment
        raise DocxUnavailableError('.docx support needs python-docx: pip install "paknevis[docx]"') from None
    return docx.Document(str(path))


def _paragraphs(document: Any) -> Iterator[Any]:
    def from_container(container: Any) -> Iterator[Any]:
        yield from container.paragraphs
        for table in getattr(container, "tables", []):
            for row in table.rows:
                for cell in row.cells:
                    yield from from_container(cell)

    yield from from_container(document)
    for section in document.sections:
        for part in (section.header, section.footer):
            if part is not None and not part.is_linked_to_previous:
                yield from from_container(part)


def lint_docx(path: Path, linter: Linter) -> list[Diagnostic]:
    """Lint a .docx file. ``line`` is the 1-based paragraph number."""
    document = _load(path)
    diagnostics: list[Diagnostic] = []
    for number, paragraph in enumerate(_paragraphs(document), start=1):
        text = paragraph.text
        if not text.strip():
            continue
        for diagnostic in linter.lint(text, syntax="plain", path=str(path)):
            diagnostics.append(replace(diagnostic, line=number, end_line=number))
    return diagnostics


def fix_docx(path: Path, linter: Linter, output: Path | None = None) -> int:
    """Fix a .docx file in place (or write to *output*). Returns paragraphs changed."""
    document = _load(path)
    changed = 0
    for paragraph in _paragraphs(document):
        runs = list(paragraph.runs)
        if not "".join(run.text for run in runs).strip():
            continue
        if fix_runs(runs, linter):
            changed += 1
    if changed:
        document.save(str(output or path))
    return changed


def fix_runs(runs: list[Any], linter: Linter, max_passes: int = 20) -> bool:
    """Apply fixes to a paragraph's *runs* in place; return whether anything changed.

    Each fix is a small edit (usually a character or two), so applying them
    run-by-run keeps formatting intact. Edits spanning runs are written to the
    first run involved.
    """
    changed = False
    for _ in range(max_passes):
        text = "".join(run.text for run in runs)
        fixes = [d for d in linter.lint(text, syntax="plain") if d.fixable]
        if not fixes:
            break
        cursor = len(text) + 1
        for diagnostic in sorted(fixes, key=lambda d: (d.offset, d.end_offset), reverse=True):
            if diagnostic.end_offset > cursor:
                continue  # overlaps an edit already applied in this pass
            _replace_range(runs, diagnostic.offset, diagnostic.end_offset, diagnostic.replacement or "")
            cursor = diagnostic.offset
        changed = True
    return changed


def _replace_range(runs: list[Any], start: int, end: int, replacement: str) -> None:
    """Replace ``[start, end)`` of the concatenated run texts with *replacement*."""
    position = 0
    first = True
    for run in runs:
        text = run.text
        run_start, run_end = position, position + len(text)
        position = run_end
        if run_end < start or (run_end == start and end > start) or run_start > end:
            continue
        if run_start == end and not first:
            break
        local_start = max(start - run_start, 0)
        local_end = min(end - run_start, len(text))
        if first:
            run.text = text[:local_start] + replacement + text[local_end:]
            first = False
        else:
            run.text = text[local_end:]
        if run_end >= end:
            break
