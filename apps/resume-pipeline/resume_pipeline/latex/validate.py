"""LaTeX structural and denylist validation (RG-021, RG-035).

The `.tex` this package guards is user input, and TeX is a programming language with file and
shell primitives in it. `\\write18`, `\\input{/etc/passwd}` and `\\openout` are real escapes, so
this scanner is a security control rather than a lint.

Three properties make it honest rather than decorative, and all three are load bearing:

* **Comments are stripped first, correctly.** An unescaped ``%`` starts a comment; ``\\%`` is a
  literal percent and does not. A scanner that skips this flags every commented-out example, and a
  scanner that strips naively lets ``\\%`` hide the rest of a line from itself.
* **Whitespace between a control sequence and its argument is arbitrary.** ``\\write18``,
  ``\\write 18`` and ``\\write`` followed by a newline and ``18`` are the same thing to TeX, so
  they are the same thing here.
* **Category-code reassignment of ``\\``, ``{`` or ``}`` is itself denied.** It is the standard way
  to make a payload unrecognisable to a pattern matcher, so a scanner that allows it is only
  pretending to be one.

Comment stripping blanks the commented span in place rather than deleting it, so every offset in
the masked text still maps to the same line in the original. That is how every problem can carry a
truthful 1-indexed line number.
"""

from __future__ import annotations

import bisect
import re
from dataclasses import dataclass

from resume_pipeline.errors import ValidationFailed

MAX_TEX_BYTES = 200 * 1024

# Category codes of the three characters whose meaning the scanner depends on.
_BACKSLASH = 92
_BRACE_OPEN = 123
_BRACE_CLOSE = 125
_STRUCTURAL_CHAR_CODES = {_BACKSLASH: "\\", _BRACE_OPEN: "{", _BRACE_CLOSE: "}"}


@dataclass(frozen=True)
class Problem:
    """One reason a template was rejected.

    `line` is 1-indexed. It is 0 when the problem is about the document as a whole — the source
    being over the size limit, or a missing `\\begin{document}` — rather than about one line.
    """

    line: int
    message: str


# --------------------------------------------------------------------------------------
# Comment masking
# --------------------------------------------------------------------------------------


def _mask_comments(tex: str) -> str:
    """Blank every TeX comment, preserving length and every newline position.

    A backslash escapes the character after it, so `\\%` is a literal percent sign and never
    starts a comment. Any other unescaped `%` comments out the rest of its line. The commented
    span becomes spaces rather than disappearing, which keeps offsets in the returned string
    aligned with offsets in `tex`.
    """
    out: list[str] = []
    i = 0
    n = len(tex)
    while i < n:
        ch = tex[i]
        if ch == "\\":
            # The next character belongs to this control sequence whatever it is, including a
            # percent sign and including a newline. Copy both verbatim.
            out.append(ch)
            if i + 1 < n:
                out.append(tex[i + 1])
            i += 2
            continue
        if ch == "%":
            end = tex.find("\n", i)
            if end == -1:
                out.append(" " * (n - i))
                i = n
            else:
                out.append(" " * (end - i))
                i = end
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _line_starts(text: str) -> list[int]:
    starts = [0]
    for match in re.finditer("\n", text):
        starts.append(match.end())
    return starts


def _line_of(starts: list[int], offset: int) -> int:
    return bisect.bisect_right(starts, offset)


# --------------------------------------------------------------------------------------
# Patterns
#
# Every control sequence is matched with a negative lookahead for a letter, because TeX ends a
# control word at the first non-letter: `\include` and `\includegraphics` are different macros,
# and `\read` and `\readline` are different macros.
# --------------------------------------------------------------------------------------

_DOCUMENTCLASS = re.compile(r"\\documentclass(?![a-zA-Z])")
_BEGIN_DOCUMENT = re.compile(r"\\begin\s*\{\s*document\s*\}")
_END_DOCUMENT = re.compile(r"\\end\s*\{\s*document\s*\}")

_WRITE = re.compile(r"\\write(?![a-zA-Z])")
_WRITE_18 = re.compile(r"\s*18(?![0-9])")

_STREAM_OPS = re.compile(r"\\(openout|openin|read)(?![a-zA-Z])")

_INPUT = re.compile(
    r"\\(?P<cs>input|include)(?![a-zA-Z])\s*(?:\{(?P<braced>[^}]*)\}|(?P<bare>[^\s{}\\%,]+))"
)

_CATCODE = re.compile(
    r"\\catcode\s*"
    r"(?:"
    r"`\s*\\?(?P<ch>.)"
    r"|\"(?P<hex>[0-9A-Fa-f]+)"
    r"|'(?P<oct>[0-7]+)"
    r"|(?P<dec>[0-9]+)"
    r")?",
    re.DOTALL,
)

_USEPACKAGE = re.compile(
    r"\\(?:usepackage|RequirePackage)(?![a-zA-Z])\s*(?:\[[^\]]*\]\s*)?\{(?P<names>[^}]*)\}"
)

_SHELL_CS = re.compile(r"\\(ShellEscape|directlua)(?![a-zA-Z])")

_SPECIAL = re.compile(r"\\special(?![a-zA-Z])\s*\{(?P<body>[^}]*)\}")
_SPECIAL_SHELL = re.compile(
    r"[`|;]|\$\(|\bsystem\b|\bexec\b|\bpopen\b|\bbash\b|\bsh\b|\bcurl\b|\bwget\b|\brm\b",
    re.IGNORECASE,
)

_CONTROL_SEQUENCE = re.compile(r"\\[a-zA-Z@]+|\\.")


# --------------------------------------------------------------------------------------
# Scanners
# --------------------------------------------------------------------------------------


def _scan_structure(masked: str) -> list[Problem]:
    problems: list[Problem] = []
    if not _DOCUMENTCLASS.search(masked):
        problems.append(
            Problem(0, "The template has no \\documentclass. Add one and save again.")
        )
    if not _BEGIN_DOCUMENT.search(masked):
        problems.append(
            Problem(0, "The template has no \\begin{document}. Add one and save again.")
        )
    if not _END_DOCUMENT.search(masked):
        problems.append(
            Problem(0, "The template has no \\end{document}. Add one and save again.")
        )
    return problems


def _scan_write(masked: str, starts: list[int]) -> list[tuple[int, Problem]]:
    found: list[tuple[int, Problem]] = []
    for match in _WRITE.finditer(masked):
        line = _line_of(starts, match.start())
        # `\write18` is shell escape; every other `\write` targets an output stream. Classify
        # each occurrence once so a single macro never produces two problems.
        if _WRITE_18.match(masked, match.end()):
            message = f"Line {line} uses \\write18, which runs a shell command. Remove it and save again."
        else:
            message = (
                f"Line {line} uses \\write, which writes to a file stream. Remove it and save again."
            )
        found.append((match.start(), Problem(line, message)))
    return found


def _scan_stream_ops(masked: str, starts: list[int]) -> list[tuple[int, Problem]]:
    found: list[tuple[int, Problem]] = []
    for match in _STREAM_OPS.finditer(masked):
        line = _line_of(starts, match.start())
        name = match.group(1)
        found.append(
            (
                match.start(),
                Problem(
                    line,
                    f"Line {line} uses \\{name}, which opens a file stream. "
                    "Remove it and save again.",
                ),
            )
        )
    return found


def _scan_input(masked: str, starts: list[int]) -> list[tuple[int, Problem]]:
    found: list[tuple[int, Problem]] = []
    for match in _INPUT.finditer(masked):
        cs = match.group("cs")
        raw = match.group("braced")
        if raw is None:
            raw = match.group("bare") or ""
        path = raw.strip()
        line = _line_of(starts, match.start())
        reason: str | None = None
        if path.startswith("/"):
            reason = "an absolute path"
        elif ".." in path:
            reason = "a parent directory path"
        elif _CONTROL_SEQUENCE.search(path):
            # The path is assembled by a macro, so it cannot be checked by reading it. Treating
            # that as acceptable is exactly the hole `\def\p{/etc/passwd}` walks through.
            reason = "a path this check cannot resolve"
        if reason is not None:
            found.append(
                (
                    match.start(),
                    Problem(
                        line,
                        f"Line {line} uses \\{cs} with {reason}. "
                        "Use a file inside the template directory and save again.",
                    ),
                )
            )
    return found


def _catcode_target(match: re.Match[str]) -> str | None:
    """The character whose category code is being set, or None when it cannot be determined."""
    ch = match.group("ch")
    if ch is not None:
        return ch
    for group, base in (("hex", 16), ("oct", 8), ("dec", 10)):
        raw = match.group(group)
        if raw is not None:
            try:
                return _STRUCTURAL_CHAR_CODES.get(int(raw, base))
            except ValueError:  # pragma: no cover - the pattern already constrains the digits
                return None
    return None


def _scan_catcode(masked: str, starts: list[int]) -> list[tuple[int, Problem]]:
    found: list[tuple[int, Problem]] = []
    for match in _CATCODE.finditer(masked):
        line = _line_of(starts, match.start())
        parsed = any(match.group(name) is not None for name in ("ch", "hex", "oct", "dec"))
        target = _catcode_target(match)
        if not parsed:
            # `\catcode` with an argument this scanner cannot read is treated as denied. A
            # category-code assignment it cannot evaluate is precisely how a payload gets past it.
            found.append(
                (
                    match.start(),
                    Problem(
                        line,
                        f"Line {line} uses \\catcode in a form this check cannot read. "
                        "Remove the category code assignment and save again.",
                    ),
                )
            )
            continue
        if target in _STRUCTURAL_CHAR_CODES.values():
            found.append(
                (
                    match.start(),
                    Problem(
                        line,
                        f"Line {line} reassigns the category code of {target}, which changes how "
                        "the rest of the file is read. Remove the \\catcode assignment and save "
                        "again.",
                    ),
                )
            )
    return found


def _scan_shell_escape(masked: str, starts: list[int]) -> list[tuple[int, Problem]]:
    found: list[tuple[int, Problem]] = []
    for match in _USEPACKAGE.finditer(masked):
        names = [name.strip().lower() for name in match.group("names").split(",")]
        if "shellesc" in names:
            line = _line_of(starts, match.start())
            found.append(
                (
                    match.start(),
                    Problem(
                        line,
                        f"Line {line} loads the shellesc package, which enables shell escape. "
                        "Remove it and save again.",
                    ),
                )
            )
    for match in _SHELL_CS.finditer(masked):
        line = _line_of(starts, match.start())
        name = match.group(1)
        found.append(
            (
                match.start(),
                Problem(
                    line,
                    f"Line {line} uses \\{name}, which runs code outside TeX. "
                    "Remove it and save again.",
                ),
            )
        )
    return found


def _scan_special(masked: str, starts: list[int]) -> list[tuple[int, Problem]]:
    found: list[tuple[int, Problem]] = []
    for match in _SPECIAL.finditer(masked):
        body = match.group("body")
        if "dvipdfmx:" in body.lower() or _SPECIAL_SHELL.search(body):
            line = _line_of(starts, match.start())
            found.append(
                (
                    match.start(),
                    Problem(
                        line,
                        f"Line {line} uses \\special with a driver or shell directive. "
                        "Remove it and save again.",
                    ),
                )
            )
    return found


# --------------------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------------------


def validate_tex(tex: str) -> list[Problem]:
    """Return every problem in `tex`, in document order, or an empty list when it is safe.

    Every problem is reported, never just the first. A user who has to submit, read one
    rejection, fix it and submit again learns the denylist one round trip at a time, and RG-021
    calls that out explicitly.
    """
    problems: list[Problem] = []

    size = len(tex.encode("utf-8"))
    if size > MAX_TEX_BYTES:
        problems.append(
            Problem(
                0,
                f"The LaTeX source is {size // 1024} KB, over the {MAX_TEX_BYTES // 1024} KB "
                "limit. Remove unused content and save again.",
            )
        )

    masked = _mask_comments(tex)
    starts = _line_starts(masked)

    problems.extend(_scan_structure(masked))

    located: list[tuple[int, Problem]] = []
    located.extend(_scan_write(masked, starts))
    located.extend(_scan_stream_ops(masked, starts))
    located.extend(_scan_input(masked, starts))
    located.extend(_scan_catcode(masked, starts))
    located.extend(_scan_shell_escape(masked, starts))
    located.extend(_scan_special(masked, starts))
    located.sort(key=lambda item: item[0])

    problems.extend(problem for _, problem in located)
    return problems


def assert_valid_tex(tex: str) -> None:
    """Raise `ValidationFailed` when `tex` has any problem, carrying all of them.

    The problems land in `details["problems"]` as plain dicts, because `details` is serialised
    straight into the error envelope the UI reads.
    """
    problems = validate_tex(tex)
    if not problems:
        return
    if len(problems) == 1:
        message = problems[0].message
    else:
        message = (
            f"The LaTeX source has {len(problems)} problems. Fix each one listed and save again."
        )
    raise ValidationFailed(
        message,
        details={"problems": [{"line": p.line, "message": p.message} for p in problems]},
    )
