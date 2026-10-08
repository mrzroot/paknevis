# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-10-08

First public release.

### Added

- 25 rules in five categories, each with an id, severity, bilingual (FA/EN) explanation, examples and an autofix where safe:
  - **characters**: `arabic-yeh`, `arabic-kaf`, `non-persian-heh`, `arabic-teh-marbuta` (report-only by default), `arabic-digits`, `digit-style` (Persian/Latin/keep).
  - **zwnj**: `zwnj-cleanup`, `zwnj-mi-prefix`, `zwnj-plural`, `zwnj-comparative`, `zwnj-heh-suffix` (with `ezafe = "zwnj" | "hamza"`).
  - **punctuation**: `persian-comma`, `persian-semicolon`, `persian-question-mark`, `space-before-punctuation`, `space-after-punctuation`, `bracket-spacing`, `persian-quotes`, `ellipsis`, `repeated-punctuation`.
  - **whitespace**: `multiple-spaces`, `trailing-whitespace` (keeps Markdown hard breaks), `kashida`.
  - **spelling**: `spelling` (curated YAML dictionary, extensible via config) and `tanvin`.
- Syntax-aware protection for plain text, Markdown, HTML and LaTeX (XePersian `\lr{…}`, `latin`/`LTR` environments, math, verbatim, commands and their arguments).
- Inline directives: `paknevis-disable` / `paknevis-enable`, `paknevis-disable-line`, `paknevis-disable-next-line`.
- Optional `.docx` support (`paknevis[docx]`) that preserves run formatting.
- Python API: `paknevis.fix()`, `paknevis.lint()`, `Linter`, `Config`, `load_config()`.
- CLI: `paknevis check|fix|rules|explain` with `--check`, `--diff`, JSON/GitHub/concise output, `--fail-on`, Persian messages (`--lang fa`), stdin support, glob/directory discovery and configuration via `pyproject.toml` or `.paknevis.toml`.
- pre-commit hooks (`paknevis`, `paknevis-check`) and a composite GitHub Action.
- Browser playground on GitHub Pages running the real package via Pyodide (RTL-first, dark/light, Persian/English UI, self-hosted Vazirmatn).
- Test suite with golden before/after fixtures and Hypothesis property tests (idempotency, protected regions).

[Unreleased]: https://github.com/mrzroot/paknevis/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/mrzroot/paknevis/releases/tag/v0.1.0
