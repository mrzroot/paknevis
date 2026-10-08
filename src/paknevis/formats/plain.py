"""Plain-text protection: URLs, e-mails and inline `code`."""

from __future__ import annotations

import re

from ..models import Span
from .common import regex_spans, url_and_email_spans

_INLINE_CODE = re.compile(r"`[^`\n]+`")


def plain_spans(text: str) -> list[Span]:
    """Protected spans for plain text."""
    return url_and_email_spans(text) + regex_spans(_INLINE_CODE, text)
