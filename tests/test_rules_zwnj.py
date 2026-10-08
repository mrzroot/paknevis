from __future__ import annotations

import pytest

import paknevis

from helpers import Z, fixed_by


class TestCleanup:
    @pytest.mark.parametrize(
        ("before", "after"),
        [
            (f"کتاب{Z}{Z}ها", f"کتاب{Z}ها"),
            (f"کتاب{Z}{Z}{Z}ها", f"کتاب{Z}ها"),
            (f"میز{Z} هست", "میز هست"),
            (f"و {Z}دفتر", "و دفتر"),
            (f"{Z}سلام", "سلام"),
            (f"سلام{Z}", "سلام"),
            (f"سلام{Z}.", "سلام."),
            (f"abc{Z}def", "abcdef"),
            (f"۱۲{Z}۳", "۱۲۳"),
        ],
    )
    def test_cleanup(self, before: str, after: str) -> None:
        assert fixed_by("zwnj-cleanup", before) == after

    @pytest.mark.parametrize("text", [f"کتاب{Z}ها", f"می{Z}روم", f"خانه{Z}ای"])
    def test_valid_zwnj_kept(self, text: str) -> None:
        assert fixed_by("zwnj-cleanup", text) == text


class TestMiPrefix:
    @pytest.mark.parametrize(
        ("before", "after"),
        [
            ("می روم", f"می{Z}روم"),
            ("نمی روم", f"نمی{Z}روم"),
            ("می  خواهم", f"می{Z}خواهم"),
            ("میروم", f"می{Z}روم"),
            ("نمیدانم", f"نمی{Z}دانم"),
            ("میخواستند", f"می{Z}خواستند"),
            ("میتوان", f"می{Z}توان"),
            ("میکنیم", f"می{Z}کنیم"),
            ("میشود", f"می{Z}شود"),
            ("میباشد", f"می{Z}باشد"),
            ("میرفت", f"می{Z}رفت"),
            ("میآید", f"می{Z}آید"),
            ("او هر روز می نوشت", f"او هر روز می{Z}نوشت"),
        ],
    )
    def test_fixes(self, before: str, after: str) -> None:
        assert fixed_by("zwnj-mi-prefix", before) == after

    @pytest.mark.parametrize(
        "text",
        [
            "میز",
            "میوه",
            "میدان",
            "میدانی",
            "میلیون",
            "میان",
            "میمون",
            "میهمان",
            "میراث",
            "میزان",
            "میگو",
            "شمیم",
            "کمی رفت",
            "می و ساغر",
            f"می{Z}روم",
        ],
    )
    def test_non_verbs_untouched(self, text: str) -> None:
        assert fixed_by("zwnj-mi-prefix", text) == text


class TestPlural:
    @pytest.mark.parametrize(
        ("before", "after"),
        [
            ("کتاب ها", f"کتاب{Z}ها"),
            ("کتاب های من", f"کتاب{Z}های من"),
            ("روش هایی", f"روش{Z}هایی"),
            ("دوست هایم", f"دوست{Z}هایم"),
            ("کتاب هایشان", f"کتاب{Z}هایشان"),
            ("این ها", f"این{Z}ها"),
            ("آن ها رفتند", f"آن{Z}ها رفتند"),
            ("کار هاست", f"کار{Z}هاست"),
        ],
    )
    def test_fixes(self, before: str, after: str) -> None:
        assert fixed_by("zwnj-plural", before) == after

    @pytest.mark.parametrize("text", ["کتابها", "و ها", "سلام هادی", "کتاب هامون", "book ها", "۱۲ ها"])
    def test_untouched(self, text: str) -> None:
        assert fixed_by("zwnj-plural", text) == text


class TestComparative:
    @pytest.mark.parametrize(
        ("before", "after"),
        [
            ("بزرگ ترین", f"بزرگ{Z}ترین"),
            ("زیبا ترین شهر", f"زیبا{Z}ترین شهر"),
            ("بیش تر", f"بیش{Z}تر"),
            ("سریع تر", f"سریع{Z}تر"),
            ("خوشمزه تر از", f"خوشمزه{Z}تر از"),
        ],
    )
    def test_fixes(self, before: str, after: str) -> None:
        assert fixed_by("zwnj-comparative", before) == after

    @pytest.mark.parametrize("text", ["لباس تر", "بزرگترین", "از ترین", "دست ترکید", "و تر"])
    def test_untouched(self, text: str) -> None:
        assert fixed_by("zwnj-comparative", text) == text


class TestHehSuffix:
    @pytest.mark.parametrize(
        ("before", "after"),
        [
            ("خانه ای", f"خانه{Z}ای"),
            ("رفته اند", f"رفته{Z}اند"),
            ("دیده ام", f"دیده{Z}ام"),
            ("نامه ات", f"نامه{Z}ات"),
            ("خانه اش", f"خانه{Z}اش"),
            ("رفته ایم", f"رفته{Z}ایم"),
            ("رفته اید", f"رفته{Z}اید"),
            ("نامه ی من", f"نامه{Z}ی من"),
            ("میوه ای", f"میوه{Z}ای"),
        ],
    )
    def test_fixes(self, before: str, after: str) -> None:
        assert fixed_by("zwnj-heh-suffix", before) == after

    @pytest.mark.parametrize(
        "text",
        ["راه ام", "کوه ای", "شبیه ام", "به ای", "که ای", "دانشگاه ام", "خانه ایران", "خانه یک", "گروه ای", "ه ای"],
    )
    def test_untouched(self, text: str) -> None:
        assert fixed_by("zwnj-heh-suffix", text) == text

    def test_hamza_style(self) -> None:
        assert fixed_by("zwnj-heh-suffix", "نامه ی من", ezafe="hamza") == "نامهٔ من"
        assert fixed_by("zwnj-heh-suffix", f"نامه{Z}ی من", ezafe="hamza") == "نامهٔ من"
        assert fixed_by("zwnj-heh-suffix", "خانه ای", ezafe="hamza") == f"خانه{Z}ای"

    def test_zwnj_style_keeps_hamza_form(self) -> None:
        assert paknevis.fix("نامهٔ من") == "نامهٔ من"
