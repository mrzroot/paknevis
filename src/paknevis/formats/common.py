"""Span utilities and patterns shared by all syntaxes."""

from __future__ import annotations

import re
from collections.abc import Iterable

from ..models import Span

__all__ = ["directive_spans", "gaps", "merge_spans", "regex_spans", "url_and_email_spans"]

_URL_RE = re.compile(r"(?:(?:https?|ftp|file)://|www\.)[^\s<>\"'«»`]+", re.IGNORECASE)
_EMAIL_RE = re.compile(r"(?<![\w.+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
_TRAILING = ".,;:!?،؛؟…'\""

_DIRECTIVE_RE = re.compile(r"paknevis-(disable-next-line|disable-line|disable|enable)\b")


def merge_spans(spans: Iterable[Span]) -> list[Span]:
    """Sort and merge overlapping or touching spans; drop empty ones."""
    merged: list[Span] = []
    for start, end in sorted(s for s in spans if s[1] > s[0]):
        if merged and start <= merged[-1][1]:
            if end > merged[-1][1]:
                merged[-1] = (merged[-1][0], end)
        else:
            merged.append((start, end))
    return merged


def gaps(length: int, spans: list[Span]) -> list[Span]:
    """Return the complement of merged *spans* within ``[0, length)``."""
    result: list[Span] = []
    cursor = 0
    for start, end in spans:
        if start > cursor:
            result.append((cursor, start))
        cursor = max(cursor, end)
    if cursor < length:
        result.append((cursor, length))
    return result


def regex_spans(pattern: re.Pattern[str], text: str, group: int = 0) -> list[Span]:
    """Spans of all matches of *pattern* (or of one of its groups)."""
    return [m.span(group) for m in pattern.finditer(text) if m.group(group) is not None]


def _trim_url(url: str) -> str:
    while url and url[-1] in _TRAILING:
        url = url[:-1]
    while url.endswith(")") and url.count(")") > url.count("("):
        url = url[:-1]
    return url


def url_and_email_spans(text: str) -> list[Span]:
    """Spans of bare URLs and e-mail addresses."""
    spans = [m.span() for m in _EMAIL_RE.finditer(text)]
    for match in _URL_RE.finditer(text):
        url = _trim_url(match.group(0))
        spans.append((match.start(), match.start() + len(url)))
    return spans


def _line_span(text: str, index: int) -> Span:
    start = text.rfind("\n", 0, index) + 1
    end = text.find("\n", index)
    return start, (len(text) if end == -1 else end + 1)


def directive_spans(text: str) -> list[Span]:
    """Regions disabled with inline ``paknevis-disable`` style directives.

    Supported in any comment syntax (or plain text):

    * ``paknevis-disable`` … ``paknevis-enable`` — disable a region
    * ``paknevis-disable-line`` — disable the line containing the directive
    * ``paknevis-disable-next-line`` — disable the following line
    """
    spans: list[Span] = []
    region_start: int | None = None
    for match in _DIRECTIVE_RE.finditer(text):
        kind = match.group(1)
        line_start, line_end = _line_span(text, match.start())
        if kind == "disable":
            if region_start is None:
                region_start = line_start
        elif kind == "enable":
            if region_start is not None:
                spans.append((region_start, line_end))
                region_start = None
            else:
                spans.append((line_start, line_end))
        elif kind == "disable-line":
            spans.append((line_start, line_end))
        else:
            spans.append((line_start, line_end))
            if line_end < len(text):
                spans.append(_line_span(text, line_end))
    if region_start is not None:
        spans.append((region_start, len(text)))
    return spans
