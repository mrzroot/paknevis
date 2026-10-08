"""Rule registry.

Rules run in the order listed in :data:`ALL_RULES` when fixing: character
normalisation first, then whitespace, ZWNJ and punctuation, and spelling last.
"""

from __future__ import annotations

from .base import Context, Example, RegexRule, Rule
from .characters import ArabicDigits, ArabicHeh, ArabicKaf, ArabicYeh, DigitStyle, TehMarbuta
from .punctuation import (
    BracketSpacing,
    Ellipsis,
    PersianComma,
    PersianQuestionMark,
    PersianQuotes,
    PersianSemicolon,
    RepeatedPunctuation,
    SpaceAfterPunctuation,
    SpaceBeforePunctuation,
)
from .spelling import Spelling, Tanvin
from .whitespace import Kashida, MultipleSpaces, TrailingWhitespace
from .zwnj import ZwnjCleanup, ZwnjComparative, ZwnjHehSuffix, ZwnjMiPrefix, ZwnjPlural

__all__ = ["ALL_RULES", "Context", "Example", "RegexRule", "Rule", "get_rule", "resolve_rule_name"]

ALL_RULES: tuple[Rule, ...] = (
    # characters
    ArabicYeh(),
    ArabicKaf(),
    ArabicHeh(),
    TehMarbuta(),
    ArabicDigits(),
    DigitStyle(),
    # whitespace & zwnj cleanup
    Kashida(),
    ZwnjCleanup(),
    MultipleSpaces(),
    TrailingWhitespace(),
    # spelling (before ZWNJ heuristics so compounds win)
    Spelling(),
    Tanvin(),
    # zwnj
    ZwnjMiPrefix(),
    ZwnjPlural(),
    ZwnjComparative(),
    ZwnjHehSuffix(),
    # punctuation
    PersianComma(),
    PersianSemicolon(),
    PersianQuestionMark(),
    Ellipsis(),
    RepeatedPunctuation(),
    PersianQuotes(),
    SpaceBeforePunctuation(),
    SpaceAfterPunctuation(),
    BracketSpacing(),
)

_BY_KEY: dict[str, Rule] = {}
for _rule in ALL_RULES:
    _BY_KEY[_rule.name] = _rule
    _BY_KEY[_rule.code.lower()] = _rule


def get_rule(key: str) -> Rule:
    """Look up a rule by name (``arabic-yeh``) or code (``PN101``).

    Raises:
        KeyError: if no such rule exists.
    """
    try:
        return _BY_KEY[key.strip().lower()]
    except KeyError:
        raise KeyError(f"unknown rule {key!r}; run `paknevis rules` to list rules") from None


def resolve_rule_name(key: str) -> str:
    """Normalise a rule name or code to the rule's name."""
    return get_rule(key).name
