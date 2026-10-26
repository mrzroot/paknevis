"""Python API: fix and lint, positions, sorting, option overrides, disabling rules, severities, syntax aliases, applying findings and performance on large text."""
from __future__ import annotations

import json
import re

import pytest

import paknevis
from paknevis import Config, Diagnostic, Linter, Severity
from paknevis.engine import apply_findings, max_severity
from paknevis.models import Finding


def test_version() -> None:
    assert re.fullmatch(r"\d+\.\d+\.\d+", paknevis.__version__)


def test_fix_and_lint_basic() -> None:
    assert paknevis.fix("كتاب هاي من") == "کتاب\u200cهای من"
    diagnostics = paknevis.lint("علي")
    assert [d.rule for d in diagnostics] == ["arabic-yeh"]
    (d,) = diagnostics
    assert isinstance(d, Diagnostic)
    assert (d.line, d.column, d.end_line, d.end_column) == (1, 3, 1, 4)
    assert d.code == "PN101"
    assert d.severity is Severity.ERROR
    assert d.fixable


def test_empty_text() -> None:
    assert paknevis.fix("") == ""
    assert paknevis.lint("") == []


def test_multiline_positions() -> None:
    text = "سطر اول\nسطر دوم علي"
    (d,) = paknevis.lint(text)
    assert (d.line, d.column) == (2, 11)
    assert text[d.offset] == "ي"


def test_diagnostics_are_sorted() -> None:
    diagnostics = paknevis.lint("سلام , علي ? كتاب")
    offsets = [d.offset for d in diagnostics]
    assert offsets == sorted(offsets)


def test_to_dict_is_json_serialisable() -> None:
    (d,) = paknevis.lint("علي")
    data = d.to_dict()
    assert data["severity"] == "error"
    assert data["fixable"] is True
    assert json.loads(json.dumps(data, ensure_ascii=False))["replacement"] == "ی"


def test_format() -> None:
    (d,) = paknevis.lint("علي")
    assert d.format() == "<text>:1:3: PN101 [arabic-yeh] Use Persian Yeh «ی» instead of Arabic «ي»"
    assert "فارسی" in d.format(lang="fa")


def test_options_override_config() -> None:
    config = Config(digits="latin")
    assert paknevis.fix("سال ۱۴۰۲", config=config) == "سال 1402"
    assert paknevis.fix("سال ۱۴۰۲", config=config, digits="persian") == "سال ۱۴۰۲"


def test_disable_by_code_and_name() -> None:
    assert paknevis.fix("علي", disable=["PN101"]) == "علي"
    assert paknevis.fix("علي", disable=["arabic-yeh"]) == "علي"
    assert paknevis.fix("علي", disable="arabic-yeh, kashida") == "علي"


def test_unknown_rule_raises() -> None:
    with pytest.raises(KeyError, match="unknown rule"):
        paknevis.lint("x", disable=["no-such-rule"])


def test_unknown_option_raises() -> None:
    with pytest.raises(TypeError):
        paknevis.fix("x", no_such_option=True)


def test_severity_override() -> None:
    config = Config.from_mapping({"severity": {"PN101": "info"}})
    (d,) = paknevis.lint("علي", config=config)
    assert d.severity is Severity.INFO


def test_syntax_aliases() -> None:
    assert paknevis.fix("`كتاب`", syntax="md") == "`كتاب`"
    with pytest.raises(ValueError, match="unknown syntax"):
        paknevis.fix("x", syntax="rst")


def test_linter_fix_with_report() -> None:
    linter = Linter(Config(teh_marbuta="warn"))
    result = linter.fix_with_report("علي و رحمة", path="a.txt")
    assert result.changed
    assert result.text == "علی و رحمة"
    assert {d.rule for d in result.diagnostics} == {"arabic-yeh", "arabic-teh-marbuta"}
    assert [d.rule for d in result.remaining] == ["arabic-teh-marbuta"]
    assert result.diagnostics[0].path == "a.txt"
    unchanged = linter.fix_with_report("سلام")
    assert not unchanged.changed and unchanged.remaining == ()


def test_apply_findings_skips_overlaps_and_unfixable() -> None:
    findings = [Finding(0, 2, "X"), Finding(1, 3, "Y"), Finding(3, 4, None), Finding(4, 4, "+")]
    assert apply_findings("abcde", findings) == "Xcd+e"


def test_max_severity() -> None:
    assert max_severity([]) is None
    assert max_severity(paknevis.lint("علي , سلام لطفا")) is Severity.ERROR


def test_severity_parse() -> None:
    assert Severity.parse("ERROR") is Severity.ERROR
    assert Severity.parse(Severity.INFO) is Severity.INFO
    assert Severity.INFO.rank < Severity.WARNING.rank < Severity.ERROR.rank
    with pytest.raises(ValueError, match="unknown severity"):
        Severity.parse("fatal")


def test_get_rule() -> None:
    assert paknevis.get_rule("pn203").name == "zwnj-plural"
    assert paknevis.get_rule("zwnj-plural").code == "PN203"
    assert repr(paknevis.get_rule("PN101")) == "<Rule PN101 arabic-yeh>"


def test_large_document_is_fast() -> None:
    import time

    paragraph = "این یک متن آزمایشی است , که `كد` و https://example.com دارد ? کتاب ها را می خوانم.\n"
    text = paragraph * 2000
    start = time.perf_counter()
    fixed = paknevis.fix(text, syntax="markdown")
    assert time.perf_counter() - start < 30
    assert fixed.count("`كد`") == 2000
