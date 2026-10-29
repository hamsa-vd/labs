"""`resume_pipeline.storage.paths` (WP3 §5, acceptance criterion 7).

`document_path` is the only place a storage path is constructed, which makes it the first of two
gates between a request body and the filesystem. Its job is not to build a pretty path; its job is
to refuse to build one at all unless every segment is a UUID (or the literal `_` standing in for a
run that does not exist yet). That refusal is what makes the shape
`{user_id}/{application_id}/{run_id or "_"}/{kind}{ext}` safe to join onto a root directory.

The traversal cases below are the ones that matter in the order they matter: a segment that is
simply `..`, a UUID with traversal glued on, an absolute path, and the URL-encoded and
backslash-separated variants that a naive check misses.
"""

from __future__ import annotations

import importlib
import uuid
from typing import Any

import pytest

from resume_pipeline.errors import ValidationFailed

PATHS_MODULE = "resume_pipeline.storage.paths"

KINDS = (
    "resume_tex",
    "resume_pdf",
    "cover_letter_tex",
    "cover_letter_pdf",
    "jd",
    "imported_resume",
    "template_preview",
)

# The extensions the contract names explicitly. `imported_resume` is deliberately absent: the
# contract does not say what it is, so this suite only requires that it has *an* extension.
NAMED_EXTENSIONS = {
    "resume_tex": ".tex",
    "resume_pdf": ".pdf",
    "cover_letter_tex": ".tex",
    "cover_letter_pdf": ".pdf",
    "jd": ".txt",
    "template_preview": ".png",
}

USER = "11111111-1111-4111-8111-111111111111"
APPLICATION = "22222222-2222-4222-8222-222222222222"
RUN = "33333333-3333-4333-8333-333333333333"

# Every one of these is a segment that must never survive into a path.
HOSTILE_SEGMENTS = [
    "..",
    "../..",
    "../../etc/passwd",
    f"{USER}/..",
    f"{USER}/../{APPLICATION}",
    "/etc/passwd",
    "/",
    "",
    "   ",
    "not-a-uuid",
    "11111111-1111-4111-8111-11111111111",  # one character short
    f"{USER}\x00",
    f"{USER}\n",
    f"{USER} ",
    "..%2f..%2fetc%2fpasswd",
    "..\\..\\windows",
    "~/.ssh/id_rsa",
    "$HOME",
    "*",
]


@pytest.fixture(scope="module")
def paths() -> Any:
    try:
        return importlib.import_module(PATHS_MODULE)
    except ModuleNotFoundError as exc:  # pragma: no cover - only before WP3 source lands
        pytest.fail(f"WP3 has not provided `{PATHS_MODULE}` yet ({exc}).", pytrace=False)


# ─── The tables ───────────────────────────────────────────────────────────────


def test_every_kind_has_an_extension(paths: Any) -> None:
    for kind in KINDS:
        assert kind in paths.EXTENSIONS, f"no extension for {kind}"
        extension = paths.EXTENSIONS[kind]
        assert extension.startswith("."), f"{kind} extension is not dotted: {extension!r}"
        assert len(extension) > 1


@pytest.mark.parametrize(("kind", "extension"), sorted(NAMED_EXTENSIONS.items()))
def test_named_extensions_match_the_contract(paths: Any, kind: str, extension: str) -> None:
    assert paths.EXTENSIONS[kind] == extension


def test_every_kind_has_a_content_type(paths: Any) -> None:
    for kind in KINDS:
        assert kind in paths.CONTENT_TYPES, f"no content type for {kind}"
        content_type = paths.CONTENT_TYPES[kind]
        assert "/" in content_type, f"{kind} content type is not a media type: {content_type!r}"


def test_pdf_and_preview_content_types(paths: Any) -> None:
    assert paths.CONTENT_TYPES["resume_pdf"] == "application/pdf"
    assert paths.CONTENT_TYPES["cover_letter_pdf"] == "application/pdf"
    assert paths.CONTENT_TYPES["template_preview"] == "image/png"


# The contract fixes the extensions but not the media types beyond what the kinds imply, so the
# `.tex` and `.txt` types are only required to be servable media types (checked above). Whether a
# `.tex` file is `text/plain`, `text/x-tex` or `application/x-tex` is an open question for review.


# ─── The happy path ───────────────────────────────────────────────────────────


@pytest.mark.parametrize("kind", KINDS)
def test_path_shape(paths: Any, kind: str) -> None:
    built = paths.document_path(USER, APPLICATION, RUN, kind)
    assert built == f"{USER}/{APPLICATION}/{RUN}/{kind}{paths.EXTENSIONS[kind]}"


@pytest.mark.parametrize("kind", KINDS)
def test_a_missing_run_becomes_an_underscore_segment(paths: Any, kind: str) -> None:
    built = paths.document_path(USER, APPLICATION, None, kind)
    assert built == f"{USER}/{APPLICATION}/_/{kind}{paths.EXTENSIONS[kind]}"


def test_the_literal_underscore_is_accepted_as_a_run_id(paths: Any) -> None:
    assert paths.document_path(USER, APPLICATION, "_", "jd").split("/")[2] == "_"


def test_a_generated_uuid_round_trips(paths: Any) -> None:
    user, application, run = (str(uuid.uuid4()) for _ in range(3))
    built = paths.document_path(user, application, run, "resume_pdf")
    assert built.split("/") == [user, application, run, "resume_pdf.pdf"]


@pytest.mark.parametrize("kind", KINDS)
def test_a_built_path_is_relative_and_traversal_free(paths: Any, kind: str) -> None:
    built = paths.document_path(USER, APPLICATION, RUN, kind)
    assert not built.startswith("/")
    assert ".." not in built
    assert "\\" not in built
    assert "\x00" not in built
    assert len(built.split("/")) == 4


# ─── Criterion 7, first half: every segment is validated ──────────────────────


@pytest.mark.parametrize("hostile", HOSTILE_SEGMENTS)
def test_a_hostile_user_id_is_rejected(paths: Any, hostile: str) -> None:
    with pytest.raises(ValidationFailed):
        paths.document_path(hostile, APPLICATION, RUN, "resume_tex")


@pytest.mark.parametrize("hostile", HOSTILE_SEGMENTS)
def test_a_hostile_application_id_is_rejected(paths: Any, hostile: str) -> None:
    with pytest.raises(ValidationFailed):
        paths.document_path(USER, hostile, RUN, "resume_tex")


@pytest.mark.parametrize("hostile", HOSTILE_SEGMENTS)
def test_a_hostile_run_id_is_rejected(paths: Any, hostile: str) -> None:
    with pytest.raises(ValidationFailed):
        paths.document_path(USER, APPLICATION, hostile, "resume_tex")


def test_an_unknown_kind_is_rejected(paths: Any) -> None:
    with pytest.raises(ValidationFailed):
        paths.document_path(USER, APPLICATION, RUN, "shell_script")


def test_rejection_does_not_echo_the_hostile_value_verbatim(paths: Any) -> None:
    """The error goes to a user; it says what was wrong, not what the attacker sent."""
    with pytest.raises(ValidationFailed) as excinfo:
        paths.document_path("../../etc/passwd", APPLICATION, RUN, "jd")
    assert "/etc/passwd" not in str(excinfo.value)
