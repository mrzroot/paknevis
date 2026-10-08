"""Dictionary-based spelling rules."""

from __future__ import annotations

import re
from collections.abc import Iterator
from functools import lru_cache
from importlib import resources

import yaml

from .._chars import NOT_WORD_AFTER, NOT_WORD_BEFORE
from ..models import Finding, Severity
from .base import Context, Example, Rule

__all__ = ["Spelling", "Tanvin", "compile_dictionary"]


@lru_cache(maxsize=32)
def compile_dictionary(entries: tuple[tuple[str, str], ...]) -> re.Pattern[str] | None:
    """Compile ``(wrong, right)`` pairs into one whole-word alternation regex."""
    words = sorted({wrong for wrong, _ in entries}, key=len, reverse=True)
    if not words:
        return None
    alternation = "|".join(re.escape(w).replace(r"\ ", r"[ \t]+") for w in words)
    return re.compile(f"{NOT_WORD_BEFORE}(?:{alternation}){NOT_WORD_AFTER}")


class Spelling(Rule):
    code = "PN501"
    name = "spelling"
    category = "spelling"
    severity = Severity.WARNING
    title_en = "Common misspelling"
    title_fa = "غلط املایی رایج"
    description_en = (
        "A small, curated dictionary of unambiguous misspellings (e.g. «اطاق» → «اتاق», "
        "«سپاسگذار» → «سپاسگزار», «نرم افزار» → «نرم‌افزار»). Extend it with your own YAML "
        "files via the `dictionaries` option or inline with `[tool.paknevis.spelling]`."
    )
    description_fa = (
        "فهرستی کوچک و گزیده از غلط‌های املایی بی‌ابهام (مانند «اطاق» ← «اتاق»، «سپاسگذار» ← "
        "«سپاسگزار»، «نرم افزار» ← «نرم‌افزار»). می‌توانید با گزینهٔ `dictionaries` یا جدول "
        "`[tool.paknevis.spelling]` واژه‌های خود را بیفزایید."
    )
    message_en = "Did you mean «{1}»?"
    message_fa = "آیا منظورتان «{1}» است؟"
    examples = (Example("اطاق کار", "اتاق کار"), Example("سپاسگذارم", "سپاسگزارم"))
    options = ("dictionaries", "spelling")

    def find(self, text: str, ctx: Context) -> Iterator[Finding]:
        pattern = compile_dictionary(ctx.spelling)
        if pattern is None:
            return
        lookup = {re.sub(r"\s+", " ", wrong): right for wrong, right in ctx.spelling}
        for match in pattern.finditer(text):
            right = lookup[re.sub(r"\s+", " ", match.group(0))]
            yield Finding(
                match.start(),
                match.end(),
                right,
                self.message_en.format(match.group(0), right),
                self.message_fa.format(match.group(0), right),
            )


@lru_cache(maxsize=1)
def _tanvin_pattern() -> re.Pattern[str]:
    text = resources.files("paknevis").joinpath("data/tanvin.yaml").read_text(encoding="utf-8")
    words = sorted(yaml.safe_load(text), key=len, reverse=True)
    return re.compile(f"{NOT_WORD_BEFORE}(?:{'|'.join(map(re.escape, words))}){NOT_WORD_AFTER}")


class Tanvin(Rule):
    code = "PN502"
    name = "tanvin"
    category = "spelling"
    severity = Severity.INFO
    title_en = "Missing tanvin on adverbs"
    title_fa = "تنوین قید"
    description_en = (
        "Adverbs of Arabic origin such as «مثلاً»، «حتماً» and «لطفاً» are written with tanvin "
        "«ـاً». Only a curated list of unambiguous adverbs is checked."
    )
    description_fa = "قیدهای عربی‌تبار مانند «مثلاً»، «حتماً» و «لطفاً» با تنوین «ـاً» نوشته می‌شوند. فقط فهرستی گزیده و بی‌ابهام بررسی می‌شود."
    message_en = "Write «{1}» with tanvin"
    message_fa = "«{1}» را با تنوین بنویسید"
    examples = (Example("لطفا صبر کنید", "لطفاً صبر کنید"),)

    def find(self, text: str, ctx: Context) -> Iterator[Finding]:
        for match in _tanvin_pattern().finditer(text):
            fixed = match.group(0) + "\u064b"
            yield Finding(
                match.start(),
                match.end(),
                fixed,
                self.message_en.format(match.group(0), fixed),
                self.message_fa.format(match.group(0), fixed),
            )
