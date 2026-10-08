"""Syntax-aware protection of regions that must never be modified.

Each syntax handler returns the spans of the document that are *not* prose
(code, URLs, markup, math …). Rules only ever see the remaining prose chunks.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

from ..models import Span
from .common import directive_spans, gaps, merge_spans
from .html import html_spans
from .latex import latex_spans
from .markdown import markdown_spans
from .plain import plain_spans

__all__ = ["SYNTAXES", "detect_syntax", "normalize_syntax", "prose_chunks", "protected_spans"]

SYNTAXES = ("plain", "markdown", "html", "latex")

_ALIASES = {
    "plain": "plain",
    "text": "plain",
    "txt": "plain",
    "markdown": "markdown",
    "md": "markdown",
    "mdx": "markdown",
    "html": "html",
    "htm": "html",
    "xhtml": "html",
    "latex": "latex",
    "tex": "latex",
}

EXTENSIONS = {
    ".md": "markdown",
    ".markdown": "markdown",
    ".mdown": "markdown",
    ".mkd": "markdown",
    ".mdx": "markdown",
    ".txt": "plain",
    ".text": "plain",
    ".html": "html",
    ".htm": "html",
    ".xhtml": "html",
    ".tex": "latex",
    ".ltx": "latex",
}

_COMMENT_DIRECTIVE = {
    "markdown": re.compile(r"<!--[ \t]*paknevis-"),
    "html": re.compile(r"<!--[ \t]*paknevis-"),
    "latex": re.compile(r"%[ \t]*paknevis-"),
}


def normalize_syntax(syntax: str) -> str:
    """Normalise a syntax name or alias (``md``, ``tex`` …) to a canonical name."""
    try:
        return _ALIASES[syntax.strip().lower().lstrip(".")]
    except KeyError:
        raise ValueError(f"unknown syntax {syntax!r} (expected one of: {', '.join(SYNTAXES)})") from None


def detect_syntax(path: str | Path) -> str:
    """Guess the syntax of a file from its extension (default: ``plain``)."""
    return EXTENSIONS.get(Path(path).suffix.lower(), "plain")


def protected_spans(text: str, syntax: str = "plain", *, latex_text_commands: Iterable[str] = ()) -> list[Span]:
    """Return merged spans of *text* that rules must not touch."""
    syntax = normalize_syntax(syntax)
    code: list[Span] = []
    if syntax == "markdown":
        spans, code = markdown_spans(text)
    elif syntax == "html":
        spans = html_spans(text)
    elif syntax == "latex":
        spans, code = latex_spans(text, latex_text_commands)
    else:
        spans = plain_spans(text)
    code = merge_spans(code)
    spans.extend(code)
    spans.extend(_directives(text, syntax, code))
    return merge_spans(spans)


def _directives(text: str, syntax: str, code: list[Span]) -> list[Span]:
    if "paknevis-" not in text:
        return []
    marker = _COMMENT_DIRECTIVE.get(syntax)
    if marker is not None:
        # Only honour directives written inside a real comment.
        keep = [m.start() for m in marker.finditer(text) if not _inside(m.start(), code)]
        if not keep:
            return []
        masked = list(text)
        for index, char in enumerate(text):
            if char != "\n":
                masked[index] = " "
        for start in keep:
            end = text.find("\n", start)
            end = len(text) if end == -1 else end
            masked[start:end] = text[start:end]
        return directive_spans("".join(masked))
    return [s for s in directive_spans(text) if not _inside(s[0], code)]


def _inside(index: int, spans: list[Span]) -> bool:
    return any(start <= index < end for start, end in spans)


def prose_chunks(text: str, spans: list[Span]) -> list[Span]:
    """Complement of *spans*: the prose regions rules are allowed to edit."""
    return gaps(len(text), spans)
