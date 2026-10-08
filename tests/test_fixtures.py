"""Golden before/after fixture files in tests/fixtures (``*.in.*`` → ``*.out.*``)."""

from __future__ import annotations

from pathlib import Path

import pytest

import paknevis
from paknevis.formats import detect_syntax

FIXTURES = Path(__file__).parent / "fixtures"
PAIRS = sorted(FIXTURES.glob("*.in.*"))


def _expected(path: Path) -> Path:
    return path.with_name(path.name.replace(".in.", ".out."))


def test_fixture_pairs_exist() -> None:
    assert len(PAIRS) >= 10
    for source in PAIRS:
        assert _expected(source).exists(), f"missing expected output for {source.name}"


@pytest.mark.parametrize("source", PAIRS, ids=lambda p: p.name)
def test_fix_matches_expected(source: Path) -> None:
    text = source.read_text(encoding="utf-8")
    expected = _expected(source).read_text(encoding="utf-8")
    assert paknevis.fix(text, syntax=detect_syntax(source)) == expected


@pytest.mark.parametrize("source", PAIRS, ids=lambda p: p.name)
def test_expected_output_is_stable(source: Path) -> None:
    expected = _expected(source).read_text(encoding="utf-8")
    syntax = detect_syntax(source)
    assert paknevis.fix(expected, syntax=syntax) == expected
    assert not [d for d in paknevis.lint(expected, syntax=syntax) if d.fixable]


@pytest.mark.parametrize("source", PAIRS, ids=lambda p: p.name)
def test_diagnostic_positions_point_at_original_text(source: Path) -> None:
    text = source.read_text(encoding="utf-8")
    lines = text.split("\n")
    for d in paknevis.lint(text, syntax=detect_syntax(source)):
        assert text[d.offset : d.end_offset] == d.original
        line_start = sum(len(line) + 1 for line in lines[: d.line - 1])
        assert line_start + d.column - 1 == d.offset


def test_clean_fixture_is_untouched() -> None:
    text = (FIXTURES / "clean.in.md").read_text(encoding="utf-8")
    assert paknevis.lint(text, syntax="markdown") == []
