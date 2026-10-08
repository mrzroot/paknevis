from __future__ import annotations

from pathlib import Path

import pytest

from paknevis import Config, ConfigError, Severity, load_config
from paknevis.config import find_config_file
from paknevis.dictionary import DictionaryError, builtin_dictionary, load_dictionary_file, parse_dictionary


def test_defaults() -> None:
    config = Config()
    assert config.digits == "persian"
    assert config.ezafe == "zwnj"
    assert config.teh_marbuta == "warn"
    assert config.fail_on is Severity.WARNING


def test_from_mapping_accepts_dashes_and_underscores() -> None:
    config = Config.from_mapping(
        {
            "disable": ["kashida"],
            "teh-marbuta": "HEH",
            "latex_text_commands": "foo, bar",
            "fail-on": "error",
            "severity": {"spelling": "error"},
            "spelling": {"الف": "ب"},
            "exclude": ["vendor/**"],
        }
    )
    assert config.disable == frozenset({"kashida"})
    assert config.teh_marbuta == "heh"
    assert config.latex_text_commands == ("foo", "bar")
    assert config.fail_on is Severity.ERROR
    assert config.severity_for("spelling", "PN501", Severity.WARNING) is Severity.ERROR
    assert config.severity_for("kashida", "PN403", Severity.WARNING) is Severity.WARNING
    assert config.spelling_entries() == {"الف": "ب"}


@pytest.mark.parametrize(
    ("data", "message"),
    [
        ({"colour": "red"}, "unknown paknevis option"),
        ({"digits": "roman"}, "must be one of"),
        ({"disable": [1, 2]}, "list of strings"),
        ({"severity": ["x"]}, "table of rule"),
        ({"severity": {"x": "fatal"}}, "unknown severity"),
        ({"spelling": {"a": 1}}, "wrong = right"),
        ({"fail-on": "fatal"}, "fail-on"),
        ({"ezafe": 3}, "must be one of"),
    ],
)
def test_invalid_values(data: dict[str, object], message: str) -> None:
    with pytest.raises(ConfigError, match=message):
        Config.from_mapping(data)


def test_load_from_pyproject(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text('[tool.paknevis]\ndigits = "latin"\n', encoding="utf-8")
    sub = tmp_path / "docs"
    sub.mkdir()
    assert find_config_file(sub) == tmp_path / "pyproject.toml"
    config = load_config(start=sub)
    assert config.digits == "latin"
    assert config.root == tmp_path.resolve()


def test_pyproject_without_table_is_skipped(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'x'\n", encoding="utf-8")
    assert find_config_file(tmp_path) != tmp_path / "pyproject.toml"


def test_dot_paknevis_toml_takes_precedence(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text('[tool.paknevis]\ndigits = "latin"\n', encoding="utf-8")
    (tmp_path / ".paknevis.toml").write_text('digits = "keep"\n', encoding="utf-8")
    assert load_config(start=tmp_path).digits == "keep"


def test_dot_paknevis_toml_with_tool_table(tmp_path: Path) -> None:
    path = tmp_path / ".paknevis.toml"
    path.write_text('[tool.paknevis]\nezafe = "hamza"\n', encoding="utf-8")
    assert load_config(path).ezafe == "hamza"


def test_invalid_toml(tmp_path: Path) -> None:
    path = tmp_path / ".paknevis.toml"
    path.write_text("digits = ", encoding="utf-8")
    with pytest.raises(ConfigError, match="invalid TOML"):
        load_config(path)


def test_invalid_option_in_file_mentions_path(tmp_path: Path) -> None:
    path = tmp_path / ".paknevis.toml"
    path.write_text('digit = "latin"\n', encoding="utf-8")
    with pytest.raises(ConfigError, match=r"\.paknevis\.toml"):
        load_config(path)


def test_no_config_returns_defaults(tmp_path: Path) -> None:
    assert load_config(start=tmp_path / "missing").digits == "persian"


def test_merged_ignores_none() -> None:
    config = Config().merged(digits=None, ezafe="hamza")
    assert config.digits == "persian" and config.ezafe == "hamza"


class TestDictionaries:
    def test_builtin_dictionary_is_valid(self) -> None:
        entries = builtin_dictionary()
        assert len(entries) >= 50
        assert entries["اطاق"] == "اتاق"
        for wrong, right in entries.items():
            assert wrong != right
            assert wrong not in entries.values(), f"{wrong} is both wrong and right"

    def test_parse_mapping_and_list(self) -> None:
        assert parse_dictionary({"a": "b"}) == {"a": "b"}
        assert parse_dictionary([{"wrong": " a ", "right": "b", "note": "x"}]) == {"a": "b"}
        assert parse_dictionary(None) == {}

    @pytest.mark.parametrize("data", [[{"wrong": "a"}], "text", [{"wrong": "", "right": "b"}], {"a": 1}])
    def test_parse_errors(self, data: object) -> None:
        with pytest.raises(DictionaryError):
            parse_dictionary(data)

    def test_load_errors(self, tmp_path: Path) -> None:
        with pytest.raises(DictionaryError, match="cannot read"):
            load_dictionary_file(tmp_path / "missing.yaml")
        bad = tmp_path / "bad.yaml"
        bad.write_text("a: [", encoding="utf-8")
        with pytest.raises(DictionaryError, match="invalid YAML"):
            load_dictionary_file(bad)

    def test_relative_dictionary_resolved_from_config_root(self, tmp_path: Path) -> None:
        (tmp_path / "words.yaml").write_text("غلط: درست\n", encoding="utf-8")
        (tmp_path / ".paknevis.toml").write_text('dictionaries = ["words.yaml"]\n', encoding="utf-8")
        assert load_config(start=tmp_path).spelling_entries() == {"غلط": "درست"}
