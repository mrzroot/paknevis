"""Command-line interface: ``paknevis check|fix|rules|explain``."""

from __future__ import annotations

import argparse
import contextlib
import difflib
import fnmatch
import glob
import json
import os
import sys
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import TextIO

from . import __version__
from .config import DEFAULT_EXCLUDE, Config, ConfigError, load_config
from .dictionary import DictionaryError
from .engine import Linter
from .formats import EXTENSIONS, detect_syntax, normalize_syntax
from .models import Diagnostic, Severity
from .rules import ALL_RULES, get_rule

__all__ = ["main"]

EXIT_OK = 0
EXIT_ISSUES = 1
EXIT_ERROR = 2

_BOM = "\ufeff"
_GITHUB_LEVEL = {Severity.ERROR: "error", Severity.WARNING: "warning", Severity.INFO: "notice"}


# --------------------------------------------------------------------------- #
# Output helpers
# --------------------------------------------------------------------------- #
@dataclass
class Style:
    """ANSI styling that degrades to plain text."""

    enabled: bool

    def __call__(self, text: str, code: str) -> str:
        return f"\033[{code}m{text}\033[0m" if self.enabled else text

    def severity(self, severity: Severity) -> str:
        colour = {Severity.ERROR: "31;1", Severity.WARNING: "33;1", Severity.INFO: "36"}[severity]
        return self(severity.value, colour)


def _use_colour(stream: TextIO, flag: bool | None) -> bool:
    if flag is not None:
        return flag
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return hasattr(stream, "isatty") and stream.isatty()


def _configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            with contextlib.suppress(ValueError, OSError):
                reconfigure(encoding="utf-8")


# --------------------------------------------------------------------------- #
# File discovery
# --------------------------------------------------------------------------- #
@dataclass
class Discovery:
    """Resolve CLI path arguments into concrete files."""

    config: Config
    explicit_syntax: str | None = None
    errors: list[str] = field(default_factory=list)

    def _excluded(self, path: Path, root: Path) -> bool:
        try:
            relative = path.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            relative = path.as_posix()
        parts = relative.split("/")
        patterns = (*(self.config.exclude or DEFAULT_EXCLUDE), *self.config.extend_exclude)
        for pattern in patterns:
            pattern = pattern.rstrip("/")
            if fnmatch.fnmatch(relative, pattern) or any(fnmatch.fnmatch(part, pattern) for part in parts):
                return True
        return False

    def _included(self, path: Path, root: Path) -> bool:
        if self.config.include:
            relative = path.relative_to(root).as_posix()
            return any(fnmatch.fnmatch(relative, p) or fnmatch.fnmatch(path.name, p) for p in self.config.include)
        return path.suffix.lower() in EXTENSIONS

    def files(self, arguments: Sequence[str]) -> Iterator[str]:
        seen: set[str] = set()
        for argument in arguments:
            for path in self._expand(argument):
                key = path if path == "-" else str(Path(path).resolve())
                if key not in seen:
                    seen.add(key)
                    yield path

    def _expand(self, argument: str) -> Iterator[str]:
        if argument == "-":
            yield "-"
            return
        path = Path(argument)
        if path.is_file():
            yield argument
            return
        if path.is_dir():
            for candidate in sorted(self._walk(path)):
                yield candidate.as_posix()
            return
        if any(char in argument for char in "*?["):
            matches = sorted(glob.glob(argument, recursive=True))
            files = [Path(m).as_posix() for m in matches if Path(m).is_file()]
            root = Path.cwd()
            files = [m for m in files if not self._excluded(Path(m), root)]
            if not files:
                self.errors.append(f"{argument}: no files match")
            yield from files
            return
        self.errors.append(f"{argument}: no such file or directory")

    def _walk(self, root: Path) -> Iterator[Path]:
        for directory, subdirs, filenames in os.walk(root):
            current = Path(directory)
            subdirs[:] = sorted(d for d in subdirs if not self._excluded(current / d, root))
            for name in filenames:
                candidate = current / name
                if self._included(candidate, root) and not self._excluded(candidate, root):
                    yield candidate


# --------------------------------------------------------------------------- #
# Reading / writing
# --------------------------------------------------------------------------- #
def _read(path: str) -> tuple[str, bool]:
    """Return ``(text, had_bom)``; ``-`` reads stdin."""
    if path == "-":
        data = sys.stdin.buffer.read() if hasattr(sys.stdin, "buffer") else sys.stdin.read().encode()
        text = data.decode("utf-8")
    else:
        with open(path, encoding="utf-8", newline="") as handle:
            text = handle.read()
    if text.startswith(_BOM):
        return text[1:], True
    return text, False


def _write(path: str, text: str, bom: bool) -> None:
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write((_BOM if bom else "") + text)


def _syntax_for(path: str, explicit: str | None) -> str:
    if explicit:
        return explicit
    return "plain" if path == "-" else detect_syntax(path)


def _display(path: str) -> str:
    return "<stdin>" if path == "-" else path


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #
def _build_config(args: argparse.Namespace) -> Config:
    if args.config:
        config = load_config(Path(args.config))
    elif args.isolated:
        config = Config(root=Path.cwd())
    else:
        start = Path(args.paths[0]) if getattr(args, "paths", None) and args.paths[0] != "-" else Path.cwd()
        config = load_config(start=start if start.exists() else Path.cwd())
    overrides: dict[str, object] = {}
    if args.disable:
        overrides["disable"] = config.disable | frozenset(_split(args.disable))
    if args.enable:
        overrides["enable"] = config.enable | frozenset(_split(args.enable))
    if args.exclude:
        overrides["extend_exclude"] = (*config.extend_exclude, *_split(args.exclude))
    overrides["digits"] = args.digits
    overrides["ezafe"] = args.ezafe
    overrides["teh_marbuta"] = args.teh_marbuta
    if getattr(args, "fail_on", None):
        overrides["fail_on"] = args.fail_on
    config = config.merged(**overrides)
    for key in (*config.disable, *config.enable, *(name for name, _ in config.severity)):
        get_rule(key)  # validate early: raises KeyError for unknown rules
    return config


def _split(values: Iterable[str]) -> list[str]:
    return [part.strip() for value in values for part in value.split(",") if part.strip()]


def _lint_file(linter: Linter, path: str, syntax: str) -> list[Diagnostic]:
    if path.lower().endswith(".docx"):
        from .docx import lint_docx

        return lint_docx(Path(path), linter)
    text, _ = _read(path)
    return linter.lint(text, syntax=syntax, path=_display(path))


def _print_diagnostics(diagnostics: list[Diagnostic], args: argparse.Namespace, style: Style) -> None:
    out = sys.stdout
    if args.output_format == "json":
        json.dump([d.to_dict() for d in diagnostics], out, ensure_ascii=False, indent=2)
        out.write("\n")
        return
    if args.output_format == "github":
        for d in diagnostics:
            message = (d.message_fa if args.lang == "fa" else d.message).replace("%", "%25").replace("\n", "%0A")
            out.write(
                f"::{_GITHUB_LEVEL[d.severity]} file={d.path},line={d.line},col={d.column},"
                f"endLine={d.end_line},endColumn={d.end_column},title={d.code} {d.rule}::{message}\n"
            )
        return
    if args.output_format == "concise":
        for d in diagnostics:
            out.write(d.format(lang=args.lang) + "\n")
        return
    for d in diagnostics:
        location = style(f"{d.path}:{d.line}:{d.column}", "1")
        message = d.message_fa if args.lang == "fa" else d.message
        fix = ""
        if d.fixable and args.show_fixes:
            fix = style(f"  «{_visible(d.original)}» → «{_visible(d.replacement or '')}»", "2")
        out.write(f"{location}: {style.severity(d.severity)} {style(d.code, '35')} [{d.rule}] {message}{fix}\n")


def _visible(text: str) -> str:
    return text.replace("\u200c", "⟨ZWNJ⟩").replace("\t", "⟨TAB⟩").replace("\n", "⏎")


def _summary(diagnostics: list[Diagnostic], files: int, lang: str) -> str:
    fixable = sum(d.fixable for d in diagnostics)
    if lang == "fa":
        if not diagnostics:
            return f"✓ هیچ مشکلی در {files} پرونده پیدا نشد."
        return f"{len(diagnostics)} مشکل در {files} پرونده پیدا شد ({fixable} مورد با `paknevis fix` اصلاح‌پذیر است)."
    if not diagnostics:
        return f"✓ No issues found in {files} file{'s' if files != 1 else ''}."
    return (
        f"Found {len(diagnostics)} issue{'s' if len(diagnostics) != 1 else ''} in {files} "
        f"file{'s' if files != 1 else ''} ({fixable} fixable with `paknevis fix`)."
    )


def cmd_check(args: argparse.Namespace) -> int:
    config = _build_config(args)
    linter = Linter(config)
    discovery = Discovery(config)
    style = Style(_use_colour(sys.stdout, args.color))
    all_diagnostics: list[Diagnostic] = []
    count = 0
    errors = 0
    diffs: list[str] = []
    for path in discovery.files(args.paths):
        count += 1
        try:
            syntax = _syntax_for(path, args.syntax)
            diagnostics = _lint_file(linter, path, syntax)
            if args.diff and not path.lower().endswith(".docx"):
                text, _ = _read(path) if path != "-" else ("", False)
                diffs.append(_diff(text, linter.fix(text, syntax=syntax), _display(path)))
        except (UnicodeDecodeError, OSError) as exc:
            _error(f"{_display(path)}: {_describe(exc)}")
            errors += 1
            continue
        all_diagnostics.extend(diagnostics)
    for message in discovery.errors:
        _error(message)
        errors += 1
    if args.statistics and args.output_format == "text":
        _print_statistics(all_diagnostics)
    else:
        _print_diagnostics(all_diagnostics, args, style)
    if args.diff:
        sys.stdout.write("".join(diffs))
    if args.output_format == "text" and not args.quiet:
        sys.stderr.write(_summary(all_diagnostics, count, args.lang) + "\n")
    if errors:
        return EXIT_ERROR
    threshold = config.fail_on.rank
    return EXIT_ISSUES if any(d.severity.rank >= threshold for d in all_diagnostics) else EXIT_OK


def _print_statistics(diagnostics: list[Diagnostic]) -> None:
    counts: dict[tuple[str, str], int] = {}
    fixable: dict[tuple[str, str], bool] = {}
    for d in diagnostics:
        key = (d.code, d.rule)
        counts[key] = counts.get(key, 0) + 1
        fixable[key] = fixable.get(key, False) or d.fixable
    for (code, rule), number in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        marker = "*" if fixable[(code, rule)] else " "
        sys.stdout.write(f"{number:>6}  {code}  {marker} {rule}\n")


def _diff(before: str, after: str, name: str) -> str:
    if before == after:
        return ""
    lines = difflib.unified_diff(
        before.splitlines(keepends=True),
        after.splitlines(keepends=True),
        fromfile=name if name.startswith(("/", "<")) else f"a/{name}",
        tofile=name if name.startswith(("/", "<")) else f"b/{name}",
    )
    return "".join(line if line.endswith("\n") else line + "\n\\ No newline at end of file\n" for line in lines)


def cmd_fix(args: argparse.Namespace) -> int:
    config = _build_config(args)
    linter = Linter(config)
    discovery = Discovery(config)
    changed = 0
    count = 0
    errors = 0
    write = not (args.check or args.diff)
    for path in discovery.files(args.paths):
        count += 1
        try:
            if path.lower().endswith(".docx"):
                from .docx import fix_docx, lint_docx

                if write:
                    if fix_docx(Path(path), linter):
                        changed += 1
                        _info(args, f"fixed {path}")
                elif any(d.fixable for d in lint_docx(Path(path), linter)):
                    changed += 1
                    _info(args, f"would fix {path}")
                continue
            syntax = _syntax_for(path, args.syntax)
            text, bom = _read(path)
            fixed = linter.fix(text, syntax=syntax)
        except (UnicodeDecodeError, OSError) as exc:
            _error(f"{_display(path)}: {_describe(exc)}")
            errors += 1
            continue
        if path == "-":
            if args.diff:
                sys.stdout.write(_diff(text, fixed, "<stdin>"))
            elif not args.check:
                sys.stdout.write(fixed)
            changed += fixed != text
            continue
        if fixed == text:
            continue
        changed += 1
        if args.diff:
            sys.stdout.write(_diff(text, fixed, path))
        if write:
            _write(path, fixed, bom)
            _info(args, f"fixed {path}")
        elif args.check:
            _info(args, f"would fix {path}")
    for message in discovery.errors:
        _error(message)
        errors += 1
    if not args.quiet and not (args.paths == ["-"] and write):
        plural = "s" if count != 1 else ""
        if args.lang == "fa":
            verb_fa = "اصلاح شد" if write else "نیاز به اصلاح دارد"
            sys.stderr.write(f"{changed} پرونده از {count} پرونده {verb_fa}.\n")
        elif write:
            sys.stderr.write(f"Fixed {changed} of {count} file{plural}.\n")
        else:
            sys.stderr.write(f"{changed} of {count} file{plural} would be changed.\n")
    if errors:
        return EXIT_ERROR
    return EXIT_ISSUES if (changed and not write) else EXIT_OK


def cmd_rules(args: argparse.Namespace) -> int:
    if args.output_format == "json":
        from .web import rules_json

        sys.stdout.write(rules_json() + "\n")
        return EXIT_OK
    if args.output_format == "markdown":
        sys.stdout.write("| Code | Rule | Category | Severity | Fix | Description |\n")
        sys.stdout.write("|---|---|---|---|:-:|---|\n")
        for rule in sorted(ALL_RULES, key=lambda r: r.code):
            title = rule.title_fa if args.lang == "fa" else rule.title_en
            sys.stdout.write(
                f"| {rule.code} | `{rule.name}` | {rule.category} | {rule.severity.value} | "
                f"{'✅' if rule.fixable else '—'} | {title} |\n"
            )
        return EXIT_OK
    style = Style(_use_colour(sys.stdout, args.color))
    for rule in sorted(ALL_RULES, key=lambda r: r.code):
        title = rule.title_fa if args.lang == "fa" else rule.title_en
        fix = "fix" if rule.fixable else "   "
        sys.stdout.write(f"{style(rule.code, '35')}  {rule.name:<26} {rule.severity.value:<8} {fix}  {title}\n")
    return EXIT_OK


def cmd_explain(args: argparse.Namespace) -> int:
    try:
        rule = get_rule(args.rule)
    except KeyError as exc:
        _error(str(exc.args[0]))
        return EXIT_ERROR
    style = Style(_use_colour(sys.stdout, args.color))
    out = sys.stdout
    out.write(f"{style(rule.code, '35;1')}  {style(rule.name, '1')}  ({rule.category}, {rule.severity.value}")
    out.write(", auto-fixable)\n\n" if rule.fixable else ")\n\n")
    out.write(f"{rule.title_en}\n{rule.description_en}\n\n")
    out.write(f"{rule.title_fa}\n{rule.description_fa}\n")
    if rule.examples:
        out.write("\nExamples / نمونه‌ها:\n")
        for example in rule.examples:
            out.write(f"  {_visible(example.before)}  →  {_visible(example.after)}\n")
    if rule.options:
        out.write(f"\nOptions: {', '.join(rule.options)}\n")
    return EXIT_OK


def _info(args: argparse.Namespace, message: str) -> None:
    if not args.quiet:
        sys.stderr.write(message + "\n")


def _error(message: str) -> None:
    sys.stderr.write(f"paknevis: error: {message}\n")


def _describe(exc: BaseException) -> str:
    if isinstance(exc, UnicodeDecodeError):
        return "not valid UTF-8 text"
    if isinstance(exc, OSError):
        return exc.strerror or str(exc)
    return str(exc)  # pragma: no cover


# --------------------------------------------------------------------------- #
# Argument parsing
# --------------------------------------------------------------------------- #
def _syntax_arg(value: str) -> str:
    try:
        return normalize_syntax(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from None


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="paknevis",
        description="پاک‌نویس — lint and fix Persian text in plain text, Markdown, HTML, LaTeX and .docx files.",
        epilog="Docs & playground: https://mrzroot.github.io/paknevis/",
    )
    parser.add_argument("-V", "--version", action="version", version=f"paknevis {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--lang", choices=("en", "fa"), default="en", help="language of messages (default: en)")
    colour = common.add_mutually_exclusive_group()
    colour.add_argument("--color", dest="color", action="store_true", default=None, help="force coloured output")
    colour.add_argument("--no-color", dest="color", action="store_false", help="disable coloured output")
    common.add_argument("-q", "--quiet", action="store_true", help="only print diagnostics / diffs")

    files = argparse.ArgumentParser(add_help=False)
    files.add_argument("paths", nargs="*", help="files, directories or globs ('-' for stdin)")
    files.add_argument("--syntax", type=_syntax_arg, help="force syntax: plain, markdown, html or latex")
    files.add_argument("--config", metavar="FILE", help="path to pyproject.toml or .paknevis.toml")
    files.add_argument("--isolated", action="store_true", help="ignore configuration files")
    files.add_argument("--disable", action="append", metavar="RULES", help="comma-separated rules to disable")
    files.add_argument("--enable", action="append", metavar="RULES", help="comma-separated rules to enable")
    files.add_argument("--exclude", action="append", metavar="GLOB", help="extra paths/globs to exclude")
    files.add_argument("--digits", choices=("persian", "latin", "keep"), help="digit style outside code")
    files.add_argument("--ezafe", choices=("zwnj", "hamza"), help="how to write the ezafe after silent «ه»")
    files.add_argument("--teh-marbuta", choices=("warn", "heh", "teh"), help="how to handle «ة»")

    check = sub.add_parser("check", parents=[files, common], help="report problems (does not modify files)")
    check.add_argument(
        "--format",
        dest="output_format",
        choices=("text", "concise", "json", "github"),
        default="text",
        help="output format (github = workflow annotations)",
    )
    check.add_argument("--diff", action="store_true", help="also print the diff that `fix` would apply")
    check.add_argument("--statistics", action="store_true", help="print counts per rule instead of each issue")
    check.add_argument(
        "--fail-on", choices=("info", "warning", "error"), help="minimum severity that fails (default: warning)"
    )
    check.add_argument("--no-show-fixes", dest="show_fixes", action="store_false", help="hide suggested replacements")
    check.set_defaults(func=cmd_check)

    fix = sub.add_parser("fix", parents=[files, common], help="fix problems in place")
    fix.add_argument("--check", action="store_true", help="don't write; exit 1 if any file would change")
    fix.add_argument("--diff", action="store_true", help="don't write; print a unified diff instead")
    fix.set_defaults(func=cmd_fix)

    rules = sub.add_parser("rules", parents=[common], help="list all rules")
    rules.add_argument("--format", dest="output_format", choices=("text", "json", "markdown"), default="text")
    rules.set_defaults(func=cmd_rules)

    explain = sub.add_parser("explain", parents=[common], help="explain a rule in English and Persian")
    explain.add_argument("rule", help="rule name or code, e.g. zwnj-plural or PN203")
    explain.set_defaults(func=cmd_explain)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the ``paknevis`` command. Returns the exit code."""
    _configure_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return EXIT_ERROR
    if hasattr(args, "paths") and not args.paths:
        if sys.stdin is not None and not sys.stdin.isatty():
            args.paths = ["-"]
        else:
            parser.error(f"{args.command}: no paths given (use '.' for the current directory or '-' for stdin)")
    try:
        result: int = args.func(args)
    except (ConfigError, DictionaryError) as exc:
        _error(str(exc))
        return EXIT_ERROR
    except KeyError as exc:
        _error(str(exc.args[0]))
        return EXIT_ERROR
    except ImportError as exc:  # pragma: no cover - optional dependency missing
        _error(str(exc))
        return EXIT_ERROR
    except RuntimeError as exc:
        _error(str(exc))
        return EXIT_ERROR
    return result
