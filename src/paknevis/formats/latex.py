r"""LaTeX protection, tuned for Persian documents typeset with XePersian.

Commands, their options and non-textual arguments, comments, math and
verbatim-like environments are protected. Arguments of *text commands*
(``\section``, ``\textbf``, ``\caption``, ``\footnote`` …) remain prose so
that headings and captions are linted. XePersian's ``\lr{…}``/``\latin{…}``
and the ``latin``/``LTR`` environments hold left-to-right Latin text and are
protected.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from ..models import Span

TEXT_COMMANDS = frozenset(
    [
        "textbf",
        "textit",
        "emph",
        "textsl",
        "textup",
        "textmd",
        "textrm",
        "textsf",
        "textsc",
        "underline",
        "uline",
        "hl",
        "section",
        "subsection",
        "subsubsection",
        "paragraph",
        "subparagraph",
        "chapter",
        "part",
        "caption",
        "footnote",
        "footnotetext",
        "marginpar",
        "title",
        "author",
        "thanks",
        "date",
        "mbox",
        "fbox",
        "centerline",
        "intertext",
        "frametitle",
        "framesubtitle",
        "alert",
        "structure",
        "MakeUppercase",
        "MakeLowercase",
        "textnormal",
        "textsuperscript",
        "textsubscript",
        "rl",
        "textpersian",
        "textfarsi",
    ]
)
"""Commands whose ``{…}`` arguments are Persian prose."""

FIRST_ARG_PROTECTED = frozenset({"textcolor", "colorbox", "href", "foreignlanguage", "fcolorbox"})
"""Commands whose first argument is technical and later arguments are prose."""

VERBATIM_ENVIRONMENTS = frozenset(
    [
        "verbatim",
        "verbatim*",
        "Verbatim",
        "Verbatim*",
        "BVerbatim",
        "LVerbatim",
        "spverbatim",
        "alltt",
        "lstlisting",
        "minted",
        "comment",
        "filecontents",
        "filecontents*",
        "equation",
        "equation*",
        "align",
        "align*",
        "alignat",
        "alignat*",
        "flalign",
        "flalign*",
        "gather",
        "gather*",
        "multline",
        "multline*",
        "eqnarray",
        "eqnarray*",
        "math",
        "displaymath",
        "split",
        "tikzpicture",
        "pgfpicture",
        "forest",
        "latin",
        "LTR",
        "english",
    ]
)
"""Environments whose whole body is protected."""

_COMMAND = re.compile(r"\\([A-Za-z@]+)\*?")
_ENV_NAME = re.compile(r"\{([^{}]*)\}")


def _match_group(text: str, start: int, open_char: str, close_char: str) -> int:
    """Index just past the group starting at *start* (balanced, escape-aware)."""
    depth = 0
    i = start
    while i < len(text):
        char = text[i]
        if char == "\\":
            i += 2
            continue
        if char == open_char:
            depth += 1
        elif char == close_char:
            depth -= 1
            if depth == 0:
                return i + 1
        elif char == "%" and open_char == "{":
            newline = text.find("\n", i)
            i = len(text) if newline == -1 else newline
            continue
        i += 1
    return len(text)


def _skip_groups(text: str, index: int, spans: list[Span]) -> int:
    """Protect adjacent ``[…]``/``{…}`` groups starting at *index*."""
    while index < len(text) and text[index] in "[{":
        end = _match_group(text, index, text[index], "]" if text[index] == "[" else "}")
        spans.append((index, end))
        index = end
    return index


def latex_spans(text: str, extra_text_commands: Iterable[str] = ()) -> tuple[list[Span], list[Span]]:
    """Protected spans for LaTeX. Returns ``(protected, code)``."""
    text_commands = TEXT_COMMANDS | frozenset(extra_text_commands)
    spans: list[Span] = []
    code: list[Span] = []
    i = 0
    n = len(text)
    while i < n:
        char = text[i]
        if char == "%":
            newline = text.find("\n", i)
            end = n if newline == -1 else newline
            spans.append((i, end))
            i = end
        elif char == "\\":
            i = _handle_backslash(text, i, spans, code, text_commands)
        elif char == "$":
            delimiter = "$$" if text.startswith("$$", i) else "$"
            close = _find_unescaped(text, delimiter, i + len(delimiter))
            end = n if close == -1 else close + len(delimiter)
            spans.append((i, end))
            i = end
        elif char in "{}&":
            spans.append((i, i + 1))
            i += 1
        else:
            i += 1
    return spans, code


def _find_unescaped(text: str, needle: str, start: int) -> int:
    index = text.find(needle, start)
    while index != -1 and index > 0 and text[index - 1] == "\\":
        index = text.find(needle, index + 1)
    return index


def _handle_backslash(text: str, i: int, spans: list[Span], code: list[Span], text_commands: frozenset[str]) -> int:
    n = len(text)
    command = _COMMAND.match(text, i)
    if command is None:
        nxt = text[i + 1 : i + 2]
        if nxt in ("[", "("):
            closing = "\\]" if nxt == "[" else "\\)"
            close = text.find(closing, i + 2)
            end = n if close == -1 else close + 2
            spans.append((i, end))
            return end
        end = min(i + 2, n)
        spans.append((i, end))
        if nxt == "\\":  # line break with optional spacing: \\[2pt]
            return _skip_groups(text, end, spans) if text[end : end + 1] == "[" else end
        return end

    name = command.group(1)
    end = command.end()
    if name in ("begin", "end"):
        env = _ENV_NAME.match(text, end)
        if env is None:
            spans.append((i, end))
            return end
        env_name = env.group(1).strip()
        if name == "begin" and env_name in VERBATIM_ENVIRONMENTS:
            closing = f"\\end{{{env_name}}}"
            close = text.find(closing, env.end())
            stop = n if close == -1 else close + len(closing)
            spans.append((i, stop))
            code.append((i, stop))
            return stop
        spans.append((i, env.end()))
        return _skip_groups(text, env.end(), spans) if name == "begin" else env.end()

    if name in ("verb", "lstinline", "mintinline"):
        j = end
        if name == "mintinline" or text[j : j + 1] == "[":
            j = _skip_groups(text, j, spans)
        if j >= n:
            spans.append((i, n))
            return n
        delimiter = text[j]
        stop = _match_group(text, j, "{", "}") if delimiter == "{" else text.find(delimiter, j + 1) + 1
        if stop <= 0:
            stop = n
        spans.append((i, stop))
        code.append((i, stop))
        return stop

    spans.append((i, end))
    if name in text_commands:
        # Options are technical, the {…} argument is prose: protect only braces
        # (the main loop protects every bare brace it meets).
        return _skip_options(text, end, spans)
    if name in FIRST_ARG_PROTECTED:
        j = _skip_options(text, end, spans)
        if text[j : j + 1] == "{":
            stop = _match_group(text, j, "{", "}")
            spans.append((j, stop))
            return stop
        return j
    return _skip_groups(text, end, spans)


def _skip_options(text: str, index: int, spans: list[Span]) -> int:
    while text[index : index + 1] == "[":
        end = _match_group(text, index, "[", "]")
        spans.append((index, end))
        index = end
    return index
