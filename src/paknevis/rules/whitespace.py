"""Whitespace rules: repeated spaces, trailing whitespace and kashida."""

from __future__ import annotations

import re
from collections.abc import Iterator

from .._chars import KASHIDA, LETTER_RANGES, contains_persian
from ..models import Finding, Severity
from .base import Context, Example, RegexRule, Rule

__all__ = ["Kashida", "MultipleSpaces", "TrailingWhitespace"]

_TABLE_ROW = re.compile(r"^\s*\|")


class MultipleSpaces(RegexRule):
    code = "PN401"
    name = "multiple-spaces"
    category = "whitespace"
    severity = Severity.WARNING
    title_en = "Multiple spaces"
    title_fa = "فاصله‌های پشت‌سرهم"
    description_en = (
        "Runs of spaces between words on a line with Persian text collapse to one space. "
        "Indentation and Markdown table rows are left alone."
    )
    description_fa = "چند فاصلهٔ پشت‌سرهم میان واژه‌ها (در سطرهای فارسی) به یک فاصله تبدیل می‌شود. تورفتگی آغاز سطر و جدول‌های مارک‌داون دست نمی‌خورند."
    message_en = "Use a single space"
    message_fa = "یک فاصله کافی است"
    examples = (Example("سلام   دنیا", "سلام دنیا"),)
    pattern = re.compile(r"(?<=\S) {2,}(?=\S)")

    def replace(self, match: re.Match[str], text: str, ctx: Context) -> str | None:
        line = ctx.full_line(text, match.start())
        if not contains_persian(line):
            return None
        if ctx.syntax == "markdown" and _TABLE_ROW.match(line):
            return None
        return " "


class TrailingWhitespace(Rule):
    code = "PN402"
    name = "trailing-whitespace"
    category = "whitespace"
    severity = Severity.WARNING
    title_en = "Trailing whitespace"
    title_fa = "فاصلهٔ پایان سطر"
    description_en = (
        "Spaces and tabs at the end of a line are removed. In Markdown, two or more trailing "
        "spaces form a hard line break and are kept."
    )
    description_fa = (
        "فاصله و تب پایان سطر حذف می‌شود. در مارک‌داون دو فاصله یا بیشتر در پایان سطر شکست سطر است و حفظ می‌شود."
    )
    message_en = "Remove trailing whitespace"
    message_fa = "فاصلهٔ پایان سطر را حذف کنید"
    examples = (Example("سلام   \nدنیا", "سلام\nدنیا"),)

    _PATTERN = re.compile(r"[ \t]+(?=\r?\n|\Z)")

    def find(self, text: str, ctx: Context) -> Iterator[Finding]:
        for match in self._PATTERN.finditer(text):
            if match.end() == len(text) and ctx.after:
                continue  # chunk ends before a protected span on the same line
            if match.start() == 0 and ctx.before:
                continue  # whitespace right after a protected span (e.g. inline code)
            if (
                ctx.syntax == "markdown"
                and match.group(0).startswith("  ")
                and "\t" not in match.group(0)
                and match.start() > 0
                and text[match.start() - 1] not in "\r\n"
            ):
                continue  # Markdown hard line break
            yield Finding(match.start(), match.end(), "")


class Kashida(RegexRule):
    code = "PN403"
    name = "kashida"
    category = "whitespace"
    severity = Severity.WARNING
    title_en = "Kashida (tatweel)"
    title_fa = "کشیده (ـ)"
    description_en = (
        "The kashida «ـ» stretches letters for visual justification. It breaks search and should "
        "not be stored in text; let the renderer justify instead."
    )
    description_fa = "کشیدهٔ «ـ» فقط برای زیبایی ظاهری است، جست‌وجو را خراب می‌کند و نباید در متن ذخیره شود."
    message_en = "Remove the kashida «ـ»"
    message_fa = "کشیدهٔ «ـ» را حذف کنید"
    examples = (Example("سـلام", "سلام"),)
    pattern = re.compile(f"(?<=[{LETTER_RANGES}]){KASHIDA}+|{KASHIDA}+(?=[{LETTER_RANGES}])")

    def replace(self, match: re.Match[str], text: str, ctx: Context) -> str:
        return ""
