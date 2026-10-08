"""Character normalisation rules: Arabic letters and digits → Persian."""

from __future__ import annotations

import re
from collections.abc import Iterator

from .._chars import (
    ARABIC_DIGITS,
    LATIN_DIGITS,
    PERSIAN_DIGITS,
    is_latin_letter,
    is_persian_letter,
    to_latin_digits,
    to_persian_digits,
)
from ..models import Finding, Severity
from .base import Context, Example, RegexRule, Rule

__all__ = ["ArabicDigits", "ArabicHeh", "ArabicKaf", "ArabicYeh", "DigitStyle", "TehMarbuta"]


class ArabicYeh(RegexRule):
    code = "PN101"
    name = "arabic-yeh"
    category = "characters"
    severity = Severity.ERROR
    title_en = "Arabic Yeh instead of Persian Yeh"
    title_fa = "«ي» عربی به‌جای «ی» فارسی"
    description_en = (
        "Arabic Yeh (U+064A) and Alef Maksura (U+0649) look similar to Persian Yeh (U+06CC) "
        "but are different characters. Mixing them breaks search, sorting and spell-checking."
    )
    description_fa = (
        "«ي» عربی (U+064A) و «ى» (الف مقصوره) شبیه «ی» فارسی (U+06CC) هستند اما نویسهٔ "
        "دیگری‌اند و جست‌وجو، مرتب‌سازی و غلط‌یابی را خراب می‌کنند."
    )
    message_en = "Use Persian Yeh «ی» instead of Arabic «{0}»"
    message_fa = "به‌جای «{0}» عربی از «ی» فارسی استفاده کنید"
    examples = (Example("علي", "علی"), Example("مصطفى", "مصطفی"))
    pattern = re.compile("[\u064a\u0649]")

    def replace(self, match: re.Match[str], text: str, ctx: Context) -> Finding:
        return _char_finding(self, match, "\u06cc")


class ArabicKaf(RegexRule):
    code = "PN102"
    name = "arabic-kaf"
    category = "characters"
    severity = Severity.ERROR
    title_en = "Arabic Kaf instead of Persian Keheh"
    title_fa = "«ك» عربی به‌جای «ک» فارسی"
    description_en = "Arabic Kaf (U+0643) should be written as Persian Keheh «ک» (U+06A9)."
    description_fa = "«ك» عربی (U+0643) باید به صورت «ک» فارسی (U+06A9) نوشته شود."
    message_en = "Use Persian Kaf «ک» instead of Arabic «{0}»"
    message_fa = "به‌جای «{0}» عربی از «ک» فارسی استفاده کنید"
    examples = (Example("كتاب", "کتاب"),)
    pattern = re.compile("\u0643")

    def replace(self, match: re.Match[str], text: str, ctx: Context) -> Finding:
        return _char_finding(self, match, "\u06a9")


class ArabicHeh(RegexRule):
    code = "PN103"
    name = "non-persian-heh"
    category = "characters"
    severity = Severity.ERROR
    title_en = "Non-Persian Heh variant"
    title_fa = "گونهٔ غیرفارسی «ه»"
    description_en = (
        "Heh Doachashmee «ھ» (U+06BE), Heh Goal «ہ» (U+06C1) and Ae «ە» (U+06D5) come from "
        "Urdu/Kurdish keyboards. Persian uses «ه» (U+0647)."
    )
    description_fa = (
        "«ھ» (U+06BE)، «ہ» (U+06C1) و «ە» (U+06D5) از صفحه‌کلیدهای اردو و کردی می‌آیند؛ "
        "در فارسی «ه» (U+0647) به کار می‌رود."
    )
    message_en = "Use Persian Heh «ه» instead of «{0}»"
    message_fa = "به‌جای «{0}» از «ه» فارسی استفاده کنید"
    examples = (Example("ھمه", "همه"),)
    pattern = re.compile("[\u06be\u06c1\u06d5]")

    def replace(self, match: re.Match[str], text: str, ctx: Context) -> Finding:
        return _char_finding(self, match, "\u0647")


class TehMarbuta(RegexRule):
    code = "PN104"
    name = "arabic-teh-marbuta"
    category = "characters"
    severity = Severity.INFO
    title_en = "Arabic Teh Marbuta"
    title_fa = "«ة» (تای گرد) عربی"
    description_en = (
        "Teh Marbuta «ة» is not part of the Persian alphabet; Persian writes it as «ه» or «ت» "
        "depending on the word (e.g. رحمة → رحمت, دائرة‌المعارف → دایرةالمعارف). Because the "
        "right letter depends on the word, the default mode only reports it. Set "
        '`teh-marbuta = "heh"` or `"teh"` to fix automatically.'
    )
    description_fa = (
        "«ة» جزو الفبای فارسی نیست و بسته به واژه به «ه» یا «ت» تبدیل می‌شود (مانند رحمة ← رحمت). "
        "چون انتخاب درست به واژه بستگی دارد، حالت پیش‌فرض فقط هشدار می‌دهد. با "
        '`teh-marbuta = "heh"` یا `"teh"` اصلاح خودکار فعال می‌شود.'
    )
    message_en = "Teh Marbuta «ة» is not a Persian letter; use «ه» or «ت»"
    message_fa = "«ة» حرف فارسی نیست؛ از «ه» یا «ت» استفاده کنید"
    examples = (Example("رحمة", "رحمه"),)
    options = ("teh-marbuta",)
    pattern = re.compile("\u0629")

    def replace(self, match: re.Match[str], text: str, ctx: Context) -> Finding:
        mode = ctx.config.teh_marbuta
        replacement = {"heh": "\u0647", "teh": "\u062a"}.get(mode)
        return Finding(match.start(), match.end(), replacement)


class ArabicDigits(RegexRule):
    code = "PN105"
    name = "arabic-digits"
    category = "characters"
    severity = Severity.ERROR
    title_en = "Arabic-Indic digits"
    title_fa = "رقم‌های عربی"
    description_en = (
        "Arabic-Indic digits (٤ ٥ ٦) differ from Extended Arabic-Indic (Persian) digits "
        "(۴ ۵ ۶). They are converted to the configured digit style (Persian by default)."
    )
    description_fa = (
        "رقم‌های عربی (٤ ٥ ٦) با رقم‌های فارسی (۴ ۵ ۶) فرق دارند و به سبک رقم تنظیم‌شده (پیش‌فرض فارسی) تبدیل می‌شوند."
    )
    message_en = "Arabic-Indic digits «{0}»; use «{1}»"
    message_fa = "رقم عربی «{0}»؛ از «{1}» استفاده کنید"
    examples = (Example("سال ١٤٠٣", "سال ۱۴۰۳"),)
    options = ("digits",)
    pattern = re.compile(f"[{ARABIC_DIGITS}]+")

    def replace(self, match: re.Match[str], text: str, ctx: Context) -> Finding:
        digits = match.group(0)
        fixed = to_latin_digits(digits) if ctx.config.digits == "latin" else to_persian_digits(digits)
        return Finding(
            match.start(),
            match.end(),
            fixed,
            self.message_en.format(digits, fixed),
            self.message_fa.format(digits, fixed),
        )


_NUMBER_RE = re.compile(
    f"[{LATIN_DIGITS}{PERSIAN_DIGITS}](?:[{LATIN_DIGITS}{PERSIAN_DIGITS}.,/:٫٬-]*[{LATIN_DIGITS}{PERSIAN_DIGITS}])?%?٪?"
)


class DigitStyle(Rule):
    """Normalise digits to the configured style in Persian context."""

    code = "PN106"
    name = "digit-style"
    category = "characters"
    severity = Severity.WARNING
    title_en = "Digit style"
    title_fa = "سبک رقم‌ها"
    description_en = (
        'With `digits = "persian"` (default), Latin digits inside Persian prose become Persian '
        "digits — but numbers touching Latin words (e.g. `Python 3.12`, `mp3`, `10 GB`) are left "
        'alone. With `digits = "latin"`, Persian digits become Latin digits. `digits = "keep"` '
        "disables the rule. Code, URLs and Markdown list markers are never changed."
    )
    description_fa = (
        'با `digits = "persian"` (پیش‌فرض) رقم‌های لاتین در متن فارسی به رقم فارسی تبدیل '
        "می‌شوند؛ اما عددهایی که کنار واژهٔ لاتین آمده‌اند (مانند `Python 3.12` یا `10 GB`) دست "
        'نمی‌خورند. با `digits = "latin"` رقم‌های فارسی لاتین می‌شوند و `keep` قاعده را خاموش '
        "می‌کند. کد، نشانی‌ها و شمارهٔ فهرست‌های مارک‌داون هرگز تغییر نمی‌کنند."
    )
    message_en = "Use {0} digits: «{1}» → «{2}»"
    message_fa = "از رقم {0} استفاده کنید: «{1}» ← «{2}»"
    examples = (Example("سال 2024 و 50% رشد", "سال ۲۰۲۴ و ۵۰٪ رشد"),)
    options = ("digits",)

    def find(self, text: str, ctx: Context) -> Iterator[Finding]:
        style = ctx.config.digits
        if style == "keep":
            return
        for match in _NUMBER_RE.finditer(text):
            number = match.group(0)
            if style == "latin":
                fixed = to_latin_digits(number).replace("٪", "%")
                label_en, label_fa = "Latin", "لاتین"
            else:
                if not any(c in LATIN_DIGITS + "%" for c in number) or not _persian_neighbourhood(
                    text, match.start(), match.end()
                ):
                    continue
                fixed = to_persian_digits(number).replace("%", "٪")
                label_en, label_fa = "Persian", "فارسی"
            if fixed != number:
                yield Finding(
                    match.start(),
                    match.end(),
                    fixed,
                    self.message_en.format(label_en, number, fixed),
                    self.message_fa.format(label_fa, number, fixed),
                )


def _persian_neighbourhood(text: str, start: int, end: int) -> bool:
    """True if the nearest letters around a number are Persian (none Latin)."""
    left = _nearest_letter(text, start - 1, -1)
    right = _nearest_letter(text, end, 1)
    if is_latin_letter(left) or is_latin_letter(right):
        return False
    return is_persian_letter(left) or is_persian_letter(right)


def _nearest_letter(text: str, index: int, step: int) -> str:
    while 0 <= index < len(text):
        char = text[index]
        if char in "\r\n":
            return ""
        if char.isalpha():
            return char
        index += step
    return ""


def _char_finding(rule: Rule, match: re.Match[str], replacement: str) -> Finding:
    char = match.group(0)
    return Finding(
        match.start(),
        match.end(),
        replacement,
        rule.message_en.format(char),
        rule.message_fa.format(char),
    )
