"""HTML protection: tags, comments, entities and raw-text elements."""

from __future__ import annotations

import re

from ..models import Span
from .common import regex_spans, url_and_email_spans

RAW_ELEMENTS = "pre|code|script|style|textarea|kbd|samp|var|math|svg|template"

_RAW_BLOCK = re.compile(rf"<({RAW_ELEMENTS})\b[^>]*>.*?</\1\s*>", re.IGNORECASE | re.DOTALL)
_COMMENT = re.compile(r"<!--.*?(?:-->|\Z)", re.DOTALL)
_SPECIAL = re.compile(r"<![^>]*>|<\?.*?\?>", re.DOTALL)
_TAG = re.compile(r"</?[A-Za-z][A-Za-z0-9:-]*(?:\s(?:[^<>\"']|\"[^\"]*\"|'[^']*')*)?/?>")
_ENTITY = re.compile(r"&(?:[A-Za-z][A-Za-z0-9]*|#[0-9]+|#[xX][0-9a-fA-F]+);")
_TEMPLATE = re.compile(r"\{\{.*?\}\}|\{%.*?%\}", re.DOTALL)


def html_spans(text: str) -> list[Span]:
    """Protected spans for HTML (also used for raw HTML inside Markdown)."""
    spans: list[Span] = []
    for pattern in (_COMMENT, _RAW_BLOCK, _SPECIAL, _TAG, _ENTITY, _TEMPLATE):
        spans.extend(regex_spans(pattern, text))
    spans.extend(url_and_email_spans(text))
    return spans
