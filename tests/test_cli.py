"""Command line: check and fix commands (exit codes, reports, Persian messages), info commands and `python -m paknevis`."""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from paknevis.cli import EXIT_ERROR, EXIT_ISSUES, EXIT_OK, main

BAD = "سلام , دنیا ?\nكتاب هاي من\n"
GOOD = "سلام، دنیا؟\nکتاب‌های من\n"


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text(BAD, encoding="utf-8")
    (tmp_path / "docs" / "b.txt").write_text(GOOD, encoding="utf-8")
    (tmp_path / "docs" / "c.py").write_text("x = 'كتاب'\n", encoding="utf-8")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "x.md").write_text(BAD, encoding="utf-8")
    return tmp_path


def run(*args: str) -> int:
    return main(list(args))


class TestCheck:
    def test_reports_and_fails(self, project: Path, capsys: pytest.CaptureFixture[str]) -> None:
        assert run("check", "--no-color", ".") == EXIT_ISSUES
        out, err = capsys.readouterr()
        assert "docs/a.md:1:6: warning PN301 [persian-comma]" in out
        assert "node_modules" not in out
        assert "c.py" not in out
        assert "Found 4 issues in 2 files (4 fixable" in err

    def test_clean_file_passes(self, project: Path, capsys: pytest.CaptureFixture[str]) -> None:
        assert run("check", "docs/b.txt") == EXIT_OK
        assert "No issues found in 1 file." in capsys.readouterr().err

    def test_persian_messages(self, project: Path, capsys: pytest.CaptureFixture[str]) -> None:
        assert run("check", "--lang", "fa", "--no-color", "docs/a.md") == EXIT_ISSUES
        out, err = capsys.readouterr()
        assert "ویرگول فارسی" in out
        assert "مشکل در ۱" in err or "مشکل در 1" in err

    def test_json_output(self, project: Path, capsys: pytest.CaptureFixture[str]) -> None:
        assert run("check", "--format", "json", "docs/a.md") == EXIT_ISSUES
        data = json.loads(capsys.readouterr().out)
        assert {d["rule"] for d in data} == {"persian-comma", "persian-question-mark", "arabic-kaf", "arabic-yeh"}
        assert data[0]["path"] == "docs/a.md"
        assert data[0]["line"] == 1

    def test_github_output(self, project: Path, capsys: pytest.CaptureFixture[str]) -> None:
        run("check", "--format", "github", "docs/a.md")
        out = capsys.readouterr().out
        assert "::warning file=docs/a.md,line=1,col=6,endLine=1,endColumn=7,title=PN301 persian-comma::" in out
        assert "::error file=docs/a.md,line=2" in out

    def test_concise_output(self, project: Path, capsys: pytest.CaptureFixture[str]) -> None:
        run("check", "--format", "concise", "docs/a.md")
        assert "docs/a.md:1:6: PN301 [persian-comma]" in capsys.readouterr().out

    def test_statistics(self, project: Path, capsys: pytest.CaptureFixture[str]) -> None:
        run("check", "--statistics", "docs/a.md")
        out = capsys.readouterr().out
        assert "PN301  * persian-comma" in out

    def test_diff(self, project: Path, capsys: pytest.CaptureFixture[str]) -> None:
        run("check", "--diff", "--no-color", "docs/a.md")
        out = capsys.readouterr().out
        assert "--- a/docs/a.md" in out and "+سلام، دنیا؟" in out

    def test_fail_on_error_ignores_warnings(self, project: Path) -> None:
        (project / "w.txt").write_text("سلام , دنیا\n", encoding="utf-8")
        assert run("check", "--fail-on", "error", "w.txt") == EXIT_OK
        assert run("check", "--fail-on", "warning", "w.txt") == EXIT_ISSUES

    def test_disable_and_exclude(self, project: Path) -> None:
        assert (
            run("check", "--disable", "persian-comma,persian-question-mark", "--disable", "PN101,PN102", "docs/a.md")
            == EXIT_OK
        )
        assert run("check", "--exclude", "a.md", "docs") == EXIT_OK

    def test_glob(self, project: Path, capsys: pytest.CaptureFixture[str]) -> None:
        assert run("check", "--format", "concise", "docs/*.md") == EXIT_ISSUES
        assert "docs/a.md" in capsys.readouterr().out

    def test_missing_path(self, project: Path, capsys: pytest.CaptureFixture[str]) -> None:
        assert run("check", "nope.md") == EXIT_ERROR
        assert "no such file" in capsys.readouterr().err
        assert run("check", "nothing/*.md") == EXIT_ERROR

    def test_unknown_rule(self, project: Path, capsys: pytest.CaptureFixture[str]) -> None:
        assert run("check", "--disable", "nope", "docs/a.md") == EXIT_ERROR
        assert "unknown rule" in capsys.readouterr().err

    def test_bad_config(self, project: Path, capsys: pytest.CaptureFixture[str]) -> None:
        (project / ".paknevis.toml").write_text("colour = 1\n", encoding="utf-8")
        assert run("check", "docs/a.md") == EXIT_ERROR
        assert "unknown paknevis option" in capsys.readouterr().err
        assert run("check", "--isolated", "docs/b.txt") == EXIT_OK

    def test_config_file_is_used(self, project: Path) -> None:
        (project / "pyproject.toml").write_text(
            '[tool.paknevis]\ndisable = ["persian-comma", "persian-question-mark", "arabic-yeh", "arabic-kaf"]\n',
            encoding="utf-8",
        )
        assert run("check", "docs/a.md") == EXIT_OK
        assert run("check", "--config", "pyproject.toml", "docs/a.md") == EXIT_OK

    def test_include_option(self, project: Path, capsys: pytest.CaptureFixture[str]) -> None:
        (project / ".paknevis.toml").write_text('include = ["*.py"]\n', encoding="utf-8")
        run("check", "--format", "concise", "docs")
        out = capsys.readouterr().out
        assert "c.py" in out and "a.md" not in out

    def test_invalid_utf8(self, project: Path, capsys: pytest.CaptureFixture[str]) -> None:
        (project / "latin1.txt").write_bytes("caf\xe9".encode("latin-1"))
        assert run("check", "latin1.txt") == EXIT_ERROR
        assert "not valid UTF-8" in capsys.readouterr().err

    def test_colour(self, project: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
        run("check", "--color", "docs/a.md")
        assert "\033[" in capsys.readouterr().out
        monkeypatch.setenv("FORCE_COLOR", "1")
        run("check", "docs/a.md")
        assert "\033[" in capsys.readouterr().out
        monkeypatch.setenv("NO_COLOR", "1")
        run("check", "docs/a.md")
        assert "\033[" not in capsys.readouterr().out

    def test_quiet(self, project: Path, capsys: pytest.CaptureFixture[str]) -> None:
        run("check", "-q", "docs/b.txt")
        assert capsys.readouterr().err == ""


class TestFix:
    def test_fix_in_place(self, project: Path, capsys: pytest.CaptureFixture[str]) -> None:
        assert run("fix", "docs") == EXIT_OK
        assert (project / "docs" / "a.md").read_text(encoding="utf-8") == GOOD
        assert (project / "node_modules" / "x.md").read_text(encoding="utf-8") == BAD
        assert "Fixed 1 of 2 files." in capsys.readouterr().err
        assert run("check", "docs") == EXIT_OK

    def test_check_mode(self, project: Path, capsys: pytest.CaptureFixture[str]) -> None:
        assert run("fix", "--check", "docs") == EXIT_ISSUES
        assert (project / "docs" / "a.md").read_text(encoding="utf-8") == BAD
        err = capsys.readouterr().err
        assert "would fix docs/a.md" in err.replace(os.sep, "/")
        assert run("fix", "--check", "docs/b.txt") == EXIT_OK

    def test_diff_mode(self, project: Path, capsys: pytest.CaptureFixture[str]) -> None:
        assert run("fix", "--diff", "docs/a.md") == EXIT_ISSUES
        assert "+کتاب‌های من" in capsys.readouterr().out
        assert (project / "docs" / "a.md").read_text(encoding="utf-8") == BAD

    def test_preserves_crlf_and_bom(self, project: Path) -> None:
        path = project / "win.txt"
        path.write_bytes("\ufeffسلام , دنیا\r\nخط دوم  \r\n".encode())
        assert run("fix", "win.txt") == EXIT_OK
        assert path.read_bytes() == "\ufeffسلام، دنیا\r\nخط دوم\r\n".encode()

    def test_stdin_stdout(
        self, project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(BAD.encode()), encoding="utf-8"))
        assert run("fix", "-") == EXIT_OK
        assert capsys.readouterr().out == GOOD

    def test_stdin_check(
        self, project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(BAD.encode()), encoding="utf-8"))
        assert run("check", "--format", "concise", "--syntax", "md", "-") == EXIT_ISSUES
        assert "<stdin>:1:6" in capsys.readouterr().out

    def test_stdin_diff(
        self, project: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(BAD.encode()), encoding="utf-8"))
        assert run("fix", "--diff", "-") == EXIT_ISSUES
        assert "+++ <stdin>" in capsys.readouterr().out

    def test_options(self, project: Path) -> None:
        path = project / "d.txt"
        path.write_text("سال ۱۴۰۲ و نامه ی من و رحمة\n", encoding="utf-8")
        assert run("fix", "--digits", "latin", "--ezafe", "hamza", "--teh-marbuta", "teh", "d.txt") == EXIT_OK
        assert path.read_text(encoding="utf-8") == "سال 1402 و نامهٔ من و رحمت\n"

    def test_forced_syntax(self, project: Path) -> None:
        path = project / "notes.txt"
        path.write_text("`كد` و كتاب\n", encoding="utf-8")
        run("fix", "--syntax", "markdown", "notes.txt")
        assert path.read_text(encoding="utf-8") == "`كد` و کتاب\n"

    def test_fa_summary(self, project: Path, capsys: pytest.CaptureFixture[str]) -> None:
        run("fix", "--lang", "fa", "docs")
        assert "پرونده" in capsys.readouterr().err


class TestInfoCommands:
    def test_rules_text(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert run("rules", "--no-color") == EXIT_OK
        out = capsys.readouterr().out
        assert "PN101  arabic-yeh" in out
        assert out.index("PN101") < out.index("PN201") < out.index("PN501")

    def test_rules_json_and_markdown(self, capsys: pytest.CaptureFixture[str]) -> None:
        run("rules", "--format", "json")
        data = json.loads(capsys.readouterr().out)
        assert data[0]["code"] == "PN101" and data[0]["title_fa"]
        run("rules", "--format", "markdown", "--lang", "fa")
        assert "| PN203 | `zwnj-plural` |" in capsys.readouterr().out

    def test_explain(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert run("explain", "--no-color", "PN203") == EXIT_OK
        out = capsys.readouterr().out
        assert "zwnj-plural" in out and "نیم‌فاصله" in out and "⟨ZWNJ⟩" in out
        assert run("explain", "arabic-teh-marbuta") == EXIT_OK
        assert "Options: teh-marbuta" in capsys.readouterr().out

    def test_explain_unknown(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert run("explain", "nope") == EXIT_ERROR
        assert "unknown rule" in capsys.readouterr().err

    def test_no_command(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert run() == EXIT_ERROR
        assert "usage" in capsys.readouterr().out

    def test_version(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit):
            run("--version")
        assert "paknevis 0." in capsys.readouterr().out

    def test_no_paths_with_tty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        class FakeTTY(io.StringIO):
            def isatty(self) -> bool:
                return True

        monkeypatch.setattr(sys, "stdin", FakeTTY())
        with pytest.raises(SystemExit) as excinfo:
            run("check")
        assert excinfo.value.code == 2


def test_python_dash_m(tmp_path: Path) -> None:
    path = tmp_path / "x.txt"
    path.write_text("علي\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "paknevis", "check", "--format", "json", str(path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert result.returncode == EXIT_ISSUES
    assert json.loads(result.stdout)[0]["rule"] == "arabic-yeh"
