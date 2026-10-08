from __future__ import annotations

import re

import pytest

import paknevis
from paknevis.rules import ALL_RULES, Rule

RULE_IDS = [rule.name for rule in ALL_RULES]


def test_codes_and_names_unique() -> None:
    assert len({r.code for r in ALL_RULES}) == len(ALL_RULES)
    assert len({r.name for r in ALL_RULES}) == len(ALL_RULES)


def test_at_least_twenty_rules() -> None:
    assert len(ALL_RULES) >= 20


@pytest.mark.parametrize("rule", ALL_RULES, ids=RULE_IDS)
def test_metadata_complete(rule: Rule) -> None:
    assert re.fullmatch(r"PN[1-5]\d\d", rule.code)
    assert re.fullmatch(r"[a-z]+(-[a-z]+)*", rule.name)
    assert rule.category in {"characters", "zwnj", "punctuation", "whitespace", "spelling"}
    for text in (
        rule.title_en,
        rule.title_fa,
        rule.description_en,
        rule.description_fa,
        rule.message_en,
        rule.message_fa,
    ):
        assert text.strip()
    assert re.search("[\u0600-\u06ff]", rule.title_fa)
    assert re.search("[\u0600-\u06ff]", rule.description_fa)
    assert rule.examples, "every rule needs at least one example"


@pytest.mark.parametrize(
    ("rule", "example"),
    [(rule, example) for rule in ALL_RULES for example in rule.examples],
    ids=lambda value: getattr(value, "name", None) or getattr(value, "before", "")[:12],
)
def test_examples(rule: Rule, example) -> None:  # type: ignore[no-untyped-def]
    options = {"teh_marbuta": "heh"} if rule.name == "arabic-teh-marbuta" else {}
    hits = {d.rule for d in paknevis.lint(example.before, **options)}
    assert rule.name in hits
    assert paknevis.fix(example.before, **options) == example.after
    assert rule.name not in {d.rule for d in paknevis.lint(example.after, **options)}
