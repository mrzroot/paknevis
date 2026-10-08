from __future__ import annotations

from pathlib import Path

import pytest

docx = pytest.importorskip("docx")

from paknevis import Linter  # noqa: E402
from paknevis.cli import EXIT_ISSUES, EXIT_OK, main  # noqa: E402
from paknevis.docx import fix_docx, lint_docx  # noqa: E402


def _make(path: Path) -> None:
    document = docx.Document()
    paragraph = document.add_paragraph()
    paragraph.add_run("سلام , ")
    bold = paragraph.add_run("كتاب")
    bold.bold = True
    paragraph.add_run(" هاي من ?")
    document.add_paragraph("")
    table = document.add_table(rows=1, cols=1)
    table.cell(0, 0).text = "علي"
    document.sections[0].header.is_linked_to_previous = False
    document.sections[0].header.paragraphs[0].text = "سرصفحه ی سند"
    document.save(str(path))


def test_lint_docx(tmp_path: Path) -> None:
    path = tmp_path / "thesis.docx"
    _make(path)
    diagnostics = lint_docx(path, Linter())
    rules = {d.rule for d in diagnostics}
    assert {"persian-comma", "arabic-kaf", "arabic-yeh", "zwnj-heh-suffix"} <= rules
    assert diagnostics[0].line == 1


def test_fix_docx_preserves_formatting(tmp_path: Path) -> None:
    path = tmp_path / "thesis.docx"
    _make(path)
    assert fix_docx(path, Linter()) >= 3
    document = docx.Document(str(path))
    paragraph = document.paragraphs[0]
    assert paragraph.text == "سلام، کتاب‌های من؟"
    bold_runs = [run.text for run in paragraph.runs if run.bold]
    assert bold_runs and "کتاب" in bold_runs[0]
    assert document.tables[0].cell(0, 0).text == "علی"
    assert document.sections[0].header.paragraphs[0].text == "سرصفحه‌ی سند"
    assert fix_docx(path, Linter()) == 0


def test_cli_docx(tmp_path: Path) -> None:
    path = tmp_path / "thesis.docx"
    _make(path)
    assert main(["check", "-q", str(path)]) == EXIT_ISSUES
    assert main(["fix", "--check", str(path)]) == EXIT_ISSUES
    assert main(["fix", str(path)]) == EXIT_OK
    assert main(["fix", "--check", str(path)]) == EXIT_OK


class _Run:
    def __init__(self, text: str) -> None:
        self.text = text


@pytest.mark.parametrize(
    ("texts", "start", "end", "replacement", "expected"),
    [
        (["ab", "cd", "ef"], 1, 5, "X", ["aX", "", "f"]),
        (["ab", "cd"], 2, 2, "+", ["ab+", "cd"]),
        (["ab", "cd"], 2, 3, "C", ["ab", "Cd"]),
        (["ab", "cd"], 1, 2, "B", ["aB", "cd"]),
        (["", "ab"], 0, 1, "A", ["", "Ab"]),
        (["ab"], 2, 2, "!", ["ab!"]),
    ],
)
def test_replace_range(texts: list[str], start: int, end: int, replacement: str, expected: list[str]) -> None:
    from paknevis.docx import _replace_range

    runs = [_Run(t) for t in texts]
    _replace_range(runs, start, end, replacement)
    assert [r.text for r in runs] == expected


def test_fix_runs_keeps_bold_word() -> None:
    from paknevis.docx import fix_runs

    runs = [_Run("سلام , "), _Run("كتاب"), _Run(" هاي من ?")]
    assert fix_runs(runs, Linter())
    assert [r.text for r in runs] == ["سلام، ", "کتاب", "‌های من؟"]
