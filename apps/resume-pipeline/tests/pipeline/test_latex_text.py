"""LaTeX to ATS-visible prose (WP2 §6).

`tex_to_text` is the shared reduction used by the ATS service and the import service. The bar
it has to clear is acceptance criterion 5: a .tex resume and its plain-text equivalent score
within 2 ATS points. That is asserted in `tests/services/test_ats_service.py`; this module pins
the individual transformations that make it true.
"""

from __future__ import annotations

import re

import pytest

from resume_pipeline.pipeline.latex_text import tex_to_text

ATS_BULLET_LINE = re.compile(r"^\s*[\-•◦▸*]\s+(.+)$")


# ─── Preamble ─────────────────────────────────────────────────────────────────


def test_the_preamble_is_dropped_when_begin_document_is_present() -> None:
    tex = (
        "\\documentclass[letterpaper,11pt]{article}\n"
        "\\usepackage{geometry}\n"
        "\\newcommand{\\resumeItem}[1]{#1}\n"
        "\\begin{document}\n"
        "Real prose here.\n"
        "\\end{document}\n"
    )
    text = tex_to_text(tex)
    assert "Real prose here." in text
    assert "documentclass" not in text
    assert "usepackage" not in text
    assert "geometry" not in text
    assert "newcommand" not in text


def test_plain_text_without_a_preamble_passes_through() -> None:
    plain = "Jane Doe\n\nEXPERIENCE\n\n- Built an API that served 2 million requests."
    assert tex_to_text(plain).strip() == plain.strip()


def test_an_empty_document_returns_empty_text() -> None:
    assert tex_to_text("").strip() == ""


# ─── Comments ─────────────────────────────────────────────────────────────────


def test_a_whole_line_comment_is_dropped() -> None:
    text = tex_to_text("\\item Kept line.\n% dropped entirely\n\\item Another kept line.")
    assert "dropped entirely" not in text
    assert "Kept line." in text
    assert "Another kept line." in text


def test_a_trailing_comment_is_dropped_but_its_line_survives() -> None:
    text = tex_to_text("\\item Delivered the platform. % TODO reword this bullet")
    assert "Delivered the platform." in text
    assert "TODO" not in text


def test_a_percent_in_prose_is_a_percent_sign_not_a_comment() -> None:
    """Contract amended during WP2 reconciliation.

    An imported resume is pasted as prose, and the import flow scores it through
    this function. Treating a bare `%` as a comment there deletes the rest of the
    bullet -- and a bullet with a percentage in it is precisely the quantified
    achievement the ATS structural score rewards. Stripping is conditional on the
    input carrying an actual LaTeX signal.
    """
    prose = "Cut settlement latency by 45% across 12 services.\nGrew revenue 30% year on year."
    assert tex_to_text(prose).strip() == prose.strip()


def test_an_escaped_percent_is_not_treated_as_a_comment() -> None:
    text = tex_to_text("Cut latency by 45\\% across twelve services.")
    assert "Cut latency by 45% across twelve services." in text


def test_an_escaped_percent_survives_next_to_a_real_comment() -> None:
    text = tex_to_text("Grew revenue 30\\% year on year. % internal note")
    assert "Grew revenue 30% year on year." in text
    assert "internal note" not in text


# ─── Text macros ──────────────────────────────────────────────────────────────


@pytest.mark.parametrize("macro", ["textbf", "textit", "emph", "underline", "texttt"])
def test_a_text_macro_is_unwrapped_to_its_argument(macro: str) -> None:
    text = tex_to_text("Led the \\" + macro + "{payments platform} rebuild.")
    assert "Led the payments platform rebuild." in text
    assert macro not in text
    assert "{" not in text and "}" not in text


def test_href_keeps_the_label_and_drops_the_url() -> None:
    text = tex_to_text("\\href{https://www.linkedin.com/in/jane}{linkedin.com/in/jane}")
    assert "linkedin.com/in/jane" in text
    assert "https://www.linkedin.com/in/jane" not in text
    assert "href" not in text


def test_a_bold_section_heading_becomes_a_bare_line() -> None:
    text = tex_to_text("\\textbf{EXPERIENCE}\n\nLiv-ex, London")
    assert "EXPERIENCE" in text.splitlines()


# ─── Layout-only macros ───────────────────────────────────────────────────────


def test_layout_macros_and_their_arguments_are_dropped() -> None:
    tex = (
        "Before.\n"
        "\\vspace{-6pt}\n"
        "\\hspace{12pt}\n"
        "\\rule{\\linewidth}{0.4pt}\n"
        "After. \\hfill Right side.\n"
    )
    text = tex_to_text(tex)
    assert "Before." in text
    assert "After." in text
    assert "Right side." in text
    for residue in ("vspace", "hspace", "rule", "hfill", "linewidth", "0.4pt", "-6pt", "12pt"):
        assert residue not in text


def test_begin_and_end_markers_are_dropped() -> None:
    tex = "\\begin{itemize}\n\\item Shipped it.\n\\end{itemize}\n"
    text = tex_to_text(tex)
    assert "Shipped it." in text
    assert "itemize" not in text
    assert "begin" not in text
    assert "end{" not in text


# ─── Bullets ──────────────────────────────────────────────────────────────────


def test_each_item_becomes_its_own_line() -> None:
    tex = "\\begin{itemize}\n\\item First bullet.\n\\item Second bullet.\n\\end{itemize}\n"
    lines = [line.strip() for line in tex_to_text(tex).splitlines() if line.strip()]
    assert len(lines) == 2
    assert lines[0].endswith("First bullet.")
    assert lines[1].endswith("Second bullet.")
    assert "item" not in tex_to_text(tex)


def test_items_on_one_source_line_are_split_onto_separate_lines() -> None:
    tex = "\\begin{itemize}\\item One. \\item Two. \\item Three.\\end{itemize}"
    lines = [line.strip() for line in tex_to_text(tex).splitlines() if line.strip()]
    assert len(lines) == 3


def test_converted_items_are_countable_bullets_for_the_ats_structural_score() -> None:
    # The ATS structural score only counts lines that start with a bullet marker, and the
    # contract's reason for handling \item at all is that the structural score counts bullets.
    tex = (
        "\\begin{itemize}\n"
        "\\item Architected a Kafka pipeline that cut latency by 45\\%.\n"
        "\\item Migrated search to OpenSearch, cutting p95 from 2.5s to 250ms.\n"
        "\\end{itemize}\n"
    )
    bullets = [line for line in tex_to_text(tex).splitlines() if ATS_BULLET_LINE.match(line)]
    assert len(bullets) == 2


# ─── Escaped characters ───────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("escaped", "literal"),
    [("\\&", "&"), ("\\%", "%"), ("\\$", "$"), ("\\#", "#"), ("\\_", "_")],
)
def test_escaped_characters_become_literals(escaped: str, literal: str) -> None:
    text = tex_to_text(f"Johnson {escaped} Johnson")
    assert text.strip() == f"Johnson {literal} Johnson"


def test_several_escapes_in_one_line() -> None:
    text = tex_to_text("Cut cost by 30\\% saving \\$2M for R\\&D on user\\_ids \\#1.")
    assert "Cut cost by 30% saving $2M for R&D on user_ids #1." in text


# ─── Whitespace ───────────────────────────────────────────────────────────────


def test_long_runs_of_blank_lines_are_collapsed() -> None:
    # "collapse runs of three or more blank lines to two" — at most two blank lines survive,
    # which is at most three consecutive newlines.
    text = tex_to_text("First.\n\n\n\n\n\nSecond.\n\n\n\nThird.")
    assert "\n\n\n\n" not in text
    assert "First." in text and "Second." in text and "Third." in text


def test_two_blank_lines_are_not_collapsed_further() -> None:
    # "collapse runs of three or more blank lines to two" — a single blank line separator stays.
    assert tex_to_text("First.\n\nSecond.").strip() == "First.\n\nSecond."


def test_no_line_has_trailing_whitespace() -> None:
    tex = "Name   \n\\textbf{ROLE}  \t\nA bullet line.   \n"
    text = tex_to_text(tex)
    assert all(line == line.rstrip() for line in text.splitlines())


# ─── Whole document ───────────────────────────────────────────────────────────


def test_a_whole_resume_reduces_to_clean_prose(tex_resume: str) -> None:
    text = tex_to_text(tex_resume)
    for residue in (
        "\\documentclass",
        "\\usepackage",
        "\\begin{",
        "\\end{",
        "\\item",
        "\\textbf",
        "\\textit",
        "\\href",
        "\\vspace",
        "\\hspace",
        "\\rule",
        "\\hfill",
        "Layout tuning below",
        "Most recent role first",
    ):
        assert residue not in text
    for kept in (
        "Hamsa Vardhan",
        "SUMMARY",
        "SKILLS",
        "EXPERIENCE",
        "EDUCATION",
        "Software Engineer",
        "linkedin.com/in/hamsa-vardhan",
        "45%",
        "60%",
        "35%",
    ):
        assert kept in text
    assert "\n\n\n\n" not in text


def test_conversion_is_deterministic(tex_resume: str) -> None:
    assert tex_to_text(tex_resume) == tex_to_text(tex_resume)


def test_every_section_heading_survives_on_its_own_line(tex_resume: str) -> None:
    lines = [line.strip() for line in tex_to_text(tex_resume).splitlines()]
    for heading in ("SUMMARY", "SKILLS", "EXPERIENCE", "EDUCATION"):
        assert heading in lines
