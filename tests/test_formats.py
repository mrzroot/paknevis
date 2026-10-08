"""Protected regions per syntax: nothing inside them may ever change."""

from __future__ import annotations

import itertools

import pytest

import paknevis
from paknevis.formats import detect_syntax, normalize_syntax, protected_spans
from paknevis.formats.common import gaps, merge_spans

BAD = "كتاب , ?"  # would be changed if it were prose


def _assert_kept(text: str, syntax: str, *fragments: str) -> str:
    fixed = paknevis.fix(text, syntax=syntax)
    for fragment in fragments:
        assert fragment in fixed, f"{fragment!r} was modified in {fixed!r}"
    return fixed


class TestPlain:
    def test_urls_and_emails(self) -> None:
        text = "سایت https://example.com/كتاب?a=1,2 و ایمیل ali.reza@example.co.ir را ببین , لطفا"
        fixed = _assert_kept(text, "plain", "https://example.com/كتاب?a=1,2", "ali.reza@example.co.ir")
        assert fixed.endswith("ببین، لطفاً")

    def test_url_trailing_punctuation_is_prose(self) -> None:
        fixed = paknevis.fix("ببینید (https://example.com/a_(b)) .")
        assert "https://example.com/a_(b)" in fixed

    def test_www_url(self) -> None:
        _assert_kept("به www.example.com/كتاب بروید", "plain", "www.example.com/كتاب")

    def test_inline_backticks(self) -> None:
        _assert_kept(f"دستور `{BAD}` را بزن", "plain", f"`{BAD}`")


class TestMarkdown:
    def test_front_matter(self) -> None:
        text = f"---\ntitle: {BAD}\n---\nمتن , اصلی"
        fixed = _assert_kept(text, "markdown", f"title: {BAD}")
        assert fixed.endswith("متن، اصلی")

    def test_toml_front_matter(self) -> None:
        _assert_kept(f'+++\ntitle = "{BAD}"\n+++\nمتن', "markdown", BAD)

    @pytest.mark.parametrize("fence", ["```", "~~~", "````"])
    def test_fenced_code(self, fence: str) -> None:
        _assert_kept(f"متن\n{fence}python\n{BAD}\n{fence}\nمتن", "markdown", BAD)

    def test_unclosed_fence_protects_rest(self) -> None:
        _assert_kept(f"متن\n```\n{BAD}\n{BAD}", "markdown", f"{BAD}\n{BAD}")

    def test_nested_fence_lengths(self) -> None:
        text = f"````md\n```\n{BAD}\n```\n````\nسلام , دنیا"
        fixed = _assert_kept(text, "markdown", BAD)
        assert fixed.endswith("سلام، دنیا")

    def test_inline_code_spans(self) -> None:
        _assert_kept(f"متغیر `{BAD}` و ``a ` {BAD}`` را ببین", "markdown", f"`{BAD}`", f"``a ` {BAD}``")

    def test_indented_code(self) -> None:
        _assert_kept(f"پاراگراف\n\n    {BAD}\n    {BAD}\n\nمتن", "markdown", f"    {BAD}\n    {BAD}")

    def test_indented_list_content_is_prose(self) -> None:
        text = "- مورد اول\n\n    ادامه , مورد"
        assert paknevis.fix(text, syntax="markdown").endswith("ادامه، مورد")

    def test_links_and_images(self) -> None:
        text = '[متن , پیوند](https://x.org/كتاب "عنوان , ها") و ![تصویر](img/كتاب.png)'
        fixed = _assert_kept(text, "markdown", '(https://x.org/كتاب "عنوان , ها")', "(img/كتاب.png)")
        assert fixed.startswith("[متن، پیوند]")

    def test_reference_links(self) -> None:
        text = '[متن][كتاب]\n\n[كتاب]: https://example.com/كتاب  "عنوان , ها"'
        _assert_kept(text, "markdown", "[كتاب]\n", '[كتاب]: https://example.com/كتاب  "عنوان , ها"')

    def test_autolinks_and_html(self) -> None:
        text = f'<https://example.com/كتاب> و <span title="{BAD}">متن</span> <!-- {BAD} -->'
        _assert_kept(text, "markdown", "<https://example.com/كتاب>", f'title="{BAD}"', f"<!-- {BAD} -->")

    def test_math(self) -> None:
        text = f"فرمول $a,b ? c$ و\n$$\n{BAD}\n$$\nو $$x , y$$"
        _assert_kept(text, "markdown", "$a,b ? c$", f"$$\n{BAD}\n$$", "$$x , y$$")

    def test_dollar_amounts_are_not_math(self) -> None:
        assert paknevis.fix("قیمت $5 و $10 است , خوب", syntax="markdown").endswith("خوب")

    def test_ordered_list_markers_keep_ascii_digits(self) -> None:
        fixed = paknevis.fix("1. مورد اول\n2) مورد دوم\n10. مورد 3", syntax="markdown")
        assert fixed == "1. مورد اول\n2) مورد دوم\n10. مورد ۳"

    def test_footnotes_emoji_attributes_and_escapes(self) -> None:
        text = r"متن[^كتاب] :smile_cat: {#كتاب .x} \* \_ و"
        _assert_kept(text, "markdown", "[^كتاب]", ":smile_cat:", "{#كتاب .x}", r"\* \_")

    def test_templates(self) -> None:
        _assert_kept("{{ كتاب , ? }} و {% if كتاب %}", "markdown", "{{ كتاب , ? }}", "{% if كتاب %}")


class TestHtml:
    def test_tags_attributes_and_raw_elements(self) -> None:
        text = (
            f'<p class="x" title="{BAD}">سلام , دنیا</p><pre>{BAD}</pre>'
            f"<code>{BAD}</code><script>var a = '{BAD}';</script><style>/* {BAD} */</style>"
        )
        fixed = _assert_kept(
            text, "html", f'title="{BAD}"', f"<pre>{BAD}</pre>", f"<code>{BAD}</code>", f"'{BAD}'", f"/* {BAD} */"
        )
        assert "سلام، دنیا" in fixed

    def test_entities_and_comments(self) -> None:
        _assert_kept("کتاب&nbsp;ها &#x200c; <!-- كتاب , --> &laquo;", "html", "&nbsp;", "&#x200c;", "<!-- كتاب , -->")

    def test_doctype(self) -> None:
        _assert_kept("<!DOCTYPE html><p>سلام</p>", "html", "<!DOCTYPE html>")


class TestLatex:
    def test_commands_and_arguments(self) -> None:
        text = r"متن \cite{كتاب,ها} و \ref{fig:كتاب} و \label{sec:a} و \includegraphics[width=0.5\textwidth]{img/كتاب}"
        _assert_kept(text, "latex", r"\cite{كتاب,ها}", r"\ref{fig:كتاب}", r"[width=0.5\textwidth]{img/كتاب}")

    def test_text_commands_are_prose(self) -> None:
        fixed = paknevis.fix(r"\section{بيان مسئله} \textbf{نکته , مهم} \caption[كوتاه]{عنوان ها}", syntax="latex")
        assert fixed == "\\section{بیان مسئله} \\textbf{نکته، مهم} \\caption[كوتاه]{عنوان\u200cها}"

    def test_xepersian_latin_text(self) -> None:
        text = "مدل \\lr{Hello, world?} و \\latin{a , b}\n\\begin{latin}\nEnglish , text ?\n\\end{latin}"
        _assert_kept(text, "latex", r"\lr{Hello, world?}", r"\latin{a , b}", "English , text ?")

    def test_math(self) -> None:
        text = r"فرمول $a , b ?$ و $$x,y$$ و \(c , d\) و \[e , f\] و \$ دلار , بله"
        fixed = _assert_kept(text, "latex", "$a , b ?$", "$$x,y$$", r"\(c , d\)", r"\[e , f\]", r"\$")
        assert fixed.endswith("دلار، بله")

    @pytest.mark.parametrize("env", ["equation", "align*", "verbatim", "lstlisting", "minted", "tikzpicture", "LTR"])
    def test_protected_environments(self, env: str) -> None:
        _assert_kept(f"\\begin{{{env}}}\n{BAD}\n\\end{{{env}}}\nسلام , دنیا", "latex", BAD)

    def test_comments(self) -> None:
        fixed = _assert_kept(f"سلام , دنیا % {BAD}\n\\% درصد , بله", "latex", f"% {BAD}")
        assert fixed.startswith("سلام، دنیا")
        assert fixed.endswith("\\% درصد، بله")

    def test_verb(self) -> None:
        _assert_kept(rf"دستور \verb|{BAD}| و \verb+{BAD}+", "latex", f"|{BAD}|", f"+{BAD}+")

    def test_tabular_spec_and_line_breaks(self) -> None:
        text = "\\begin{tabular}{|c|c|}\nروش & دقت \\\\[2pt]\n\\end{tabular}"
        assert paknevis.fix(text, syntax="latex") == text

    def test_href_second_argument_is_prose(self) -> None:
        fixed = paknevis.fix(r"\href{https://x.org/كتاب}{پیوند , سایت}", syntax="latex")
        assert fixed == r"\href{https://x.org/كتاب}{پیوند، سایت}"

    def test_extra_text_commands(self) -> None:
        text = r"\myemph{نکته , مهم}"
        assert paknevis.fix(text, syntax="latex") == text
        assert paknevis.fix(text, syntax="latex", latex_text_commands=["myemph"]) == r"\myemph{نکته، مهم}"


class TestDirectives:
    def test_disable_enable_region(self) -> None:
        text = "<!-- paknevis-disable -->\nسلام , دنیا\n<!-- paknevis-enable -->\nسلام , دنیا"
        assert paknevis.fix(text, syntax="markdown").endswith("\nسلام، دنیا")
        assert "\nسلام , دنیا\n" in paknevis.fix(text, syntax="markdown")

    def test_disable_line_and_next_line(self) -> None:
        text = "سلام , دنیا % paknevis-disable-line\n% paknevis-disable-next-line\nسلام , دنیا\nسلام , دنیا"
        assert paknevis.fix(text, syntax="latex") == text.rsplit("\n", 1)[0] + "\nسلام، دنیا"

    def test_unterminated_disable(self) -> None:
        text = "سلام , دنیا\n<!-- paknevis-disable -->\nسلام , دنیا"
        assert paknevis.fix(text, syntax="html") == "سلام، دنیا\n<!-- paknevis-disable -->\nسلام , دنیا"

    def test_plain_text_directive(self) -> None:
        text = "# paknevis-disable-next-line\nسلام , دنیا"
        assert paknevis.fix(text) == text

    def test_directive_in_code_block_ignored(self) -> None:
        text = "```\n<!-- paknevis-disable -->\n```\nسلام , دنیا"
        assert paknevis.fix(text, syntax="markdown").endswith("سلام، دنیا")

    def test_stray_enable(self) -> None:
        text = "<!-- paknevis-enable -->\nسلام , دنیا"
        assert paknevis.fix(text, syntax="markdown").endswith("سلام، دنیا")


class TestHelpers:
    def test_merge_and_gaps(self) -> None:
        assert merge_spans([(5, 7), (0, 2), (1, 3), (7, 9), (4, 4)]) == [(0, 3), (5, 9)]
        assert gaps(10, [(0, 3), (5, 9)]) == [(3, 5), (9, 10)]
        assert gaps(3, []) == [(0, 3)]

    @pytest.mark.parametrize(
        ("name", "syntax"),
        [
            ("a.md", "markdown"),
            ("A.MARKDOWN", "markdown"),
            ("x.tex", "latex"),
            ("p.htm", "html"),
            ("r.txt", "plain"),
            ("x", "plain"),
        ],
    )
    def test_detect_syntax(self, name: str, syntax: str) -> None:
        assert detect_syntax(name) == syntax

    def test_normalize_syntax(self) -> None:
        assert normalize_syntax("MD") == "markdown"
        assert normalize_syntax(".tex") == "latex"
        with pytest.raises(ValueError, match="unknown syntax"):
            normalize_syntax("rst")

    def test_protected_spans_are_merged(self) -> None:
        spans = protected_spans("`a` https://x.org `b`", "markdown")
        assert spans == sorted(spans)
        assert all(a[1] < b[0] for a, b in itertools.pairwise(spans))
