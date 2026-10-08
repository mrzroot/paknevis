# Contributing to paknevis · مشارکت در پاک‌نویس

Thanks for helping make Persian text on the web cleaner! Bug reports, false
positives, dictionary words and new rules are all welcome. Persian or English —
both are fine in issues and pull requests.

## Development setup

```bash
git clone https://github.com/mrzroot/paknevis && cd paknevis
uv sync --group dev            # or: python -m venv .venv && pip install -e . pytest hypothesis ruff mypy python-docx
uv run pytest                  # full test suite (with doctests and property tests)
uv run ruff check . && uv run ruff format --check .
uv run mypy                    # strict typing
```

Useful scripts:

| Script | Purpose |
|---|---|
| `python scripts/gen_fixture_outputs.py` | Regenerate `tests/fixtures/*.out.*` from `*.in.*` — **review the diff** before committing |
| `python scripts/build_playground.py` | Rebuild `docs/assets/py/paknevis.zip` (CI fails if it is stale) |
| `python scripts/e2e_playground.py` | Headless-browser test of the playground (`pip install playwright && playwright install chromium`) |

## How the engine works

1. A **syntax handler** (`src/paknevis/formats/`) computes *protected spans* —
   code, URLs, markup, math, LaTeX commands…
2. The remaining **prose chunks** are passed to every enabled **rule**
   (`src/paknevis/rules/`). A rule yields `Finding(start, end, replacement)`
   objects relative to the chunk; `replacement=None` means “report only”.
3. `lint()` turns findings into `Diagnostic`s with absolute line/column
   positions. `fix()` applies rules one after another to each chunk and
   repeats until nothing changes, which guarantees idempotency.

## Adding a rule (step by step)

1. **Pick a code and name.** Codes are grouped by category: `PN1xx`
   characters, `PN2xx` ZWNJ, `PN3xx` punctuation, `PN4xx` whitespace, `PN5xx`
   spelling. Names are kebab-case, e.g. `zwnj-bi-prefix`.
2. **Implement it** in the matching module. Most rules subclass `RegexRule`:

   ```python
   class ZwnjBiPrefix(RegexRule):
       code = "PN206"
       name = "zwnj-bi-prefix"
       category = "zwnj"
       severity = Severity.WARNING
       title_en = "ZWNJ after «بی»"
       title_fa = "نیم‌فاصله پس از «بی»"
       description_en = "…why, when it applies, and what it deliberately skips…"
       description_fa = "…"
       message_en = "Attach «بی» with a ZWNJ"
       message_fa = "«بی» را با نیم‌فاصله بچسبانید"
       examples = (Example("بی کار", "بی‌کار"),)
       pattern = re.compile(...)

       def replace(self, match, text, ctx):
           if <false positive>:
               return None              # skip this match
           return "replacement"         # or Finding(..., replacement=None) to only report
   ```

   Rules only see prose (protected regions are already removed), but they
   must still be **conservative**: act only in Persian context and prefer
   skipping an uncertain case over a wrong fix. Use helpers from
   `rules/base.py` (`prev_nonspace`, `word_before`, `one_of`, …).
3. **Register it** in `ALL_RULES` in `src/paknevis/rules/__init__.py`. Order
   matters only for `fix()` convergence; put it next to related rules.
4. **Test it.** Add positive and negative parametrised cases to the matching
   `tests/test_rules_*.py`, and, if useful, a line to a fixture in
   `tests/fixtures/`. `tests/test_rule_metadata.py` automatically checks
   metadata and that every `Example` round-trips through `fix()`.
5. **Document it**: add a row to the rule table in `README.md` and an entry
   under *Unreleased* in `CHANGELOG.md`.
6. Run `python scripts/build_playground.py` so the playground ships the new
   rule, then `uv run pytest`, `ruff` and `mypy`.

The property tests (`tests/test_properties.py`) will catch rules that are
not idempotent or that fight with other rules.

## Adding dictionary words

Edit `src/paknevis/data/spelling.yaml` (or `tanvin.yaml`). Only add
**unambiguous** corrections: if the “wrong” form is a valid word in some
context, it does not belong in the built-in list (users can still add it to
their own dictionary via the `dictionaries` option). Please mention a source
(e.g. *دستور خط فارسی*, فرهنگستان زبان و ادب فارسی) in the PR.

## Reporting false positives

Open an issue with the *false positive* template and paste the exact sentence,
the syntax (Markdown/LaTeX/…) and `paknevis --version`. A failing test case in
the PR is the fastest way to get it fixed.

## Pull requests

- Keep PRs focused; include tests.
- Make sure `pytest`, `ruff check`, `ruff format --check` and `mypy` pass.
- Use clear commit messages (e.g. `rules: add zwnj-bi-prefix`).

By contributing you agree that your contributions are licensed under the MIT
license.
