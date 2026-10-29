"""Applications: the one table the tracker and the generator share (RG-020, A1).

Every query carries `user_id = $n`. Ascend holds the Cloudflare Access identity and asserts it on
each call, and this service trusts that assertion — but a bug in ascend must not become a
cross-tenant read, so the predicate is here too and is not optional.

A read that finds nothing raises `NotFound`. It never raises `Forbidden` and never returns an
empty row for "exists, but not yours": those two answers differ, and the difference is enough to
enumerate other people's application ids.
"""

from __future__ import annotations

import base64
import binascii
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from resume_pipeline.errors import NotFound, ValidationFailed
from resume_pipeline.util.slug import slugify

_COLUMNS = """
    id, user_id, company_norm, company_display, company_slug,
    role_title, role_norm, role_slug, source, origin, job_url, note,
    first_seen_at, current_status, status_as_of, archived,
    jd_text, jd_source_type, jd_url,
    round_count, current_round, next_action, applied_at,
    derived_from, migrated_from, created_at, updated_at
"""

_NOT_FOUND = "That application was not found. Check the application and try again."

#: Mirrors ascend's `src/domain/normalization.ts::normalizeEntity`. The trigram dedup index in
#: migration 0001 compares `company_norm` across rows written by both services, so the two
#: implementations have to agree character for character or ascend stops recognising its own
#: applications after the generator creates one.
_LEGAL_SUFFIXES = re.compile(r"\b(?:ltd|limited|inc|llc|gmbh|plc|group|company|co)\b", re.IGNORECASE)
_NON_ALNUM = re.compile(r"[^\w\d]+|_+", re.UNICODE)

#: Fields `update_tracking` will write. Anything else is refused rather than silently ignored,
#: because a typo'd field name that is quietly dropped looks exactly like a saved edit.
TRACKING_FIELDS: frozenset[str] = frozenset(
    {
        "current_status",
        "current_round",
        "round_count",
        "next_action",
        "applied_at",
        "archived",
        "note",
        "job_url",
        "jd_text",
        "jd_source_type",
        "jd_url",
        "derived_from",
    }
)

DEFAULT_LIMIT = 50
MAX_LIMIT = 200


@dataclass(frozen=True)
class ApplicationRow:
    id: str
    user_id: str
    company_norm: str
    company_display: str
    company_slug: str | None
    role_title: str | None
    role_norm: str | None
    role_slug: str | None
    source: str | None
    origin: str
    job_url: str | None
    note: str | None
    first_seen_at: datetime
    current_status: str
    status_as_of: datetime
    archived: bool
    # `repr=False`: a job description must never reach a log line or a traceback by accident.
    jd_text: str | None = field(repr=False, default=None)
    jd_source_type: str | None = None
    jd_url: str | None = None
    round_count: int = 0
    current_round: str | None = None
    next_action: str | None = None
    applied_at: datetime | None = None
    derived_from: str | None = None
    migrated_from: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


def normalize_entity(value: str) -> str:
    folded = unicodedata.normalize("NFKC", value).lower()
    stripped = _LEGAL_SUFFIXES.sub("", folded)
    collapsed = _NON_ALNUM.sub(" ", stripped)
    return " ".join(collapsed.split())


def _row(record: Any) -> ApplicationRow:
    data = dict(record)
    return ApplicationRow(
        id=str(data["id"]),
        user_id=str(data["user_id"]),
        company_norm=data["company_norm"],
        company_display=data["company_display"],
        company_slug=data["company_slug"],
        role_title=data["role_title"],
        role_norm=data["role_norm"],
        role_slug=data["role_slug"],
        source=data["source"],
        origin=data["origin"],
        job_url=data["job_url"],
        note=data["note"],
        first_seen_at=data["first_seen_at"],
        current_status=data["current_status"],
        status_as_of=data["status_as_of"],
        archived=data["archived"],
        jd_text=data["jd_text"],
        jd_source_type=data["jd_source_type"],
        jd_url=data["jd_url"],
        round_count=data["round_count"],
        current_round=data["current_round"],
        next_action=data["next_action"],
        applied_at=data["applied_at"],
        derived_from=str(data["derived_from"]) if data["derived_from"] else None,
        migrated_from=data["migrated_from"],
        created_at=data["created_at"],
        updated_at=data["updated_at"],
    )


def encode_cursor(updated_at: datetime, application_id: str) -> str:
    raw = f"{updated_at.isoformat()}|{application_id}".encode()
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode_cursor(cursor: str) -> tuple[datetime, str]:
    try:
        padding = "=" * (-len(cursor) % 4)
        raw = base64.urlsafe_b64decode(cursor + padding).decode("utf-8")
        stamp, application_id = raw.split("|", 1)
        return datetime.fromisoformat(stamp), application_id
    except (binascii.Error, UnicodeDecodeError, ValueError) as exc:
        raise ValidationFailed(
            "That page cursor is not valid. Start the list again without a cursor.",
            details={"field": "cursor"},
        ) from exc


async def get(conn: Any, user_id: str, application_id: str) -> ApplicationRow:
    record = await conn.fetchrow(
        f"select {_COLUMNS} from applications where id = $1 and user_id = $2",
        application_id,
        user_id,
    )
    if record is None:
        raise NotFound(_NOT_FOUND)
    return _row(record)


async def create(
    conn: Any,
    user_id: str,
    *,
    company: str,
    role: str | None,
    jd_text: str | None = None,
    jd_source_type: str | None = None,
    jd_url: str | None = None,
    origin: str = "generated",
    status: str = "draft",
) -> str:
    if not company or not company.strip():
        raise ValidationFailed(
            "An application needs a company name. Add one and try again.",
            details={"field": "company"},
        )
    record = await conn.fetchrow(
        """
        insert into applications
            (user_id, company_norm, company_display, company_slug,
             role_title, role_norm, role_slug,
             first_seen_at, current_status, status_as_of, origin,
             jd_text, jd_source_type, jd_url)
        values ($1, $2, $3, $4, $5, $6, $7, now(), $8, now(), $9, $10, $11, $12)
        returning id
        """,
        user_id,
        normalize_entity(company),
        company,
        slugify(company),
        role,
        normalize_entity(role) if role else None,
        slugify(role) if role else None,
        status,
        origin,
        jd_text,
        jd_source_type,
        jd_url,
    )
    return str(record["id"])


async def list_for_user(
    conn: Any,
    user_id: str,
    *,
    status: str | None = None,
    query: str | None = None,
    limit: int = DEFAULT_LIMIT,
    cursor: str | None = None,
) -> tuple[list[ApplicationRow], str | None]:
    """Cursor pagination on `(updated_at desc, id desc)`.

    Never offset: an offset page over a list that reorders whenever a row is touched drops rows
    and repeats rows, and this list reorders on every status change.
    """
    bounded = max(1, min(int(limit), MAX_LIMIT))
    params: list[Any] = [user_id]
    clauses = ["user_id = $1"]

    if status is not None:
        params.append(status)
        clauses.append(f"current_status = ${len(params)}")
    if query is not None and query.strip():
        params.append(f"%{query.strip()}%")
        index = len(params)
        clauses.append(f"(company_display ilike ${index} or role_title ilike ${index})")
    if cursor is not None:
        stamp, last_id = decode_cursor(cursor)
        params.extend([stamp, last_id])
        clauses.append(f"(updated_at, id) < (${len(params) - 1}, ${len(params)})")

    params.append(bounded + 1)
    records = await conn.fetch(
        f"select {_COLUMNS} from applications where {' and '.join(clauses)} "
        f"order by updated_at desc, id desc limit ${len(params)}",
        *params,
    )
    rows = [_row(record) for record in records[:bounded]]
    next_cursor: str | None = None
    if len(records) > bounded and rows:
        last = rows[-1]
        assert last.updated_at is not None
        next_cursor = encode_cursor(last.updated_at, last.id)
    return rows, next_cursor


async def update_tracking(
    conn: Any, user_id: str, application_id: str, **fields: Any
) -> ApplicationRow:
    if "status" in fields:
        fields["current_status"] = fields.pop("status")
    unknown = sorted(set(fields) - TRACKING_FIELDS)
    if unknown:
        raise ValidationFailed(
            f"Those fields cannot be updated on an application: {', '.join(unknown)}. "
            "Remove them and try again.",
            details={"fields": unknown},
        )
    if not fields:
        return await get(conn, user_id, application_id)

    assignments: list[str] = []
    params: list[Any] = [application_id, user_id]
    for name, value in fields.items():
        params.append(value)
        assignments.append(f"{name} = ${len(params)}")
    if "current_status" in fields:
        assignments.append("status_as_of = now()")

    record = await conn.fetchrow(
        f"update applications set {', '.join(assignments)} "
        f"where id = $1 and user_id = $2 returning {_COLUMNS}",
        *params,
    )
    if record is None:
        raise NotFound(_NOT_FOUND)
    return _row(record)


async def find_by_migration_key(
    conn: Any, user_id: str, migrated_from: str
) -> ApplicationRow | None:
    """Return the application a previous v1 directory migration created, if any.

    This is the one read that returns `None` rather than raising: the caller is asking whether a
    row exists so it can decide between insert and skip, and an absent row is the expected answer
    on a first pass rather than a failure.
    """
    record = await conn.fetchrow(
        f"select {_COLUMNS} from applications where user_id = $1 and migrated_from = $2",
        user_id,
        migrated_from,
    )
    return _row(record) if record is not None else None
