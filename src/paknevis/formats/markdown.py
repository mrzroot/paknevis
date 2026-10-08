"""Markdown protection: front matter, code, links, HTML, math and more."""

from __future__ import annotations

import re

from ..models import Span
from .common import regex_spans, url_and_email_spans
from .html import html_spans

_FRONT_MATTER = re.compile(
    r"\A(?:---|\+\+\+)[ \t]*\r?\n(?:.*?\r?\n)??(?:---|\+\+\+|\.\.\.)[ \t]*(?:\r?\n|\Z)", re.DOTALL
)
_FENCE_OPEN = re.compile(r"^( {0,3})(`{3,}|~{3,})(.*)$")
_LIST_ITEM = re.compile(r"^[ \t]*(?:[-*+]|\d+[.)])(?:[ \t]|$)")
_MATH_BLOCK = re.compile(r"\$\$.+?\$\$", re.DOTALL)
_INLINE_MATH = re.compile(r"(?<![\\$\w])\$(?=[^\s$])[^$\n]*?(?<=[^\s\\])\$(?![\d$])")
_LINK_DEST = re.compile(
    r"\]\((?:<[^>\n]*>|(?:[^()\s]|\([^()\s]*\))*)(?:\s+(?:\"[^\"\n]*\"|'[^'\n]*'|\([^()\n]*\)))?\s*\)"
)
_REF_LABEL = re.compile(r"\]\[[^\]\n]*\]")
_REF_DEF = re.compile(r"^ {0,3}\[[^\]\n]+\]:[ \t]*\S.*$", re.MULTILINE)
_FOOTNOTE = re.compile(r"\[\^[^\]\s]+\]")
_AUTOLINK = re.compile(r"<(?:[A-Za-z][A-Za-z0-9+.-]{1,31}:[^<>\s]*|[^<>\s@]+@[^<>\s]+)>")
_ORDERED_MARKER = re.compile(r"^[ \t>]*\d{1,9}[.)](?=[ \t]|$)", re.MULTILINE)
_ESCAPE = re.compile(r"\\[!-/:-@\[-`{-~]")
_ATTRIBUTES = re.compile(r"\{[#.:][^}\n]*\}")
_EMOJI = re.compile(r"(?<![\w:]):[a-z0-9_+-]+:(?![\w:])")
_TEMPLATE = re.compile(r"\{\{.*?\}\}|\{%.*?%\}", re.DOTALL)
_BACKTICKS = re.compile(r"`+")


def _block_spans(text: str) -> tuple[list[Span], list[Span]]:
    """Front matter, fenced and indented code blocks and ``$$`` blocks.

    Returns ``(protected, code)`` where *code* lists verbatim code regions.
    """
    protected: list[Span] = []
    code: list[Span] = []
    front = _FRONT_MATTER.match(text)
    skip_until = front.end() if front else 0
    if front:
        protected.append((0, front.end()))

    fence: tuple[str, int, int] | None = None  # (char, length, start)
    math_start: int | None = None
    prev_blank = True
    prev_code = False
    in_list = False
    offset = 0
    for line in text.splitlines(keepends=True):
        start, offset = offset, offset + len(line)
        if start < skip_until:
            continue
        content = line.rstrip("\r\n")
        if fence is not None:
            char, length, fence_start = fence
            stripped = content.strip()
            if not content.startswith("    ") and stripped and set(stripped) == {char} and len(stripped) >= length:
                code.append((fence_start, offset))
                fence = None
            continue
        if math_start is not None:
            if "$$" in content:
                protected.append((math_start, offset))
                math_start = None
            continue
        opened = _FENCE_OPEN.match(content)
        if opened and not (opened.group(2)[0] == "`" and "`" in opened.group(3)):
            fence = (opened.group(2)[0], len(opened.group(2)), start)
            prev_blank = prev_code = False
            continue
        if content.strip() == "$$" or (content.lstrip().startswith("$$") and content.count("$$") == 1):
            math_start = start
            continue
        blank = not content.strip()
        if _LIST_ITEM.match(content):
            in_list = True
        elif not blank and not content[:1].isspace():
            in_list = False
        indented = content.startswith(("    ", "\t"))
        if indented and not blank and not in_list and (prev_blank or prev_code):
            code.append((start, start + len(content)))
            prev_code = True
        elif not blank:
            prev_code = False
        prev_blank = blank
    if fence is not None:
        code.append((fence[2], len(text)))
    if math_start is not None:
        protected.append((math_start, len(text)))
    return protected, code


def _code_span_spans(text: str, blocks: list[Span]) -> list[Span]:
    """Inline code spans (matching backtick runs), skipping block regions."""

    def in_block(pos: int) -> bool:
        return any(s <= pos < e for s, e in blocks)

    spans: list[Span] = []
    pos = 0
    while True:
        match = _BACKTICKS.search(text, pos)
        if match is None:
            return spans
        if in_block(match.start()) or (match.start() > 0 and text[match.start() - 1] == "\\"):
            pos = match.end()
            continue
        run = match.group(0)
        closing = re.compile(f"(?<!`){run}(?!`)")
        close = closing.search(text, match.end())
        if close is None or in_block(close.start()):
            spans.append(match.span())
            pos = match.end()
        else:
            spans.append((match.start(), close.end()))
            pos = close.end()


def markdown_spans(text: str) -> tuple[list[Span], list[Span]]:
    """Protected spans for Markdown. Returns ``(protected, code)``."""
    protected, code = _block_spans(text)
    code.extend(_code_span_spans(text, code))
    patterns = (
        _MATH_BLOCK,
        _INLINE_MATH,
        _AUTOLINK,
        _REF_DEF,
        _FOOTNOTE,
        _ORDERED_MARKER,
        _ESCAPE,
        _ATTRIBUTES,
        _EMOJI,
        _TEMPLATE,
    )
    for pattern in patterns:
        protected.extend(regex_spans(pattern, text))
    for match in _LINK_DEST.finditer(text):
        protected.append((match.start() + 1, match.end()))
    for match in _REF_LABEL.finditer(text):
        protected.append((match.start() + 1, match.end()))
    protected.extend(html_spans(text))
    protected.extend(url_and_email_spans(text))
    return protected, code
