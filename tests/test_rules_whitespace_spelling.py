"""Whitespace and spelling rules: repeated spaces, trailing whitespace, kashida, spelling lists and tanvin."""
from __future__ import annotations

import pytest

import paknevis

from helpers import Z, fixed_by, rules_hit


class TestMultipleSpaces:
    def test_collapses(self) -> None:
        assert fixed_by("multiple-spaces", "سلام    دنیا") == "سلام دنیا"

    @pytest.mark.parametrize(
        "text",
        ["    سلام دنیا", "hello    world", "سلام\t\tدنیا", "سلام  \nدنیا"],
    )
    def test_untouched(self, text: str) -> None:
        assert fixed_by("multiple-spaces", text) == text

    def test_markdown_table_rows_untouched(self) -> None:
        text = "| ستون  اول | دوم |"
        assert paknevis.fix(text, syntax="markdown", disable=["trailing-whitespace"]) == text
        assert paknevis.fix(text, syntax="plain") == "| ستون اول | دوم |"


class TestTrailingWhitespace:
    def test_removed(self) -> None:
        assert fixed_by("trailing-whitespace", "سلام  \t\nدنیا   ") == "سلام\nدنیا"

    def test_crlf_preserved(self) -> None:
        assert fixed_by("trailing-whitespace", "سلام  \r\nدنیا\r\n") == "سلام\r\nدنیا\r\n"

    def test_markdown_hard_break_kept(self) -> None:
        text = "خط اول  \nخط دوم"
        assert paknevis.fix(text, syntax="markdown") == text
        assert paknevis.fix("خط اول \nخط دوم", syntax="markdown") == "خط اول\nخط دوم"

    def test_space_before_inline_code_is_not_trailing(self) -> None:
        text = "این را اجرا کنید `pip install x`\n"
        assert paknevis.fix(text, syntax="markdown") == text


class TestKashida:
    @pytest.mark.parametrize(("before", "after"), [("سـلام", "سلام"), ("بـــزرگ", "بزرگ"), ("محمـد", "محمد")])
    def test_removed(self, before: str, after: str) -> None:
        assert fixed_by("kashida", before) == after

    def test_standalone_kept(self) -> None:
        assert fixed_by("kashida", "ـــــ") == "ـــــ"


class TestSpelling:
    @pytest.mark.parametrize(
        ("before", "after"),
        [
            ("اطاق", "اتاق"),
            ("اطاق‌ها", "اتاق‌ها"),
            ("سپاسگذارم", "سپاسگزارم"),
            ("برگذاری جلسه", "برگزاری جلسه"),
            ("نرم افزار", f"نرم{Z}افزار"),
            ("نرم  افزار", f"نرم{Z}افزار"),
            ("بروزرسانی", f"به{Z}روزرسانی"),
            ("وبسایت", f"وب{Z}سایت"),
            ("پائین", "پایین"),
        ],
    )
    def test_fixes(self, before: str, after: str) -> None:
        assert fixed_by("spelling", before) == after

    @pytest.mark.parametrize("text", ["اطاقک", "شکرگزار", "بروز", "خاستگاه", "نرم‌افزار"])
    def test_untouched(self, text: str) -> None:
        assert fixed_by("spelling", text) == text

    def test_message(self) -> None:
        (d,) = [d for d in paknevis.lint("اطاق") if d.rule == "spelling"]
        assert d.message == "Did you mean «اتاق»?"
        assert d.message_fa == "آیا منظورتان «اتاق» است؟"
        assert d.replacement == "اتاق"

    def test_inline_config_entries(self) -> None:
        assert paknevis.fix("وب سرویس", spelling={"وب سرویس": f"وب{Z}سرویس"}) == f"وب{Z}سرویس"

    def test_user_dictionary_file(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        words = tmp_path / "words.yaml"
        words.write_text("- {wrong: گوگل کروم, right: گوگل‌کروم}\n", encoding="utf-8")
        config = paknevis.Config(dictionaries=(str(words),), root=tmp_path)
        assert paknevis.fix("گوگل کروم", config=config) == "گوگل‌کروم"


class TestTanvin:
    @pytest.mark.parametrize(("before", "after"), [("لطفا", "لطفاً"), ("مثلا این", "مثلاً این"), ("حتما!", "حتماً!")])
    def test_fixes(self, before: str, after: str) -> None:
        assert fixed_by("tanvin", before) == after

    @pytest.mark.parametrize("text", ["لطفاً", "جدا", "ابتدا", "مثلاها"])
    def test_untouched(self, text: str) -> None:
        assert fixed_by("tanvin", text) == text

    def test_can_be_disabled(self) -> None:
        assert "tanvin" not in rules_hit("لطفا", disable=["tanvin"])
