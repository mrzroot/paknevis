"""Unicode character classes used throughout paknevis.

All constants are plain strings or compiled regular expressions so that they
can be shared by rules and format handlers without import cycles.
"""

from __future__ import annotations

import re

ZWNJ = "\u200c"
"""Zero-width non-joiner (نیم‌فاصله)."""

KASHIDA = "\u0640"
"""Arabic tatweel / kashida (ـ)."""

PERSIAN_YEH = "\u06cc"  # ی
PERSIAN_KAF = "\u06a9"  # ک
HEH = "\u0647"  # ه
HAMZA_ABOVE = "\u0654"  # ٔ

ARABIC_YEH = "\u064a"  # ي
ALEF_MAKSURA = "\u0649"  # ى
ARABIC_KAF = "\u0643"  # ك
TEH_MARBUTA = "\u0629"  # ة

PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
LATIN_DIGITS = "0123456789"

# Letters of the Arabic script block that occur in Persian (and Arabic) text.
LETTER_RANGES = "\u0621-\u063a\u0641-\u064a\u0671-\u06d3\u06d5\u06fa-\u06fc\u06ff"
# Combining marks (harakat, superscript alef, hamza above/below).
MARK_RANGES = "\u064b-\u065f\u0670"

LETTER_CLASS = f"[{LETTER_RANGES}]"
"""Regex character class matching one Persian/Arabic-script letter."""

WORD_CHAR_CLASS = f"[{LETTER_RANGES}{MARK_RANGES}{KASHIDA}]"
"""A letter, combining mark or kashida — anything that is *inside* a word."""

NOT_WORD_BEFORE = f"(?<![{LETTER_RANGES}{MARK_RANGES}{KASHIDA}{ZWNJ}])"
"""Lookbehind asserting that no Persian word character (or ZWNJ) precedes."""

NOT_WORD_AFTER = f"(?![{LETTER_RANGES}{MARK_RANGES}{KASHIDA}])"
"""Lookahead asserting that no Persian word character follows (ZWNJ is allowed)."""

NOT_WORD_OR_ZWNJ_AFTER = f"(?![{LETTER_RANGES}{MARK_RANGES}{KASHIDA}{ZWNJ}])"
"""Lookahead asserting that neither a Persian word character nor ZWNJ follows."""

PERSIAN_WORD = f"{LETTER_CLASS}(?:[{LETTER_RANGES}{MARK_RANGES}{KASHIDA}{ZWNJ}]*{LETTER_CLASS})?[{MARK_RANGES}]*"
"""Regex for a Persian word (letters, optionally joined by ZWNJ)."""

_LETTER_RE = re.compile(LETTER_CLASS)
_LATIN_LETTER_RE = re.compile(r"[A-Za-z]")

# Letters that never connect to the following letter. A ZWNJ after these is
# visually redundant (but harmless), so rules treat them specially.
NON_JOINING_LETTERS = "اآأإدذرزژوؤءة"

PERSIAN_PUNCTUATION = "،؛؟«»"
SPACES = " \t"


def is_persian_letter(char: str) -> bool:
    """Return ``True`` if *char* is a single Persian/Arabic-script letter."""
    return bool(char) and _LETTER_RE.fullmatch(char) is not None


def is_latin_letter(char: str) -> bool:
    """Return ``True`` if *char* is an ASCII Latin letter."""
    return bool(char) and _LATIN_LETTER_RE.fullmatch(char) is not None


def contains_persian(text: str) -> bool:
    """Return ``True`` if *text* contains at least one Persian letter."""
    return _LETTER_RE.search(text) is not None


def to_persian_digits(text: str) -> str:
    """Convert Latin and Arabic-Indic digits in *text* to Persian digits."""
    return text.translate(_TO_PERSIAN)


def to_latin_digits(text: str) -> str:
    """Convert Persian and Arabic-Indic digits in *text* to Latin digits."""
    return text.translate(_TO_LATIN)


_TO_PERSIAN = str.maketrans(LATIN_DIGITS + ARABIC_DIGITS, PERSIAN_DIGITS * 2)
_TO_LATIN = str.maketrans(PERSIAN_DIGITS + ARABIC_DIGITS, LATIN_DIGITS * 2)
