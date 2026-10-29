"""LaTeX to plain text reduction (RG-033).

Shared by the ATS service and the import service. Reduces a LaTeX document to the prose an ATS
would actually read, so that a `.tex` resume and its plain-text equivalent score alike. Plain
text passes through unchanged, which is what makes this safe to call on an imported resume of
unknown format.
"""

from __future__ import annotations

import re

_BEGIN_DOCUMENT_RE = re.compile(r"(?s)^.*?\\begin\{document\}")
_END_DOCUMENT_RE = re.compile(r"(?s)\\end\{document\}.*$")

# An unescaped percent starts a comment. `\%` is a literal percent and must survive.
_COMMENT_RE = re.compile(r"(?<!\\)%.*$", re.MULTILINE)

# Macros that wrap text and should be replaced by their argument.
_UNWRAP_MACROS = ("textbf", "textit", "emph", "underline", "texttt", "textsc", "textrm", "url")
_UNWRAP_RE = re.compile(r"\\(?:" + "|".join(_UNWRAP_MACROS) + r")\*?\{([^{}]*)\}")

# `\href{url}{label}` keeps the label; the URL is not prose.
_HREF_RE = re.compile(r"\\href\{[^{}]*\}\{([^{}]*)\}")

# Headings carry section names the ATS structural score looks for, so keep the argument on its
# own line rather than dropping it with the other macros.
_HEADING_RE = re.compile(r"\\(?:sub)*section\*?\{([^{}]*)\}")

# Layout-only macros: the macro and its arguments both go.
_LAYOUT_WITH_ARGS_RE = re.compile(
    r"\\(?:vspace|hspace|rule|setlength|hskip|vskip)\*?(?:\[[^\]]*\])?(?:\{[^{}]*\})*"
)
_LAYOUT_BARE_RE = re.compile(r"\\(?:hfill|vfill|newpage|clearpage|noindent|centering|par)\b")
_ENVIRONMENT_RE = re.compile(r"\\(?:begin|end)\{[^{}]*\}(?:\[[^\]]*\])?")

# `\\` is a line break, optionally carrying a spacing argument such as `\\[2pt]`.
_LINE_BREAK_RE = re.compile(r"\\\\(?:\[[^\]]*\])?")

_ITEM_RE = re.compile(r"\\item\b")

# Anything still starting with a backslash is a command with no prose value.
_REMAINING_MACRO_RE = re.compile(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{[^{}]*\})*")

_ESCAPES = (
    (r"\&", "&"),
    (r"\%", "%"),
    (r"\$", "$"),
    (r"\#", "#"),
    (r"\_", "_"),
)


# A document is LaTeX if it declares a class, opens an environment, or uses a
# macro with an argument. Anything else is prose, and its `%` characters are
# percent signs. This is deliberately conservative: misreading LaTeX as prose
# leaves a few comments in the scored text, which costs a point or two;
# misreading prose as LaTeX deletes the end of any line containing a percentage,
# which silently destroys exactly the quantified achievements the structural
# score rewards.
_LATEX_MARKERS_RE = re.compile(r"\\(?:documentclass|begin|end|usepackage|item)\b|\\[A-Za-z]+\s*\{|\\[%&$#_]|\\\\")


def _looks_like_latex(text: str) -> bool:
    return bool(_LATEX_MARKERS_RE.search(text))


def tex_to_text(tex: str) -> str:
    """Reduce a LaTeX document to the prose an ATS would see.

    Input without a `\\begin{document}` is treated as already-plain text and kept whole.
    """
    text = tex or ""
    # Decided on the original input: step 1 strips the very markers that identify it.
    is_latex = _looks_like_latex(text)

    # 1. Drop the preamble and anything after the document ends, when there is a document body.
    if r"\begin{document}" in text:
        text = _BEGIN_DOCUMENT_RE.sub("", text, count=1)
    text = _END_DOCUMENT_RE.sub("", text)

    # 2. Comments go before anything else rewrites the line, but after `\%` has been
    #    left alone — and only when the input is actually LaTeX. A pasted plain-text
    #    resume reaches this function too (the import flow scores one), and there a
    #    bare `%` is a percent sign: stripping to end of line would silently delete
    #    "cut latency by 45% across 12 services" from the middle of a bullet.
    if is_latex:
        text = _COMMENT_RE.sub("", text)

    # 3. Bullets become line breaks; the ATS structural score counts bullets per line.
    text = _ITEM_RE.sub("\n- ", text)
    text = _LINE_BREAK_RE.sub("\n", text)

    # 4. Unwrap text macros to their argument, innermost first.
    for _ in range(10):
        unwrapped = _UNWRAP_RE.sub(r"\1", text)
        if unwrapped == text:
            break
        text = unwrapped
    text = _HREF_RE.sub(r"\1", text)
    text = _HEADING_RE.sub(r"\n\1\n", text)

    # 5. Drop layout-only macros and environment markers.
    text = _LAYOUT_WITH_ARGS_RE.sub(" ", text)
    text = _ENVIRONMENT_RE.sub("", text)
    text = _LAYOUT_BARE_RE.sub(" ", text)

    # 6. Whatever command is left has no prose in it.
    text = _REMAINING_MACRO_RE.sub(" ", text)

    # 7. Escaped characters become the characters they stand for.
    for escaped, literal in _ESCAPES:
        text = text.replace(escaped, literal)

    # 8. Leftover grouping braces and quoting artefacts.
    text = text.replace("``", '"').replace("''", '"')
    text = re.sub(r"[{}]", " ", text)

    return _normalise(text)


def _normalise(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
