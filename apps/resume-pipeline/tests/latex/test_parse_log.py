"""Reducing a TeX log to one sentence and one line number (WP7 §2).

A TeX log is hundreds of lines of noise around a few characters of signal. `parse_log` finds the
first meaningful error, the line number from the nearest following `l.NNN` marker, and a summary
short enough to show a user who has never seen a TeX log and should not have to.

The `raw` field carries the excerpt for operators. It is never shown to the user, which is why
every test here also checks the summary stayed a summary.
"""

from __future__ import annotations

from types import ModuleType

import pytest

# ─── Realistic log excerpts ───────────────────────────────────────────────────

UNDEFINED_CONTROL_SEQUENCE = r"""This is Tectonic 0.17.0
Running TeX ...
(resume.tex
LaTeX2e <2023-11-01> patch level 1
(/usr/share/texmf/tex/latex/base/article.cls
Document Class: article 2023/05/17 v1.4n Standard LaTeX document class
)
(/usr/share/texmf/tex/latex/geometry/geometry.sty)
! Undefined control sequence.
l.42 \resumeHeading
                   {Liv-ex}{London, UK}
The control sequence at the end of the top line
of your error message was never \def'ed.
"""

MISSING_STY_FILE = r"""This is Tectonic 0.17.0
Running TeX ...
(resume.tex
LaTeX2e <2023-11-01> patch level 1
(/usr/share/texmf/tex/latex/base/article.cls)
! LaTeX Error: File `fontawesome5.sty' not found.

Type X to quit or <RETURN> to proceed,
or enter new name. (Default extension: sty)

Enter file name:
! Emergency stop.
<read *>

l.9 \usepackage{fontawesome5}
No pages of output.
"""

MISSING_DOLLAR = r"""This is Tectonic 0.17.0
Running TeX ...
(resume.tex
LaTeX2e <2023-11-01> patch level 1
! Missing $ inserted.
<inserted text>
                $
l.68 ...95 latency from 2.5s to 250ms (-40_
                                           ) across twelve services.
I've inserted a begin-math/end-math symbol since I think
you left one out.
"""

EMERGENCY_STOP = r"""This is Tectonic 0.17.0
Running TeX ...
(resume.tex
LaTeX2e <2023-11-01> patch level 1
Runaway argument?
{Liv-ex, London, UK \textit {Software Engineer} \item Architected \ETC.
! Emergency stop.
<inserted text>
                \par
l.57 \end{document}
End of file on the terminal!
No pages of output.
"""

CAPACITY_EXCEEDED = r"""This is Tectonic 0.17.0
Running TeX ...
(resume.tex
LaTeX2e <2023-11-01> patch level 1
! TeX capacity exceeded, sorry [main memory size=5000000].
\spin ->\advance \spin
                       by 0
l.31 \loop\advance\spin by 0\ifnum\spin<1\repeat
If you really absolutely need more capacity,
you can ask a wizard to enlarge me.
"""

PACKAGE_ERROR = r"""This is Tectonic 0.17.0
Running TeX ...
(resume.tex
LaTeX2e <2023-11-01> patch level 1
(/usr/share/texmf/tex/latex/geometry/geometry.sty
! Package geometry Error: \paperwidth (0.0pt) too short.

See the geometry package documentation for explanation.
Type  H <return>  for immediate help.
 ...

l.6 \usepackage[paperwidth=0pt,margin=0.5in]{geometry}
No pages of output.
"""

UNRECOGNISED_ERROR = r"""This is Tectonic 0.17.0
Running TeX ...
(resume.tex
! Dimension too large.
<recently read> \dimen 0
l.77 \hspace{20000pt}
"""

CLEAN_LOG = r"""This is Tectonic 0.17.0
Running TeX ...
(resume.tex
LaTeX2e <2023-11-01> patch level 1
(/usr/share/texmf/tex/latex/base/article.cls
Document Class: article 2023/05/17 v1.4n Standard LaTeX document class
)
(/usr/share/texmf/tex/latex/geometry/geometry.sty)
(/usr/share/texmf/tex/latex/hyperref/hyperref.sty)
Overfull \hbox (12.48pt too wide) in paragraph at lines 45--47
LaTeX Warning: Reference `sec:experience' on page 1 undefined on input line 52.
[1] [2]
Running TeX ... done.
Writing `resume.pdf` (2 pages, 78432 bytes)
Skipped writing 1 intermediate files (use --keep-intermediates to keep them)
"""

# (id, log, expected line, a token the one-sentence summary must contain)
NAMED_ERROR_CLASSES: list[tuple[str, str, int, tuple[str, ...]]] = [
    ("undefined_control_sequence", UNDEFINED_CONTROL_SEQUENCE, 42, ("undefined",)),
    ("missing_sty_file", MISSING_STY_FILE, 9, ("fontawesome5",)),
    ("missing_dollar", MISSING_DOLLAR, 68, ("$", "math", "dollar")),
    ("emergency_stop", EMERGENCY_STOP, 57, ("stop", "abort", "finish")),
    ("capacity_exceeded", CAPACITY_EXCEEDED, 31, ("capacity", "memory", "large")),
    ("package_error", PACKAGE_ERROR, 6, ("geometry",)),
]

NAMED_IDS = [case[0] for case in NAMED_ERROR_CLASSES]
NAMED_CASES = [(case[1], case[2], case[3]) for case in NAMED_ERROR_CLASSES]


def assert_one_sentence(message: str) -> None:
    assert message.strip(), "An error with no summary tells the user nothing."
    assert "\n" not in message.strip(), f"The summary must be one sentence, got {message!r}."
    assert len(message) <= 200, f"The summary must be one sentence, got {len(message)} characters."


# ─── The six named error classes ──────────────────────────────────────────────


@pytest.mark.parametrize(("log", "line", "tokens"), NAMED_CASES, ids=NAMED_IDS)
def test_a_named_error_class_yields_its_line_number(
    parse_log_mod: ModuleType, log: str, line: int, tokens: tuple[str, ...]
) -> None:
    error = parse_log_mod.parse_log(log)

    assert error is not None, "This log contains an error and must not parse as clean."
    assert error.line == line, f"Expected the l.{line} marker nearest the first `! ` line."


@pytest.mark.parametrize(("log", "line", "tokens"), NAMED_CASES, ids=NAMED_IDS)
def test_a_named_error_class_is_summarised_in_one_sentence(
    parse_log_mod: ModuleType, log: str, line: int, tokens: tuple[str, ...]
) -> None:
    error = parse_log_mod.parse_log(log)

    assert error is not None
    assert_one_sentence(error.message)
    assert "!" not in error.message, "Copy rule: no exclamation marks in an authored summary."
    assert any(token.lower() in error.message.lower() for token in tokens), (
        f"The summary must name the actual problem (one of {tokens}), got {error.message!r}."
    )


@pytest.mark.parametrize(("log", "line", "tokens"), NAMED_CASES, ids=NAMED_IDS)
def test_the_full_log_stays_in_raw_and_out_of_the_summary(
    parse_log_mod: ModuleType, log: str, line: int, tokens: tuple[str, ...]
) -> None:
    """`raw` is for operators. The user gets the sentence, never the log."""
    error = parse_log_mod.parse_log(log)

    assert error is not None
    assert error.raw, "The operator-facing excerpt must not be empty."
    assert error.raw != error.message
    assert "This is Tectonic" not in error.message, "The log banner is noise, not a summary."
    assert "\n" not in error.message.strip()


def test_the_first_error_wins_when_a_log_holds_two(parse_log_mod: ModuleType) -> None:
    """A missing .sty is followed by an emergency stop. The missing file is the real cause,
    and reporting the stop instead sends the user to the wrong place."""
    error = parse_log_mod.parse_log(MISSING_STY_FILE)

    assert error is not None
    assert "fontawesome5" in error.message
    assert error.line == 9


# ─── Unrecognised errors keep their own text ──────────────────────────────────


def test_an_unrecognised_error_returns_its_own_text_not_a_generic_message(
    parse_log_mod: ModuleType,
) -> None:
    error = parse_log_mod.parse_log(UNRECOGNISED_ERROR)

    assert error is not None
    assert error.line == 77
    assert "dimension too large" in error.message.lower(), (
        f"An unrecognised `! ` line keeps its own text as the summary, got {error.message!r}."
    )
    assert_one_sentence(error.message)


def test_an_unrecognised_error_without_a_line_marker_has_no_line(
    parse_log_mod: ModuleType,
) -> None:
    log = "This is Tectonic 0.17.0\n! I do not like this document.\nNo pages of output.\n"
    error = parse_log_mod.parse_log(log)

    assert error is not None
    assert error.line is None, "No l.NNN marker means no line, not line 0 and not a guess."
    assert "do not like this document" in error.message.lower()


# ─── Clean logs ───────────────────────────────────────────────────────────────


def test_a_clean_log_has_no_error(parse_log_mod: ModuleType) -> None:
    assert parse_log_mod.parse_log(CLEAN_LOG) is None


def test_warnings_and_overfull_boxes_are_not_errors(parse_log_mod: ModuleType) -> None:
    """Every real resume compile emits these. Treating them as failures would fail every run."""
    log = (
        "Overfull \\hbox (12.48pt too wide) in paragraph at lines 45--47\n"
        "Underfull \\vbox (badness 10000) has occurred while \\output is active\n"
        "LaTeX Warning: Reference `sec:skills' on page 1 undefined on input line 52.\n"
        "LaTeX Font Warning: Font shape `T1/bch/bx/sc' undefined on input line 12.\n"
        "Writing `resume.pdf` (1 page, 20134 bytes)\n"
    )
    assert parse_log_mod.parse_log(log) is None


def test_an_empty_log_has_no_error(parse_log_mod: ModuleType) -> None:
    assert parse_log_mod.parse_log("") is None


def test_an_exclamation_mark_inside_prose_is_not_an_error(parse_log_mod: ModuleType) -> None:
    """`! ` must be at the start of a line. `End of file on the terminal!` is not an error line."""
    log = "Running TeX ...\nThe word Hooray! appears in the resume.\n[1]\n"
    assert parse_log_mod.parse_log(log) is None


# ─── page_count ───────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("log", "expected"),
    [
        ("Writing `resume.pdf` (2 pages, 78432 bytes)\n", 2),
        ("Writing 'resume.pdf' (3 pages)\n", 3),
        ("Writing `resume.pdf` (1 page, 20134 bytes)\n", 1),
        ("Output written on resume.pdf (2 pages, 45678 bytes).\n", 2),
        ("Output written on resume.pdf (11 pages, 145678 bytes).\n", 11),
    ],
    ids=["tectonic_backticks", "contract_quotes", "singular_page", "pdflatex", "two_digits"],
)
def test_page_count_reads_the_written_page_total(
    parse_log_mod: ModuleType, log: str, expected: int
) -> None:
    assert parse_log_mod.page_count(log) == expected


def test_page_count_reads_a_full_successful_log(parse_log_mod: ModuleType) -> None:
    assert parse_log_mod.page_count(CLEAN_LOG) == 2


def test_page_count_is_none_when_the_log_never_wrote_a_pdf(parse_log_mod: ModuleType) -> None:
    assert parse_log_mod.page_count(MISSING_STY_FILE) is None


def test_page_count_is_none_for_an_empty_log(parse_log_mod: ModuleType) -> None:
    assert parse_log_mod.page_count("") is None


def test_page_count_ignores_a_page_number_in_prose(parse_log_mod: ModuleType) -> None:
    log = "LaTeX Warning: Reference `sec:x' on page 1 undefined on input line 52.\n[1] [2]\n"
    assert parse_log_mod.page_count(log) is None


# ─── Shape ────────────────────────────────────────────────────────────────────


def test_tex_error_is_frozen(parse_log_mod: ModuleType) -> None:
    error = parse_log_mod.parse_log(UNDEFINED_CONTROL_SEQUENCE)

    assert error is not None
    with pytest.raises(Exception):  # noqa: B017 - FrozenInstanceError is a dataclass detail
        error.line = 1
