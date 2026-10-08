"""Property-based tests (Hypothesis): idempotency and protection invariants."""

from __future__ import annotations

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import paknevis

Z = "\u200c"

# An alphabet biased towards the characters the rules care about.
ALPHABET = (
    "ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهیآأئؤءةيكىھ"
    "۰۱۲۳۴۵۶۷۸۹٠١٢٣0123456789"
    "abcxyzABC"
    " \t\n" + Z + "\u0640\u064b\u0654"
    '.,;:!?،؛؟«»()[]"“”…-_/%٪*#`$<>{}\\|'
)
WORDS = [
    "می",
    "نمی",
    "ها",
    "های",
    "تر",
    "ترین",
    "ای",
    "ام",
    "اند",
    "ی",
    "خانه",
    "کتاب",
    "اطاق",
    "لطفا",
    "نرم",
    "افزار",
    "روم",
]

texts = st.lists(st.one_of(st.text(alphabet=ALPHABET, max_size=12), st.sampled_from(WORDS)), max_size=25).map(
    lambda parts: " ".join(parts)
)
syntaxes = st.sampled_from(paknevis.SYNTAXES)
digit_styles = st.sampled_from(["persian", "latin", "keep"])
ezafe_styles = st.sampled_from(["zwnj", "hamza"])

COMMON = settings(max_examples=300, deadline=None, suppress_health_check=[HealthCheck.too_slow])


@COMMON
@given(texts, syntaxes, digit_styles, ezafe_styles)
def test_fix_is_idempotent(text: str, syntax: str, digits: str, ezafe: str) -> None:
    once = paknevis.fix(text, syntax=syntax, digits=digits, ezafe=ezafe)
    assert paknevis.fix(once, syntax=syntax, digits=digits, ezafe=ezafe) == once


@COMMON
@given(texts)
def test_fixed_text_has_no_fixable_diagnostics(text: str) -> None:
    fixed = paknevis.fix(text)
    assert [d for d in paknevis.lint(fixed) if d.fixable] == []


@COMMON
@given(texts, syntaxes)
def test_diagnostic_offsets_are_consistent(text: str, syntax: str) -> None:
    for d in paknevis.lint(text, syntax=syntax):
        assert 0 <= d.offset <= d.end_offset <= len(text)
        assert text[d.offset : d.end_offset] == d.original
        assert d.line >= 1 and d.column >= 1


@COMMON
@given(texts)
def test_fix_never_changes_newline_count(text: str) -> None:
    assert paknevis.fix(text).count("\n") == text.count("\n")


PROTECTED_MD = [
    "`كتاب , ?`",
    "https://example.com/كتاب?a=1,2",
    "info@example.com",
    '<span title="ي , ك">',
    "$a , b ?$",
    "[^كتاب]",
    ":smile:",
]
PROSE_ALPHABET = "".join(c for c in ALPHABET if c not in "`$<>[]:\\*_{}\n")
prose = st.lists(st.one_of(st.text(alphabet=PROSE_ALPHABET, max_size=12), st.sampled_from(WORDS)), max_size=10).map(
    " ".join
)


@COMMON
@given(st.lists(st.tuples(prose, st.sampled_from(PROTECTED_MD)), min_size=1, max_size=6), prose)
def test_markdown_protected_tokens_survive(pairs: list[tuple[str, str]], tail: str) -> None:
    text = "".join(f"{p} {token} " for p, token in pairs) + tail
    fixed = paknevis.fix(text, syntax="markdown")
    for _, token in pairs:
        assert fixed.count(token) >= text.count(token), token


code_blocks = st.text(alphabet=ALPHABET.replace("`", ""), max_size=40)


@COMMON
@given(texts, code_blocks, texts)
def test_fenced_code_is_byte_identical(before: str, code: str, after: str) -> None:
    code = code.replace("\n", " ")
    text = f"{before}\n\n```\n{code}\n```\n\n{after}"
    fixed = paknevis.fix(text, syntax="markdown")
    assert f"\n```\n{code}\n```\n" in fixed


@COMMON
@given(texts, st.sampled_from(["$x , y ?$", r"\cite{كتاب,ها}", r"\lr{a , b ?}", "% كامنت , ?"]))
def test_latex_protected_survives(text: str, token: str) -> None:
    sample = f"{text.replace('%', '').replace('$', '').replace(chr(92), '')}\n{token}\n"
    assert token in paknevis.fix(sample, syntax="latex")


@COMMON
@given(texts)
def test_lint_and_fix_never_crash_on_any_syntax(text: str) -> None:
    for syntax in paknevis.SYNTAXES:
        paknevis.lint(text, syntax=syntax)
        paknevis.fix(text, syntax=syntax)
