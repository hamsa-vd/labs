"""The macro denylist and structural validator (WP7 §1, RG-021, RG-035).

This is the security boundary. The `.tex` reaching `validate_tex` is user input, and `\\write18`,
`\\input{/etc/passwd}` and `\\openout` are real escapes, so a scanner that is merely decorative is
worse than none — it produces confidence without protection.

Three properties are asserted here and each one is load-bearing:

* **Every denied construct is rejected, at the right line.** A rejection without a line number
  sends the user hunting through a 200-line preamble.
* **The scanner is honest about TeX syntax.** A construct inside a comment is inert and must not
  be rejected; `\\%` is a literal percent and does *not* start a comment, so what follows it is
  live code; whitespace and newlines between a control sequence and its argument are invisible to
  TeX and must be invisible to the scanner too.
* **Every problem is reported at once.** RG-021 calls this out: a user fixing one rejection per
  round trip is the experience the rule exists to prevent.
"""

from __future__ import annotations

from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from tests.latex.conftest import seed_template_paths

# A structurally valid document with a single free line for a payload.
#
#   1  \documentclass[11pt]{article}
#   2  \begin{document}
#   3  Resume body.
#   4  <payload>
#   5  \end{document}
PAYLOAD_LINE = 4

VALID_TEX = "\\documentclass[11pt]{article}\n\\begin{document}\nResume body.\n\\end{document}\n"


def tex_with(payload: str) -> str:
    """A valid document whose only unusual content is `payload`, starting at `PAYLOAD_LINE`."""
    return (
        "\\documentclass[11pt]{article}\n"
        "\\begin{document}\n"
        "Resume body.\n"
        f"{payload}\n"
        "\\end{document}\n"
    )


def lines_of(problems: list[Any]) -> set[int]:
    return {problem.line for problem in problems}


def messages_of(problems: list[Any]) -> str:
    return " ".join(problem.message for problem in problems).lower()


def normalise(text: str) -> str:
    """Lowercase and strip backslashes, so `\\ShellEscape` and `shellescape` compare equal."""
    return text.lower().replace("\\", "").replace(" ", "")


# ─── The denylist ─────────────────────────────────────────────────────────────

# (id, payload, a token the message must name). One entry per construct in the contract's list.
DENIED_CONSTRUCTS: list[tuple[str, str, str]] = [
    ("write18", r"\write18{echo owned}", "write18"),
    ("immediate_write18", r"\immediate\write18{echo owned}", "write18"),
    ("input_absolute_path", r"\input{/etc/passwd}", "input"),
    ("input_parent_traversal", r"\input{../../etc/passwd}", "input"),
    ("include_absolute_path", r"\include{/etc/shadow}", "include"),
    ("include_parent_traversal", r"\include{../../outside/secret}", "include"),
    ("openout_stream", r"\openout15=/tmp/exfiltrated.txt", "openout"),
    ("openin_stream", r"\openin1=/etc/passwd", "openin"),
    ("read_stream", r"\read1 to \stolen", "read"),
    ("write_stream", r"\write15{leaked}", "write"),
    ("immediate_write_stream", r"\immediate\write15{leaked}", "write"),
    ("catcode_backslash", r"\catcode`\\=12", "catcode"),
    ("catcode_open_brace", r"\catcode`\{=12", "catcode"),
    ("catcode_close_brace", r"\catcode`\}=12", "catcode"),
    ("usepackage_shellesc", r"\usepackage{shellesc}", "shellesc"),
    ("shell_escape_macro", r"\ShellEscape{rm -rf /}", "shellescape"),
    ("directlua", r'\directlua{os.execute("id")}', "directlua"),
    ("special_dvipdfmx", r"\special{dvipdfmx:command sh -c id}", "special"),
    ("special_shell_invocation", r'\special{! /bin/sh -c "id"}', "special"),
]

DENIED_IDS = [case[0] for case in DENIED_CONSTRUCTS]
DENIED_PAYLOADS = [case[1] for case in DENIED_CONSTRUCTS]


@pytest.mark.parametrize("payload", DENIED_PAYLOADS, ids=DENIED_IDS)
def test_a_denied_construct_is_rejected_at_its_line(validate_mod: ModuleType, payload: str) -> None:
    problems = validate_mod.validate_tex(tex_with(payload))

    assert problems, f"{payload!r} was accepted; it is on the contract's denied list."
    assert lines_of(problems) == {PAYLOAD_LINE}, (
        f"{payload!r} must be reported at line {PAYLOAD_LINE}, "
        f"got {sorted(lines_of(problems))}. The document is otherwise valid."
    )


@pytest.mark.parametrize(
    ("payload", "token"), [(c[1], c[2]) for c in DENIED_CONSTRUCTS], ids=DENIED_IDS
)
def test_a_rejection_message_names_the_line_and_the_construct(
    validate_mod: ModuleType, payload: str, token: str
) -> None:
    problems = validate_mod.validate_tex(tex_with(payload))
    assert problems

    joined = messages_of(problems)
    assert f"line {PAYLOAD_LINE}" in joined, f"The message must name the line, got {joined!r}."
    assert token in normalise(joined), f"The message must name the construct, got {joined!r}."
    assert "!" not in joined, "Copy rule: no exclamation marks."


def test_a_construct_deep_in_the_file_reports_its_own_line(validate_mod: ModuleType) -> None:
    """The contract's own example: line 40, not line 1 and not the count of problems."""
    body = ["\\documentclass[11pt]{article}"]
    body += [f"% preamble filler {n}" for n in range(2, 39)]
    body.append("\\begin{document}")  # line 39
    body.append(r"\write18{echo owned}")  # line 40
    body.append("\\end{document}")  # line 41
    tex = "\n".join(body) + "\n"

    problems = validate_mod.validate_tex(tex)

    assert lines_of(problems) == {40}
    assert "line 40" in messages_of(problems)


# ─── Comments are inert ───────────────────────────────────────────────────────


@pytest.mark.parametrize("payload", DENIED_PAYLOADS, ids=DENIED_IDS)
def test_a_denied_construct_inside_a_whole_line_comment_is_not_a_problem(
    validate_mod: ModuleType, payload: str
) -> None:
    """TeX never sees it, so neither should the user see a rejection."""
    assert validate_mod.validate_tex(tex_with(f"% {payload}")) == []


@pytest.mark.parametrize("payload", DENIED_PAYLOADS, ids=DENIED_IDS)
def test_a_denied_construct_in_a_trailing_comment_is_not_a_problem(
    validate_mod: ModuleType, payload: str
) -> None:
    assert validate_mod.validate_tex(tex_with(f"Delivered the platform. % {payload}")) == []


def test_a_comment_does_not_suppress_the_following_line(validate_mod: ModuleType) -> None:
    """A comment ends at the newline. The next line is live code again."""
    tex = (
        "\\documentclass[11pt]{article}\n"
        "\\begin{document}\n"
        "% \\write18{harmless, commented out}\n"
        "\\write18{echo owned}\n"
        "\\end{document}\n"
    )
    assert lines_of(validate_mod.validate_tex(tex)) == {4}


# ─── An escaped percent is not a comment ──────────────────────────────────────


def test_an_escaped_percent_does_not_start_a_comment(validate_mod: ModuleType) -> None:
    r"""`\%` is a literal percent character. Everything after it on the line is still live."""
    problems = validate_mod.validate_tex(tex_with(r"Cut latency by 40\% and \write18{echo owned}"))

    assert problems, r"`\%` does not start a comment, so the \write18 after it is live code."
    assert lines_of(problems) == {PAYLOAD_LINE}


@pytest.mark.parametrize("payload", DENIED_PAYLOADS, ids=DENIED_IDS)
def test_an_escaped_percent_before_a_real_comment_still_comments(
    validate_mod: ModuleType, payload: str
) -> None:
    r"""`\%` is literal, but the *next* unescaped `%` does open a comment."""
    assert validate_mod.validate_tex(tex_with(rf"Cut costs by 40\% % {payload}")) == []


def test_a_double_backslash_before_a_percent_leaves_the_percent_live(
    validate_mod: ModuleType,
) -> None:
    r"""`\\` is a line break, so the `%` after it is unescaped and does open a comment."""
    assert validate_mod.validate_tex(tex_with(r"End of line \\% \write18{commented}")) == []


# ─── Whitespace and newlines do not hide a construct ──────────────────────────


@pytest.mark.parametrize(
    ("payload", "label"),
    [
        (r"\write 18{echo owned}", "space before the stream number"),
        ("\\write\t18{echo owned}", "tab before the stream number"),
        (r"\input {/etc/passwd}", "space before the brace"),
        (r"\usepackage  {shellesc}", "two spaces before the brace"),
        (r"\immediate \write18{echo owned}", "space inside the prefix"),
        (r"\catcode `\\=12", "space before the character literal"),
    ],
)
def test_whitespace_between_the_control_sequence_and_its_argument_still_trips(
    validate_mod: ModuleType, payload: str, label: str
) -> None:
    problems = validate_mod.validate_tex(tex_with(payload))

    assert problems, f"Evaded by {label}: TeX ignores that whitespace and so must the scanner."
    assert lines_of(problems) == {PAYLOAD_LINE}


@pytest.mark.parametrize(
    ("payload", "label"),
    [
        ("\\write\n18{echo owned}", "newline before the stream number"),
        ("\\input\n{/etc/passwd}", "newline before the brace"),
        ("\\usepackage\n  {shellesc}", "newline and indent before the brace"),
        ("\\immediate\n\\write18{echo owned}", "newline inside the prefix"),
        ("\\catcode\n`\\\\=12", "newline before the character literal"),
    ],
)
def test_a_newline_between_the_control_sequence_and_its_argument_still_trips(
    validate_mod: ModuleType, payload: str, label: str
) -> None:
    """The construct spans lines 4 and 5, so either is a defensible line to report — but it
    must be reported, and it must not be attributed to some unrelated line."""
    problems = validate_mod.validate_tex(tex_with(payload))

    assert problems, f"Evaded by a {label}: TeX ignores it and so must the scanner."
    assert lines_of(problems) <= {PAYLOAD_LINE, PAYLOAD_LINE + 1}
    assert PAYLOAD_LINE in lines_of(problems) or PAYLOAD_LINE + 1 in lines_of(problems)


# ─── False positives ──────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("payload", "why"),
    [
        (r"\usepackage[utf8]{inputenc}", "every seeded template loads inputenc"),
        (r"\inputencoding{utf8}", "a longer control sequence is not \\input"),
        (r"\includegraphics[width=1cm]{logo.png}", "\\includegraphics is not \\include"),
        (r"\input{sections/skills.tex}", "a relative path with no traversal is allowed"),
        (r"\include{sections/education}", "a relative include with no traversal is allowed"),
        (r"\newcommand{\writeup}[1]{#1}", "\\writeup is not \\write to a stream"),
        (r"\catcode`\_=12", "underscore is not a backslash or a brace"),
        (r"\special{color push rgb 0 0 0}", "a colour special invokes no shell"),
        (r"Reported a 40\% reduction in p95 latency.", "an escaped percent is ordinary prose"),
        (r"The file is at ../docs/readme, per the brief.", "`..` in prose is not a traversal"),
    ],
)
def test_ordinary_latex_is_not_rejected(validate_mod: ModuleType, payload: str, why: str) -> None:
    assert validate_mod.validate_tex(tex_with(payload)) == [], f"False positive: {why}."


def test_a_minimal_valid_document_has_no_problems(validate_mod: ModuleType) -> None:
    assert validate_mod.validate_tex(VALID_TEX) == []


def test_the_shared_tex_resume_fixture_validates(validate_mod: ModuleType, tex_resume: str) -> None:
    assert validate_mod.validate_tex(tex_resume) == []


@pytest.mark.parametrize("template", seed_template_paths(), ids=lambda p: p.stem)
def test_every_seeded_template_validates(validate_mod: ModuleType, template: Path) -> None:
    """The ten shipped templates are the ground truth for "ordinary". If the denylist rejects
    one of them, the denylist is wrong, not the template."""
    problems = validate_mod.validate_tex(template.read_text(encoding="utf-8"))
    assert problems == [], f"{template.name} was rejected: {[p.message for p in problems]}"


# ─── Structural requirements ──────────────────────────────────────────────────


def test_a_missing_documentclass_is_a_document_level_problem(validate_mod: ModuleType) -> None:
    tex = "\\begin{document}\nResume body.\n\\end{document}\n"
    problems = validate_mod.validate_tex(tex)

    assert len(problems) == 1
    assert problems[0].line == 0, "A missing declaration is about the document as a whole."
    assert "documentclass" in normalise(problems[0].message)


def test_a_missing_begin_document_is_a_document_level_problem(validate_mod: ModuleType) -> None:
    tex = "\\documentclass[11pt]{article}\nResume body.\n\\end{document}\n"
    problems = validate_mod.validate_tex(tex)

    assert len(problems) == 1
    assert problems[0].line == 0
    assert "begin{document}" in normalise(problems[0].message)


def test_a_missing_end_document_is_a_document_level_problem(validate_mod: ModuleType) -> None:
    tex = "\\documentclass[11pt]{article}\n\\begin{document}\nResume body.\n"
    problems = validate_mod.validate_tex(tex)

    assert len(problems) == 1
    assert problems[0].line == 0
    assert "end{document}" in normalise(problems[0].message)


def test_an_empty_document_reports_all_three_structural_problems(validate_mod: ModuleType) -> None:
    problems = validate_mod.validate_tex("")

    assert len(problems) == 3
    assert lines_of(problems) == {0}


def test_every_problem_message_is_a_sentence_without_an_exclamation_mark(
    validate_mod: ModuleType,
) -> None:
    """Copy rule: sentence case, second person, no exclamation marks, say what to do."""
    problems = validate_mod.validate_tex("Nothing structural here at all.\n")

    assert problems
    for problem in problems:
        assert problem.message, "A problem with no message tells the user nothing."
        assert "!" not in problem.message
        assert problem.message.strip().endswith("."), problem.message
        assert "\n" not in problem.message


# ─── Every problem at once ────────────────────────────────────────────────────


def test_three_distinct_problems_are_all_reported(validate_mod: ModuleType) -> None:
    """RG-021. Returning only the first rejection makes the user fix one thing per round trip."""
    tex = (
        "\\documentclass[11pt]{article}\n"  # 1
        "\\begin{document}\n"  # 2
        "\\write18{echo owned}\n"  # 3  denied
        "Resume body.\n"  # 4
        "\\input{../../etc/passwd}\n"  # 5  denied
        "Trailing prose with no end of document.\n"  # 6
    )

    problems = validate_mod.validate_tex(tex)

    assert lines_of(problems) == {0, 3, 5}, (
        "Expected a missing \\end{document} at line 0, a \\write18 at line 3 and a traversing "
        f"\\input at line 5, got {sorted(lines_of(problems))}."
    )
    joined = normalise(messages_of(problems))
    assert "write18" in joined
    assert "input" in joined
    assert "end{document}" in joined


def test_repeated_occurrences_of_one_construct_are_each_reported(validate_mod: ModuleType) -> None:
    tex = (
        "\\documentclass[11pt]{article}\n"  # 1
        "\\begin{document}\n"  # 2
        "\\write18{first}\n"  # 3
        "Resume body.\n"  # 4
        "\\write18{second}\n"  # 5
        "\\end{document}\n"  # 6
    )
    assert lines_of(validate_mod.validate_tex(tex)) == {3, 5}


# ─── Size ─────────────────────────────────────────────────────────────────────


def test_max_tex_bytes_is_two_hundred_kilobytes(validate_mod: ModuleType) -> None:
    assert validate_mod.MAX_TEX_BYTES == 200 * 1024


def _tex_of_exactly(n_bytes: int) -> str:
    """A valid document padded with comment lines to exactly `n_bytes` UTF-8 bytes."""
    head = "\\documentclass[11pt]{article}\n\\begin{document}\nResume body.\n"
    tail = "\\end{document}\n"
    padding = n_bytes - len(head.encode("utf-8")) - len(tail.encode("utf-8"))
    assert padding >= 2
    return head + "%" + ("a" * (padding - 2)) + "\n" + tail


def test_a_document_at_exactly_the_limit_is_accepted(validate_mod: ModuleType) -> None:
    tex = _tex_of_exactly(validate_mod.MAX_TEX_BYTES)
    assert len(tex.encode("utf-8")) == validate_mod.MAX_TEX_BYTES
    assert validate_mod.validate_tex(tex) == []


def test_a_document_over_the_limit_is_a_problem_at_line_zero(validate_mod: ModuleType) -> None:
    tex = _tex_of_exactly(validate_mod.MAX_TEX_BYTES + 1)
    problems = validate_mod.validate_tex(tex)

    assert problems, "A source over MAX_TEX_BYTES must be rejected before it reaches Tectonic."
    assert 0 in lines_of(problems), "A size problem is about the document as a whole."


def test_the_limit_counts_bytes_not_characters(validate_mod: ModuleType) -> None:
    """`MAX_TEX_BYTES` is bytes. A document of half that many em dashes is over the limit."""
    count = (validate_mod.MAX_TEX_BYTES // 3) + 10
    tex = (
        "\\documentclass[11pt]{article}\n"
        "\\begin{document}\n" + ("—" * count) + "\n\\end{document}\n"
    )
    assert len(tex) < validate_mod.MAX_TEX_BYTES
    assert len(tex.encode("utf-8")) > validate_mod.MAX_TEX_BYTES

    assert 0 in lines_of(validate_mod.validate_tex(tex))


# ─── assert_valid_tex ─────────────────────────────────────────────────────────


def test_assert_valid_tex_returns_none_for_a_valid_document(validate_mod: ModuleType) -> None:
    assert validate_mod.assert_valid_tex(VALID_TEX) is None


def test_assert_valid_tex_raises_validation_failed_with_every_problem(
    validate_mod: ModuleType,
) -> None:
    from resume_pipeline.errors import ValidationFailed

    tex = tex_with(r"\write18{echo owned}")

    with pytest.raises(ValidationFailed) as caught:
        validate_mod.assert_valid_tex(tex)

    error = caught.value
    assert error.code == "validation_failed"
    assert error.status == 422
    assert "problems" in error.details, "The contract names `details.problems`."
    assert len(error.details["problems"]) == len(validate_mod.validate_tex(tex))
    assert "!" not in error.message


def test_assert_valid_tex_carries_all_three_problems_through(validate_mod: ModuleType) -> None:
    from resume_pipeline.errors import ValidationFailed

    tex = (
        "\\documentclass[11pt]{article}\n"
        "\\begin{document}\n"
        "\\write18{echo owned}\n"
        "Resume body.\n"
        "\\input{../../etc/passwd}\n"
    )

    with pytest.raises(ValidationFailed) as caught:
        validate_mod.assert_valid_tex(tex)

    assert len(caught.value.details["problems"]) == 3


def test_a_rejection_never_echoes_the_resume_body(validate_mod: ModuleType) -> None:
    """Secrets rule: an error message must not carry the document back out with it."""
    from resume_pipeline.errors import ValidationFailed

    secret = "Architected a Kafka pipeline for Liv-ex settlement"
    tex = tex_with(f"{secret} \\write18{{echo owned}}")

    with pytest.raises(ValidationFailed) as caught:
        validate_mod.assert_valid_tex(tex)

    assert secret not in caught.value.message
    assert secret not in str(caught.value)
