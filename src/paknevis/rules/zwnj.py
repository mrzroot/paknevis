"""ZWNJ (نیم‌فاصله) rules: prefixes, suffixes and cleanup."""

from __future__ import annotations

import re

from .._chars import LETTER_CLASS, LETTER_RANGES, MARK_RANGES, NOT_WORD_BEFORE, ZWNJ
from ..models import Finding, Severity
from .base import Context, Example, RegexRule, word_after, word_before

__all__ = ["ZwnjCleanup", "ZwnjComparative", "ZwnjHehSuffix", "ZwnjMiPrefix", "ZwnjPlural"]

_WORDCH = f"{LETTER_RANGES}{MARK_RANGES}\u0640"
_END = f"(?![{_WORDCH}{ZWNJ}])"  # end of word: no letter and no ZWNJ follows

# Function words that are never the stem of a ZWNJ-joined form.
_FUNCTION_WORDS = frozenset(
    [
        "و",
        "که",
        "به",
        "از",
        "در",
        "با",
        "را",
        "تا",
        "یا",
        "اگر",
        "هم",
        "نه",
        "چه",
        "پس",
        "بر",
        "برای",
        "این",
        "آن",
        "هر",
        "همه",
        "یک",
        "می",
        "نمی",
    ]
)


class ZwnjCleanup(RegexRule):
    code = "PN201"
    name = "zwnj-cleanup"
    category = "zwnj"
    severity = Severity.WARNING
    title_en = "Misplaced or duplicate ZWNJ"
    title_fa = "نیم‌فاصلهٔ زائد یا تکراری"
    description_en = (
        "A ZWNJ only makes sense between two letters. Repeated ZWNJs are collapsed, and a ZWNJ "
        "next to a space, punctuation, digit or the start/end of a word is removed (other rules "
        "then re-join known prefixes and suffixes correctly)."
    )
    description_fa = (
        "نیم‌فاصله فقط میان دو حرف معنا دارد. نیم‌فاصله‌های پشت‌سرهم یکی می‌شوند و "
        "نیم‌فاصلهٔ کنار فاصله، نشانه، رقم یا آغاز و پایان واژه حذف می‌شود."
    )
    message_en = "Redundant ZWNJ"
    message_fa = "نیم‌فاصلهٔ زائد"
    examples = (Example("کتاب\u200c\u200cها", "کتاب\u200cها"), Example("میز\u200c هست", "میز هست"))
    pattern = re.compile(
        f"(?P<dup>(?<=[{_WORDCH}]){ZWNJ}{{2,}}(?=[{_WORDCH}]))"
        f"|(?<![{_WORDCH}{ZWNJ}]){ZWNJ}+"
        f"|(?<!{ZWNJ}){ZWNJ}+(?![{_WORDCH}{ZWNJ}])"
    )

    def replace(self, match: re.Match[str], text: str, ctx: Context) -> str:
        return ZWNJ if match.group("dup") else ""


# Common present (with personal ending) and past stems for joined «می» forms.
_PRESENT_STEMS = [
    "خواه",
    "رو",
    "کن",
    "شو",
    "گوی",
    "دان",
    "توان",
    "آی",
    "ده",
    "گیر",
    "بین",
    "نویس",
    "خوان",
    "خواب",
    "خور",
    "رس",
    "زن",
    "گذار",
    "گذر",
    "پرس",
    "ساز",
    "آور",
    "بر",
    "دار",
    "کش",
    "یاب",
    "فهم",
    "پذیر",
    "ریز",
    "سوز",
    "نشین",
    "پوش",
    "شناس",
    "فرست",
    "پرداز",
    "گرد",
    "افت",
    "انداز",
    "ایست",
    "باش",
    "مان",
    "میر",
    "بند",
    "شکن",
    "دو",
    "خند",
    "ترس",
    "کوش",
    "آموز",
    "گشا",
    "فروش",
    "خر",
    "پاش",
    "لرز",
    "چرخ",
    "رقص",
]
_PAST_STEMS = [
    "خواست",
    "رفت",
    "کرد",
    "شد",
    "گفت",
    "دانست",
    "توانست",
    "آمد",
    "داد",
    "گرفت",
    "دید",
    "نوشت",
    "خواند",
    "خوابید",
    "خورد",
    "رسید",
    "زد",
    "گذاشت",
    "گذشت",
    "پرسید",
    "ساخت",
    "آورد",
    "برد",
    "داشت",
    "کشید",
    "یافت",
    "فهمید",
    "پذیرفت",
    "ریخت",
    "سوخت",
    "نشست",
    "پوشید",
    "شناخت",
    "فرستاد",
    "پرداخت",
    "گشت",
    "افتاد",
    "انداخت",
    "ایستاد",
    "ماند",
    "مرد",
    "بست",
    "شکست",
    "دوید",
    "خندید",
    "ترسید",
    "کوشید",
    "آموخت",
    "گشود",
    "فروخت",
    "خرید",
    "لرزید",
    "چرخید",
    "رقصید",
    "بایست",
]
_PRESENT_ENDINGS = "ند|ید|یم|م|ی|د"
_PAST_ENDINGS = "ند|ید|یم|م|ی|"
_JOINED_EXCEPTIONS = frozenset({"میدانی"})  # «میدانی» is also an adjective (field-)

_MI_JOINED = (
    f"{NOT_WORD_BEFORE}(ن?می)(?=(?:"
    f"(?:{'|'.join(sorted(_PRESENT_STEMS, key=len, reverse=True))})(?:{_PRESENT_ENDINGS})"
    f"|(?:{'|'.join(sorted(_PAST_STEMS, key=len, reverse=True))})(?:{_PAST_ENDINGS})"
    f"|توان"
    f"){_END})"
)
_MI_SPACED = f"{NOT_WORD_BEFORE}(ن?می)([ \t]+){ZWNJ}?(?={LETTER_CLASS})"


class ZwnjMiPrefix(RegexRule):
    code = "PN202"
    name = "zwnj-mi-prefix"
    category = "zwnj"
    severity = Severity.WARNING
    title_en = "ZWNJ after «می»/«نمی» verb prefix"
    title_fa = "نیم‌فاصله پس از پیشوند «می» و «نمی»"
    description_en = (
        "The continuous prefix «می»/«نمی» is joined to the verb with a ZWNJ: «می روم» and "
        "«میروم» become «می‌روم». Joined forms are only fixed for a curated list of common verb "
        "stems, so nouns such as «میز», «میدان» or «میوه» are never touched."
    )
    description_fa = (
        "پیشوند «می» و «نمی» با نیم‌فاصله به فعل می‌چسبد: «می روم» و «میروم» ← «می‌روم». "
        "شکل چسبیده فقط برای فهرستی از بن‌های رایج فعل اصلاح می‌شود تا واژه‌هایی مانند «میز»، "
        "«میدان» و «میوه» دست نخورند."
    )
    message_en = "Use a ZWNJ after «{0}»: «{0}‌{1}»"
    message_fa = "پس از «{0}» نیم‌فاصله بگذارید: «{0}‌{1}»"
    examples = (Example("می روم", "می‌روم"), Example("نمیدانم", "نمی‌دانم"))
    pattern = re.compile(f"{_MI_SPACED}|{_MI_JOINED}")

    def replace(self, match: re.Match[str], text: str, ctx: Context) -> Finding | None:
        if match.group(1) is not None:  # spaced form
            prefix = match.group(1)
            verb_start = match.end()
            verb = word_after(text, verb_start)
            if verb in _FUNCTION_WORDS or len(verb) < 2:
                return None
            return Finding(
                match.start(),
                match.end(),
                prefix + ZWNJ,
                self.message_en.format(prefix, verb),
                self.message_fa.format(prefix, verb),
            )
        prefix = match.group(3)
        word = word_after(text, match.start())
        if word in _JOINED_EXCEPTIONS:
            return None
        return Finding(
            match.start(),
            match.end(),
            prefix + ZWNJ,
            self.message_en.format(prefix, word[len(prefix) :]),
            self.message_fa.format(prefix, word[len(prefix) :]),
        )


_PLURAL_SUFFIX = "ها(?:ی(?:ی|م|ت|ش|مان|تان|شان)?|یم|یت|یش|یمان|یتان|یشان|ست)?"


class ZwnjPlural(RegexRule):
    code = "PN203"
    name = "zwnj-plural"
    category = "zwnj"
    severity = Severity.WARNING
    title_en = "ZWNJ before plural «ها»"
    title_fa = "نیم‌فاصله پیش از «ها»ی جمع"
    description_en = (
        "The plural suffix «ها» (and «های», «هایی», «هایم»…) is attached with a ZWNJ, not a "
        "space: «کتاب ها» → «کتاب‌ها»."
    )
    description_fa = "پسوند جمع «ها» (و «های»، «هایی»، «هایم»…) با نیم‌فاصله می‌آید: «کتاب ها» ← «کتاب‌ها»."
    message_en = "Attach «{0}» with a ZWNJ instead of a space"
    message_fa = "«{0}» را با نیم‌فاصله بچسبانید، نه فاصله"
    examples = (Example("کتاب ها", "کتاب‌ها"), Example("این روش های جدید", "این روش‌های جدید"))
    pattern = re.compile(f"(?<=[{_WORDCH}])[ \t]+(?={_PLURAL_SUFFIX}{_END})")

    def replace(self, match: re.Match[str], text: str, ctx: Context) -> Finding | None:
        before = word_before(text, match.start())
        if before in _FUNCTION_WORDS and before not in ("این", "آن", "همه"):
            return None
        suffix = word_after(text, match.end())
        return Finding(
            match.start(),
            match.end(),
            ZWNJ,
            self.message_en.format(suffix),
            self.message_fa.format(suffix),
        )


_COMPARATIVE_ADJECTIVES = frozenset(
    [
        "بیش",
        "کم",
        "بزرگ",
        "کوچک",
        "مهم",
        "ساده",
        "سریع",
        "آسان",
        "سخت",
        "دشوار",
        "کند",
        "تند",
        "زیاد",
        "قوی",
        "ضعیف",
        "دقیق",
        "سنگین",
        "سبک",
        "ارزان",
        "گران",
        "جدید",
        "قدیمی",
        "نزدیک",
        "دور",
        "طولانی",
        "کوتاه",
        "بلند",
        "پایین",
        "بالا",
        "پیچیده",
        "مناسب",
        "امن",
        "خطرناک",
        "روشن",
        "تاریک",
        "گرم",
        "سرد",
        "زیبا",
        "مفید",
        "کارآمد",
        "پرکاربرد",
        "رایج",
        "معروف",
    ]
)


class ZwnjComparative(RegexRule):
    code = "PN204"
    name = "zwnj-comparative"
    category = "zwnj"
    severity = Severity.WARNING
    title_en = "ZWNJ before «تر»/«ترین»"
    title_fa = "نیم‌فاصله پیش از «تر» و «ترین»"
    description_en = (
        "Comparative and superlative suffixes are not separate words: «بزرگ ترین» → "
        "«بزرگ‌ترین». Because «تر» alone also means *wet*, «X تر» is only fixed when X is a common "
        "adjective or the phrase continues with «از» (than)."
    )
    description_fa = (
        "«تر» و «ترین» واژهٔ جدا نیستند: «بزرگ ترین» ← «بزرگ‌ترین». چون «تر» به معنای «خیس» هم "
        "هست، «X تر» فقط وقتی اصلاح می‌شود که X صفتی رایج باشد یا پس از آن «از» بیاید."
    )
    message_en = "Attach «{0}» with a ZWNJ"
    message_fa = "«{0}» را با نیم‌فاصله بچسبانید"
    examples = (Example("بزرگ ترین", "بزرگ‌ترین"), Example("سریع تر از", "سریع‌تر از"))
    pattern = re.compile(f"(?<=[{_WORDCH}])[ \t]+(?=(تر(?:ین)?)(?:ها|{ZWNJ}ها)?{_END}([ \t]+از{_END})?)")

    def replace(self, match: re.Match[str], text: str, ctx: Context) -> Finding | None:
        before = word_before(text, match.start())
        if before in _FUNCTION_WORDS or not before:
            return None
        suffix = match.group(1)
        if suffix == "تر" and before not in _COMPARATIVE_ADJECTIVES and match.group(2) is None:
            return None
        return Finding(
            match.start(),
            match.end(),
            ZWNJ,
            self.message_en.format(suffix),
            self.message_fa.format(suffix),
        )


# Words ending in a pronounced «ه» (not the silent "he-ye ghayr-e malfuz").
_PRONOUNCED_HEH = frozenset(
    [
        "به",
        "که",
        "چه",
        "نه",
        "ده",
        "مه",
        "شه",
        "وه",
        "گره",
        "زره",
        "شبه",
        "فربه",
        "شبیه",
        "فقیه",
        "توجیه",
        "تنبیه",
        "تشبیه",
        "کریه",
        "وجیه",
        "سفیه",
        "تنزیه",
    ]
)
_SILENT_VAV_HEH = frozenset(["میوه", "شیوه", "بیوه", "جلوه", "قهوه", "نحوه", "رشوه", "عشوه"])
_HEH_SUFFIX = "ای|ام|ات|اش|ایم|اید|اند|ی"


class ZwnjHehSuffix(RegexRule):
    code = "PN205"
    name = "zwnj-heh-suffix"
    category = "zwnj"
    severity = Severity.WARNING
    title_en = "ZWNJ in suffixes after silent «ه»"
    title_fa = "نیم‌فاصله در پسوندهای پس از «ه» ناملفوظ"
    description_en = (
        "After a silent «ه», the suffixes «ای ام ات اش ایم اید اند» and the ezafe «ی» are attached "
        'with a ZWNJ: «خانه ای» → «خانه‌ای», «رفته اند» → «رفته‌اند». With `ezafe = "hamza"`, the '
        "ezafe is written as «هٔ» instead («خانه ی من» → «خانهٔ من»). Words with a pronounced «ه» "
        "(«راه»، «کوه»، «شبیه»…) are skipped."
    )
    description_fa = (
        "پس از «ه» ناملفوظ، پسوندهای «ای، ام، ات، اش، ایم، اید، اند» و «ی» اضافه با نیم‌فاصله "
        'می‌آیند: «خانه ای» ← «خانه‌ای» و «رفته اند» ← «رفته‌اند». با `ezafe = "hamza"` اضافه '
        "به صورت «هٔ» نوشته می‌شود («خانه ی من» ← «خانهٔ من»). واژه‌هایی با «ه» ملفوظ "
        "(«راه»، «کوه»، «شبیه») نادیده گرفته می‌شوند."
    )
    message_en = "Attach «{0}» to «{1}» with a ZWNJ"
    message_fa = "«{0}» را با نیم‌فاصله به «{1}» بچسبانید"
    examples = (Example("خانه ای", "خانه‌ای"), Example("رفته اند", "رفته‌اند"), Example("نامه ی من", "نامه‌ی من"))
    options = ("ezafe",)
    pattern = re.compile(f"(?<=[{LETTER_RANGES}]\u0647)(?:([ \t]+)({_HEH_SUFFIX})|({ZWNJ})(ی)){_END}")

    def replace(self, match: re.Match[str], text: str, ctx: Context) -> Finding | None:
        word = word_before(text, match.start())
        letters = word.replace(ZWNJ, "")
        if len(letters) < 2 or word in _PRONOUNCED_HEH:
            return None
        if letters[-2] in "اآ" or (letters[-2] == "و" and word not in _SILENT_VAV_HEH):
            return None
        hamza = ctx.config.ezafe == "hamza"
        if match.group(3) is not None:  # already «ه‌ی»
            if not hamza:
                return None
            return Finding(
                match.start(),
                match.end(),
                "\u0654",
                "Use «هٔ» for the ezafe (ezafe = hamza)",
                "برای اضافه از «هٔ» استفاده کنید",
            )
        suffix = match.group(2)
        replacement = "\u0654" if (suffix == "ی" and hamza) else ZWNJ + suffix
        return Finding(
            match.start(),
            match.end(),
            replacement,
            self.message_en.format(suffix, word),
            self.message_fa.format(suffix, word),
        )
