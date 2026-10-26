"""Character rules: Arabic yeh/kaf, non-Persian heh and the default-mode warnings."""
from __future__ import annotations

import pytest

import paknevis

from helpers import fixed_by, rules_hit


@pytest.mark.parametrize(
    ("before", "after"),
    [
        ("علي", "علی"),
        ("مصطفى", "مصطفی"),
        ("يادداشت روز", "یادداشت روز"),
        ("اين", "این"),
    ],
)
def test_arabic_yeh(before: str, after: str) -> None:
    assert fixed_by("arabic-yeh", before) == after


@pytest.mark.parametrize(("before", "after"), [("كتاب", "کتاب"), ("كودك", "کودک"), ("يك", "یک")])
def test_arabic_kaf_and_yeh_together(before: str, after: str) -> None:
    assert paknevis.fix(before) == after


@pytest.mark.parametrize(("before", "after"), [("ھمه", "همه"), ("ہمہ", "همه"), ("ە", "ه")])
def test_non_persian_heh(before: str, after: str) -> None:
    assert fixed_by("non-persian-heh", before) == after


class TestTehMarbuta:
    def test_default_mode_only_warns(self) -> None:
        diagnostics = [d for d in paknevis.lint("رحمة") if d.rule == "arabic-teh-marbuta"]
        assert len(diagnostics) == 1
        assert not diagnostics[0].fixable
        assert paknevis.fix("رحمة") == "رحمة"

    def test_heh_mode(self) -> None:
        assert paknevis.fix("رحمة", teh_marbuta="heh") == "رحمه"

    def test_teh_mode(self) -> None:
        assert paknevis.fix("رحمة", teh_marbuta="teh") == "رحمت"


class TestArabicDigits:
    def test_to_persian_by_default(self) -> None:
        assert paknevis.fix("سال ١٤٠٣") == "سال ۱۴۰۳"

    def test_to_latin_when_configured(self) -> None:
        assert paknevis.fix("سال ١٤٠٣", digits="latin") == "سال 1403"

    def test_message_mentions_replacement(self) -> None:
        (d,) = [d for d in paknevis.lint("٢٥") if d.rule == "arabic-digits"]
        assert "۲۵" in d.message and "۲۵" in d.message_fa


class TestDigitStyle:
    @pytest.mark.parametrize(
        ("before", "after"),
        [
            ("سال 2024", "سال ۲۰۲۴"),
            ("50% رشد", "۵۰٪ رشد"),
            ("۵۰% رشد", "۵۰٪ رشد"),
            ("قیمت 1,000 تومان", "قیمت ۱,۰۰۰ تومان"),
            ("تاریخ 1402/05/12 است", "تاریخ ۱۴۰۲/۰۵/۱۲ است"),
            ("3تا سیب", "۳تا سیب"),
        ],
    )
    def test_persian_context(self, before: str, after: str) -> None:
        assert fixed_by("digit-style", before) == after

    @pytest.mark.parametrize(
        "text",
        [
            "از Python 3.12 استفاده کنید",
            "فایل 10GB است",
            "نسخهٔ v2 آمد",
            "حجم 5 MB است",
            "Windows 11 را نصب کنید",
            "2024",
            "H2O آب است",
        ],
    )
    def test_latin_context_is_kept(self, text: str) -> None:
        assert fixed_by("digit-style", text) == text

    def test_latin_style(self) -> None:
        assert fixed_by("digit-style", "سال ۱۴۰۲ و ۵۰٪", digits="latin") == "سال 1402 و 50%"

    def test_keep_style_disables(self) -> None:
        assert "digit-style" not in rules_hit("سال 2024", digits="keep")
        assert paknevis.fix("سال 2024", digits="keep") == "سال 2024"
