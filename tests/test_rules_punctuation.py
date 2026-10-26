"""Punctuation rules: Latin marks to Persian marks, spacing around punctuation."""
from __future__ import annotations

import pytest

import paknevis

from helpers import fixed_by


@pytest.mark.parametrize(
    ("rule", "before", "after"),
    [
        ("persian-comma", "سیب, پرتقال", "سیب، پرتقال"),
        ("persian-comma", "سیب , پرتقال", "سیب ، پرتقال"),
        ("persian-comma", "«سلام», گفت", "«سلام»، گفت"),
        ("persian-semicolon", "سرد بود; باران", "سرد بود؛ باران"),
        ("persian-question-mark", "چطوری?", "چطوری؟"),
        ("persian-question-mark", "چطوری ?", "چطوری ؟"),
    ],
)
def test_latin_marks_become_persian(rule: str, before: str, after: str) -> None:
    assert fixed_by(rule, before) == after


@pytest.mark.parametrize(
    ("rule", "text"),
    [
        ("persian-comma", "apple, orange"),
        ("persian-comma", "۱,۰۰۰"),
        ("persian-comma", "عدد 1,000"),
        ("persian-comma", "قیمت,2"),
        ("persian-semicolon", "a; b"),
        ("persian-question-mark", "What?"),
        ("persian-question-mark", "سلام?a=1"),
    ],
)
def test_latin_marks_kept_outside_persian(rule: str, text: str) -> None:
    assert fixed_by(rule, text) == text


@pytest.mark.parametrize(
    ("before", "after"),
    [
        ("سلام ،", "سلام،"),
        ("خوبی ؟", "خوبی؟"),
        ("بله ؛ نه", "بله؛ نه"),
        ("تمام .", "تمام."),
        ("نکته :", "نکته:"),
        ("عالی !", "عالی!"),
        ("Python ،", "Python،"),
    ],
)
def test_space_before_punctuation(before: str, after: str) -> None:
    assert fixed_by("space-before-punctuation", before) == after


@pytest.mark.parametrize("text", ["Hello .", "a :smile:", "« ،", "سلام .NET", "تصویر ![x]", "    ، اول سطر"])
def test_space_before_punctuation_untouched(text: str) -> None:
    assert fixed_by("space-before-punctuation", text) == text


@pytest.mark.parametrize(
    ("before", "after"),
    [
        ("سلام،خوبی", "سلام، خوبی"),
        ("بله؛نه", "بله؛ نه"),
        ("چرا؟برای", "چرا؟ برای"),
        ("تمام.بعدی", "تمام. بعدی"),
        ("نکته:متن", "نکته: متن"),
        ("عالی!واقعاً", "عالی! واقعاً"),
        ("گفت:«سلام»", "گفت: «سلام»"),
        ("سلام،Python", "سلام، Python"),
    ],
)
def test_space_after_punctuation(before: str, after: str) -> None:
    assert fixed_by("space-after-punctuation", before) == after


@pytest.mark.parametrize(
    "text",
    ["ه.ش", "ق.م", "۱.۵", "example.com", "فایل.txt", "۱۲:۳۰", "۱،۲", "a.b", "؟!", "سلام.\nخوبی"],
)
def test_space_after_punctuation_untouched(text: str) -> None:
    assert fixed_by("space-after-punctuation", text) == text


@pytest.mark.parametrize(
    ("before", "after"),
    [
        ("کتاب( خوب )است", "کتاب (خوب) است"),
        ("( سلام )", "(سلام)"),
        ("گفت« سلام »و رفت", "گفت «سلام» و رفت"),
        ("«  سلام  »", "«سلام»"),
        ("متن(۱)", "متن (۱)"),
    ],
)
def test_bracket_spacing(before: str, after: str) -> None:
    assert fixed_by("bracket-spacing", before) == after


@pytest.mark.parametrize("text", ["f( x )", "(a) b", "(سلام) است", "foo(bar)"])
def test_bracket_spacing_untouched(text: str) -> None:
    assert fixed_by("bracket-spacing", text) == text


@pytest.mark.parametrize(
    ("before", "after"),
    [
        ('او گفت "سلام"', "او گفت «سلام»"),
        ('"سلام دنیا" و "خداحافظ"', "«سلام دنیا» و «خداحافظ»"),
        ("“سلام”", "«سلام»"),
        ("”سلام“", "«سلام»"),
        ('" سلام "', "«سلام»"),
        ('"Hello" و "سلام"', '"Hello" و «سلام»'),
    ],
)
def test_persian_quotes(before: str, after: str) -> None:
    assert fixed_by("persian-quotes", before) == after


@pytest.mark.parametrize("text", ['"Hello world"', '"سلام', 'a "b" c', '"\n"'])
def test_persian_quotes_untouched(text: str) -> None:
    assert fixed_by("persian-quotes", text) == text


@pytest.mark.parametrize(
    ("before", "after"),
    [("و غیره...", "و غیره…"), ("صبر کن . . .", "صبر کن …"), ("...و بعد", "…و بعد"), ("خب.....", "خب…")],
)
def test_ellipsis(before: str, after: str) -> None:
    assert fixed_by("ellipsis", before) == after


@pytest.mark.parametrize("text", ["wait...", "1...5", "..", "سلام.."])
def test_ellipsis_untouched(text: str) -> None:
    assert fixed_by("ellipsis", text) == text


@pytest.mark.parametrize(
    ("before", "after"), [("واقعاً؟؟؟", "واقعاً؟"), ("نه!!!", "نه!"), ("سلام،،", "سلام،"), ("بله؛؛", "بله؛")]
)
def test_repeated_punctuation(before: str, after: str) -> None:
    assert fixed_by("repeated-punctuation", before) == after


def test_repeated_exclamation_outside_persian_untouched() -> None:
    assert fixed_by("repeated-punctuation", "Wow!!!") == "Wow!!!"


def test_full_pipeline_sentence() -> None:
    before = 'او گفت "فردا می آیم" , اما نیامد ...آیا می دانی چرا ?'
    after = "او گفت «فردا می‌آیم»، اما نیامد… آیا می‌دانی چرا؟"
    assert paknevis.fix(before) == after
