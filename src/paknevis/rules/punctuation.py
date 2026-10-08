"""Punctuation rules: Persian marks, spacing, quotes, brackets and ellipsis."""

from __future__ import annotations

import re
from collections.abc import Iterator

from .._chars import contains_persian, is_latin_letter, is_persian_letter
from ..models import Finding, Severity
from .base import (
    Context,
    Example,
    RegexRule,
    Rule,
    is_persian_context_char,
    next_char,
    next_nonspace,
    one_of,
    persian_before,
    prev_char,
    prev_nonspace,
    word_before,
)

__all__ = [
    "BracketSpacing",
    "Ellipsis",
    "PersianComma",
    "PersianQuestionMark",
    "PersianQuotes",
    "PersianSemicolon",
    "RepeatedPunctuation",
    "SpaceAfterPunctuation",
    "SpaceBeforePunctuation",
]


class _LatinToPersianMark(Rule):
    """Shared logic for replacing a Latin mark after Persian text."""

    latin: str
    persian: str
    severity = Severity.WARNING
    category = "punctuation"

    def find(self, text: str, ctx: Context) -> Iterator[Finding]:
        index = text.find(self.latin)
        while index != -1:
            if self._applies(text, index):
                yield Finding(index, index + 1, self.persian)
            index = text.find(self.latin, index + 1)

    def _applies(self, text: str, index: int) -> bool:
        before, _ = prev_nonspace(text, index)
        if not (is_persian_context_char(before) or before == "»"):
            return False
        after = next_char(text, index + 1)
        return not (after.isdigit() or is_latin_letter(after) or one_of(after, "=/"))


class PersianComma(_LatinToPersianMark):
    code = "PN301"
    name = "persian-comma"
    latin, persian = ",", "،"
    title_en = "Latin comma in Persian text"
    title_fa = "ویرگول لاتین در متن فارسی"
    description_en = (
        "After a Persian word, use the Persian comma «،» instead of «,». Digit groups like «1,000» are left alone."
    )
    description_fa = "پس از واژهٔ فارسی از ویرگول فارسی «،» به‌جای «,» استفاده کنید. عددهایی مانند «1,000» دست نمی‌خورند."
    message_en = "Use the Persian comma «،»"
    message_fa = "از ویرگول فارسی «،» استفاده کنید"
    examples = (Example("سیب, پرتقال", "سیب، پرتقال"),)


class PersianSemicolon(_LatinToPersianMark):
    code = "PN302"
    name = "persian-semicolon"
    latin, persian = ";", "؛"
    title_en = "Latin semicolon in Persian text"
    title_fa = "نقطه‌ویرگول لاتین در متن فارسی"
    description_en = "After a Persian word, use the Persian semicolon «؛» instead of «;»."
    description_fa = "پس از واژهٔ فارسی از نقطه‌ویرگول فارسی «؛» به‌جای «;» استفاده کنید."
    message_en = "Use the Persian semicolon «؛»"
    message_fa = "از نقطه‌ویرگول فارسی «؛» استفاده کنید"
    examples = (Example("هوا سرد بود; باران آمد", "هوا سرد بود؛ باران آمد"),)


class PersianQuestionMark(_LatinToPersianMark):
    code = "PN303"
    name = "persian-question-mark"
    latin, persian = "?", "؟"
    title_en = "Latin question mark in Persian text"
    title_fa = "علامت سؤال لاتین در متن فارسی"
    description_en = "After a Persian word, use the Persian question mark «؟» instead of «?»."
    description_fa = "پس از واژهٔ فارسی از علامت سؤال فارسی «؟» به‌جای «?» استفاده کنید."
    message_en = "Use the Persian question mark «؟»"
    message_fa = "از علامت سؤال فارسی «؟» استفاده کنید"
    examples = (Example("حالت خوب است?", "حالت خوب است؟"),)


_ALWAYS_TIGHT = "،؛؟"
_PERSIAN_TIGHT = "!:.…"


class SpaceBeforePunctuation(RegexRule):
    code = "PN304"
    name = "space-before-punctuation"
    category = "punctuation"
    severity = Severity.WARNING
    title_en = "Space before punctuation"
    title_fa = "فاصله پیش از نشانه‌ها"
    description_en = (
        "Punctuation sticks to the preceding word: no space before «، ؛ ؟» and, after Persian "
        "text, none before «. : ! …»."
    )
    description_fa = (
        "نشانه‌ها به واژهٔ پیش از خود می‌چسبند: پیش از «، ؛ ؟» و (پس از متن فارسی) پیش از «. : ! …» فاصله نگذارید."
    )
    message_en = "Remove the space before «{0}»"
    message_fa = "فاصلهٔ پیش از «{0}» را بردارید"
    examples = (Example("سلام ، خوبی ؟", "سلام، خوبی؟"),)
    pattern = re.compile(f"(?<=[^\\s])[ \\t]+(?=[{_ALWAYS_TIGHT}{_PERSIAN_TIGHT}])")

    def replace(self, match: re.Match[str], text: str, ctx: Context) -> Finding | None:
        mark = text[match.end()]
        before = prev_char(text, match.start())
        if one_of(before, "«("):
            return None
        if mark in _PERSIAN_TIGHT:
            if not persian_before(text, match.start()):
                return None
            after = next_char(text, match.end() + 1)
            if after.isdigit() or is_latin_letter(after) or one_of(after, "[("):
                return None
        return Finding(match.start(), match.end(), "", self.message_en.format(mark), self.message_fa.format(mark))


class SpaceAfterPunctuation(RegexRule):
    code = "PN305"
    name = "space-after-punctuation"
    category = "punctuation"
    severity = Severity.WARNING
    title_en = "Missing space after punctuation"
    title_fa = "نبود فاصله پس از نشانه‌ها"
    description_en = (
        "Put one space after «، ؛ ؟» and, between Persian words, after «. : ! …». Abbreviations "
        "such as «ه.ش» and numbers such as «۱.۵» are left alone."
    )
    description_fa = "پس از «، ؛ ؟» و (میان واژه‌های فارسی) پس از «. : ! …» یک فاصله بگذارید. کوته‌نوشت‌هایی مانند «ه.ش» و عددها دست نمی‌خورند."
    message_en = "Add a space after «{0}»"
    message_fa = "پس از «{0}» فاصله بگذارید"
    examples = (Example("سلام،خوبی؟بله.", "سلام، خوبی؟ بله."),)
    pattern = re.compile(f"[{_ALWAYS_TIGHT}{_PERSIAN_TIGHT}](?=[^\\s{_ALWAYS_TIGHT}{_PERSIAN_TIGHT}»)\\]])")

    def replace(self, match: re.Match[str], text: str, ctx: Context) -> Finding | None:
        mark = match.group(0)
        after = text[match.end()]
        if mark in _ALWAYS_TIGHT:
            if not (after.isalpha() or after.isdigit() or one_of(after, "«(")):
                return None
            if mark == "،" and after.isdigit() and prev_char(text, match.start()).isdigit():
                return None
        else:
            before = prev_char(text, match.start())
            if not is_persian_letter(before) and not (mark == "…" and one_of(before, "؟!")):
                return None
            if not (is_persian_letter(after) or one_of(after, "«(")):
                return None
            if mark == "." and len(word_before(text, match.start())) == 1:
                return None  # abbreviation such as «ه.ش» or «ق.م»
        return Finding(
            match.start(), match.end(), mark + " ", self.message_en.format(mark), self.message_fa.format(mark)
        )


class BracketSpacing(Rule):
    code = "PN306"
    name = "bracket-spacing"
    category = "punctuation"
    severity = Severity.WARNING
    title_en = "Spacing around parentheses and guillemets"
    title_fa = "فاصله‌گذاری کمانک و گیومه"
    description_en = (
        "No space just inside «…» and (…) around Persian text, and one space between a Persian "
        "word and an opening or closing bracket: «کتاب( خوب )است» → «کتاب (خوب) است»."
    )
    description_fa = (
        "درون «…» و (…) کنار متن فارسی فاصله نگذارید و میان واژهٔ فارسی و کمانک یا گیومه یک "
        "فاصله بگذارید: «کتاب( خوب )است» ← «کتاب (خوب) است»."
    )
    message_en = "Fix spacing around «{0}»"
    message_fa = "فاصله‌گذاری کنار «{0}» را اصلاح کنید"
    examples = (Example("کتاب( خوب )است", "کتاب (خوب) است"), Example("او گفت« سلام »", "او گفت «سلام»"))

    _INNER_OPEN = re.compile(r"([(«])[ \t]+(?=\S)")
    _INNER_CLOSE = re.compile(r"(?<=\S)[ \t]+([)»])")
    _OUTER_OPEN = re.compile(r"(?<=\S)([(«])")
    _OUTER_CLOSE = re.compile(r"([)»])(?=\S)")

    def find(self, text: str, ctx: Context) -> Iterator[Finding]:
        for match in self._INNER_OPEN.finditer(text):
            bracket = match.group(1)
            after, _ = next_nonspace(text, match.end())
            if bracket == "«" or is_persian_letter(after) or one_of(after, "«"):
                yield self._finding(match.start(), match.end(), bracket, bracket)
        for match in self._INNER_CLOSE.finditer(text):
            bracket = match.group(1)
            before = prev_char(text, match.start())
            if bracket == "»" or is_persian_context_char(before) or one_of(before, "؟!.…»"):
                yield self._finding(match.start(), match.end(), bracket, bracket)
        for match in self._OUTER_OPEN.finditer(text):
            if is_persian_context_char(prev_char(text, match.start())):
                bracket = match.group(1)
                yield self._finding(match.start(), match.end(), " " + bracket, bracket)
        for match in self._OUTER_CLOSE.finditer(text):
            if is_persian_letter(next_char(text, match.end())):
                bracket = match.group(1)
                yield self._finding(match.start(), match.end(), bracket + " ", bracket)

    def _finding(self, start: int, end: int, replacement: str, bracket: str) -> Finding:
        return Finding(start, end, replacement, self.message_en.format(bracket), self.message_fa.format(bracket))


class PersianQuotes(RegexRule):
    code = "PN307"
    name = "persian-quotes"
    category = "punctuation"
    severity = Severity.WARNING
    title_en = "Use Persian guillemets «»"
    title_fa = "استفاده از گیومهٔ فارسی «»"
    description_en = (
        'Quoted Persian text uses guillemets «» rather than "…" or “…”. Only balanced pairs on a '
        "single line whose content contains Persian letters are converted."
    )
    description_fa = 'برای نقل‌قول فارسی از گیومهٔ «» به‌جای "…" یا “…” استفاده کنید. فقط جفت‌های کامل در یک سطر که متن فارسی دارند تبدیل می‌شوند.'
    message_en = "Use «» for Persian quotations"
    message_fa = "برای نقل‌قول فارسی از «» استفاده کنید"
    examples = (Example('او گفت "سلام"', "او گفت «سلام»"),)
    pattern = re.compile(r'"([^"\n]+)"|“([^“”\n]+)”|”([^“”\n]+)“')

    def replace(self, match: re.Match[str], text: str, ctx: Context) -> str | None:
        content = next(group for group in match.groups() if group is not None)
        if not contains_persian(content) or not content.strip():
            return None
        return f"«{content.strip()}»"


class Ellipsis(RegexRule):
    code = "PN308"
    name = "ellipsis"
    category = "punctuation"
    severity = Severity.INFO
    title_en = "Ellipsis character"
    title_fa = "نویسهٔ سه‌نقطه"
    description_en = "In Persian text, three dots «...» (or «. . .») become a single ellipsis character «…»."
    description_fa = "در متن فارسی سه نقطهٔ «...» (یا «. . .») به نویسهٔ سه‌نقطه «…» تبدیل می‌شود."
    message_en = "Use the ellipsis character «…»"
    message_fa = "از نویسهٔ سه‌نقطه «…» استفاده کنید"
    examples = (Example("و غیره...", "و غیره…"),)
    pattern = re.compile(r"\.{3,}|\.(?:[ \t]\.){2,}")

    def replace(self, match: re.Match[str], text: str, ctx: Context) -> str | None:
        after, _ = next_nonspace(text, match.end())
        if persian_before(text, match.start()) or (
            not prev_nonspace(text, match.start())[0] and is_persian_letter(after)
        ):
            return "…"
        return None


class RepeatedPunctuation(RegexRule):
    code = "PN309"
    name = "repeated-punctuation"
    category = "punctuation"
    severity = Severity.INFO
    title_en = "Repeated punctuation"
    title_fa = "نشانه‌های تکراری"
    description_en = "Repeating «؟؟؟» or «!!!» is informal; formal Persian uses a single mark."
    description_fa = "تکرار «؟؟؟» یا «!!!» غیررسمی است؛ در نوشتار رسمی یک نشانه کافی است."
    message_en = "Use a single «{0}»"
    message_fa = "یک «{0}» کافی است"
    examples = (Example("واقعاً؟؟؟", "واقعاً؟"),)
    pattern = re.compile(r"([؟!،؛])\1+")

    def replace(self, match: re.Match[str], text: str, ctx: Context) -> Finding | None:
        mark = match.group(1)
        if mark == "!" and not persian_before(text, match.start()):
            return None
        return Finding(match.start(), match.end(), mark, self.message_en.format(mark), self.message_fa.format(mark))
