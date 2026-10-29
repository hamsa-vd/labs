"""Storage path construction (RG-006).

This is the only place a storage path is built. That matters because every segment of the path
comes from an identifier that arrived over HTTP, and a path built from user input in two places
is a path validated in one of them.

Shape: `{user_id}/{application_id}/{run_id or "_"}/{kind}{ext}`.

Each segment is checked against a strict UUID pattern *before* the join, so `..`, a leading `/`,
a `%2e%2e`, a `urn:uuid:` form and a Windows drive letter all fail at the same gate rather than
being caught downstream by a containment check that somebody might one day refactor away.
`LocalBlobStore` performs that containment check anyway — two layers, because this is the path
that reaches the disk.
"""

from __future__ import annotations

import re
from typing import Literal, get_args

from resume_pipeline.errors import ValidationFailed

DocumentKind = Literal[
    "resume_tex",
    "resume_pdf",
    "cover_letter_tex",
    "cover_letter_pdf",
    "jd",
    "imported_resume",
    "template_preview",
]

DOCUMENT_KINDS: tuple[DocumentKind, ...] = get_args(DocumentKind)

#: The run segment when a document does not belong to a run — a job description attached to an
#: application, an imported resume, a template preview.
NO_RUN_SEGMENT = "_"

EXTENSIONS: dict[DocumentKind, str] = {
    "resume_tex": ".tex",
    "resume_pdf": ".pdf",
    "cover_letter_tex": ".tex",
    "cover_letter_pdf": ".pdf",
    "jd": ".txt",
    "imported_resume": ".pdf",
    "template_preview": ".png",
}

CONTENT_TYPES: dict[DocumentKind, str] = {
    "resume_tex": "application/x-tex",
    "resume_pdf": "application/pdf",
    "cover_letter_tex": "application/x-tex",
    "cover_letter_pdf": "application/pdf",
    "jd": "text/plain; charset=utf-8",
    "imported_resume": "application/pdf",
    "template_preview": "image/png",
}

_UUID_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)

_BAD_SEGMENT = (
    "That document path is not valid because one of its identifiers is not a UUID. "
    "Check the identifier and try again."
)


def is_uuid(value: str) -> bool:
    return bool(_UUID_PATTERN.match(value))


def validate_segment(value: str, *, field: str, allow_placeholder: bool = False) -> str:
    if allow_placeholder and value == NO_RUN_SEGMENT:
        return value
    if not isinstance(value, str) or not is_uuid(value):
        raise ValidationFailed(_BAD_SEGMENT, details={"field": field})
    return value


def validate_kind(kind: str) -> DocumentKind:
    if kind not in EXTENSIONS:
        raise ValidationFailed(
            "That document kind is not one this service stores. Use a supported kind and try again.",
            details={"field": "kind"},
        )
    return kind


def extension_for(kind: str) -> str:
    return EXTENSIONS[validate_kind(kind)]


def content_type_for(kind: str) -> str:
    return CONTENT_TYPES[validate_kind(kind)]


def document_path(
    user_id: str, application_id: str, run_id: str | None, kind: DocumentKind
) -> str:
    checked_kind = validate_kind(kind)
    segments = [
        validate_segment(user_id, field="user_id"),
        validate_segment(application_id, field="application_id"),
        validate_segment(
            run_id if run_id is not None else NO_RUN_SEGMENT,
            field="run_id",
            allow_placeholder=True,
        ),
    ]
    return "/".join(segments) + f"/{checked_kind}{EXTENSIONS[checked_kind]}"
