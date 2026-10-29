"""Reduce a TeX log to the one thing a user can act on (RG-035).

A TeX log is hundreds of lines of package banners, font substitutions and overfull box warnings,
and roughly six of those lines matter. `parse_log` finds the first real error, the line number TeX
blamed for it, and a single sentence describing it. The rest of the log is kept as `raw` for the
`details` field of the error envelope and is never shown to a user.

This module is copied into the compiler container and imported by `app.py`. It has no dependency
on the pipeline package, and no dependency outside the standard library.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class TexError:
    line: int | None
    message: str
    raw: str


# TeX writes `l.40 \badmacro` when it can attribute an error to a source line.
_LINE_MARKER = re.compile(r"^l\.(\d+)")

# `Writing `resume.pdf` (2 pages, 51234 bytes)` from Tectonic, and
# `Output written on resume.pdf (2 pages, 51234 bytes).` from the TeX log itself.
_PAGE_COUNT = re.compile(
    r"(?:Writing|Output\s+written\s+on)\s+[`'\"]?[^\s`'\"()]*[`'\"]?\s*\(\s*(\d+)\s+pages?",
    re.IGNORECASE,
)

_UNDEFINED_CS = re.compile(r"^Undefined control sequence")
_FILE_NOT_FOUND = re.compile(r"^LaTeX Error: File\s+[`'\"]?([^`'\"]+)[`'\"]?\s+not found")
_MISSING_MATH = re.compile(r"^Missing \$ inserted")
_EMERGENCY_STOP = re.compile(r"^Emergency stop")
_CAPACITY = re.compile(r"^TeX capacity exceeded,?\s*sorry\s*(\[[^\]]*\])?")
_PACKAGE_ERROR = re.compile(r"^Package\s+(\S+)\s+Error:\s*(.*)$")
_LATEX_ERROR = re.compile(r"^LaTeX Error:\s*(.*)$")

# The token TeX was reading when it hit an undefined control sequence appears at the end of the
# `l.NNN` line, or on the continuation line just above it.
_TRAILING_CS = re.compile(r"(\\[a-zA-Z@]+)\s*$")

# How many lines after the `! ` line are kept as context, and searched for `l.NNN`.
_CONTEXT_LINES = 12


def _sentence(text: str) -> str:
    """One sentence: collapsed whitespace, exactly one trailing full stop."""
    collapsed = " ".join(text.split()).strip()
    collapsed = collapsed.rstrip(".").strip()
    return f"{collapsed}." if collapsed else ""


def _find_line_number(context: list[str]) -> int | None:
    for entry in context:
        match = _LINE_MARKER.match(entry)
        if match:
            return int(match.group(1))
    return None


def _find_offending_cs(context: list[str]) -> str | None:
    for entry in context:
        if _LINE_MARKER.match(entry):
            match = _TRAILING_CS.search(entry)
            if match:
                return match.group(1)
    for entry in context:
        match = _TRAILING_CS.search(entry)
        if match:
            return match.group(1)
    return None


def _strip_markers(body: str) -> str:
    """Drop repeated `!` error markers.

    Tectonic re-prefixes an error it forwards from the engine, so the log can hold
    `! ! LaTeX Error: File 'x.clo' not found..` with the marker and the full stop doubled. Left in
    place, that doubling stops every pattern below from matching its own error class.
    """
    while body.startswith("!"):
        body = body[1:].lstrip()
    return body


def _summarise(body: str, context: list[str]) -> str:
    """One sentence for the `! <body>` line, using `context` when the detail lives below it."""
    body = _strip_markers(body.strip())

    if _UNDEFINED_CS.match(body):
        cs = _find_offending_cs(context)
        if cs:
            return _sentence(f"Undefined control sequence {cs}")
        return _sentence("Undefined control sequence")

    match = _FILE_NOT_FOUND.match(body)
    if match:
        return _sentence(f"File '{match.group(1).strip()}' not found")

    if _MISSING_MATH.match(body):
        return _sentence("Missing $ inserted, so a maths character was used outside maths mode")

    if _EMERGENCY_STOP.match(body):
        return _sentence("Emergency stop, so TeX could not continue")

    match = _CAPACITY.match(body)
    if match:
        detail = (match.group(1) or "").strip()
        if detail:
            return _sentence(f"TeX capacity exceeded {detail}")
        return _sentence("TeX capacity exceeded")

    match = _PACKAGE_ERROR.match(body)
    if match:
        package, detail = match.group(1), match.group(2).strip()
        if detail:
            return _sentence(f"Package {package} error: {detail}")
        return _sentence(f"Package {package} error")

    match = _LATEX_ERROR.match(body)
    if match and match.group(1).strip():
        return _sentence(f"LaTeX error: {match.group(1)}")

    # Unrecognised: return the error's own text rather than inventing a generic message, because
    # the TeX wording is the only information anyone has.
    return _sentence(body)


def parse_log(log: str) -> TexError | None:
    """The first meaningful error in `log`, or None when the log holds no error."""
    if not log:
        return None

    lines = log.splitlines()
    for index, entry in enumerate(lines):
        if not entry.startswith("! "):
            continue
        body = entry[2:]
        context = lines[index + 1 : index + 1 + _CONTEXT_LINES]
        message = _summarise(body, context)
        if not message:
            continue
        line_number = _find_line_number(context)
        raw = "\n".join(lines[index : index + 1 + _CONTEXT_LINES]).strip()
        return TexError(line=line_number, message=message, raw=raw)
    return None


def page_count(log: str) -> int | None:
    """Pages in the produced PDF, or None when the log does not say."""
    if not log:
        return None
    matches = _PAGE_COUNT.findall(log)
    if not matches:
        return None
    return int(matches[-1])
