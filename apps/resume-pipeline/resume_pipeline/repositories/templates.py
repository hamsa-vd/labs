"""Resume templates (RG-021, A3).

One deliberate departure from `user_id = $n` everywhere: a template with `user_id is null` is a
**system** template available to everyone, and the schema's two partial unique indexes exist
precisely so a user can override a system `(key, kind)` with their own row. So reads use
`(user_id = $1 or user_id is null)` and resolution prefers the user's row; **writes** stay
`user_id = $1`, so a system template cannot be edited or deleted by anyone reaching this service.

That asymmetry is the whole rule: shared to read, private to write.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from resume_pipeline.errors import NotFound, ValidationFailed

_COLUMNS = (
    "id, user_id, key, name, kind, tex_source, is_system, derived_from, created_at, updated_at"
)

_NOT_FOUND = "That template was not found. Check the template and try again."

UPDATABLE_FIELDS: frozenset[str] = frozenset({"name", "kind", "tex_source", "derived_from"})


@dataclass(frozen=True)
class TemplateRow:
    id: str
    user_id: str | None
    key: str
    name: str
    kind: str
    # `repr=False`: a .tex source is a document body, and a body does not belong in a log line.
    tex_source: str = field(repr=False, default="")
    is_system: bool = False
    derived_from: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


def _row(record: Any) -> TemplateRow:
    data = dict(record)
    return TemplateRow(
        id=str(data["id"]),
        user_id=str(data["user_id"]) if data["user_id"] else None,
        key=data["key"],
        name=data["name"],
        kind=data["kind"],
        tex_source=data["tex_source"],
        is_system=data["is_system"],
        derived_from=str(data["derived_from"]) if data["derived_from"] else None,
        created_at=data["created_at"],
        updated_at=data["updated_at"],
    )


async def get(conn: Any, user_id: str, template_id: str) -> TemplateRow:
    """Fetch a template the user may use: their own, or a system one."""
    record = await conn.fetchrow(
        f"select {_COLUMNS} from resume_templates "
        "where id = $1 and (user_id = $2 or user_id is null)",
        template_id,
        user_id,
    )
    if record is None:
        raise NotFound(_NOT_FOUND)
    return _row(record)


async def resolve(conn: Any, user_id: str, key: str, kind: str) -> TemplateRow:
    """Resolve `(key, kind)`, preferring the user's override over the system row.

    `order by user_id nulls last` is what implements "prefers the user's": the user's row sorts
    first, the system row is the fallback, and there can be at most one of each by the schema's
    two partial unique indexes.
    """
    record = await conn.fetchrow(
        f"select {_COLUMNS} from resume_templates "
        "where key = $2 and kind = $3 and (user_id = $1 or user_id is null) "
        "order by user_id nulls last limit 1",
        user_id,
        key,
        kind,
    )
    if record is None:
        raise NotFound(_NOT_FOUND)
    return _row(record)


async def list_for_user(
    conn: Any, user_id: str, *, kind: str | None = None, include_system: bool = True
) -> list[TemplateRow]:
    records = await conn.fetch(
        f"select {_COLUMNS} from resume_templates "
        "where (user_id = $1 or ($2 and user_id is null)) "
        "  and ($3::text is null or kind = $3) "
        "order by user_id nulls last, key asc, kind asc",
        user_id,
        include_system,
        kind,
    )
    return [_row(record) for record in records]


async def create(
    conn: Any,
    user_id: str,
    *,
    key: str,
    name: str,
    kind: str,
    tex_source: str,
    derived_from: str | None = None,
) -> str:
    """Create a template owned by this user. This module never creates a system template."""
    record = await conn.fetchrow(
        """
        insert into resume_templates (user_id, key, name, kind, tex_source, is_system, derived_from)
        values ($1, $2, $3, $4, $5, false, $6)
        returning id
        """,
        user_id,
        key,
        name,
        kind,
        tex_source,
        derived_from,
    )
    return str(record["id"])


async def update(conn: Any, user_id: str, template_id: str, **fields: Any) -> TemplateRow:
    unknown = sorted(set(fields) - UPDATABLE_FIELDS)
    if unknown:
        raise ValidationFailed(
            f"Those fields cannot be updated on a template: {', '.join(unknown)}. "
            "Remove them and try again.",
            details={"fields": unknown},
        )
    if not fields:
        return await get(conn, user_id, template_id)

    assignments: list[str] = []
    params: list[Any] = [template_id, user_id]
    for name, value in fields.items():
        params.append(value)
        assignments.append(f"{name} = ${len(params)}")

    # `user_id = $2`, not the read predicate: a system template is read-only here, and the miss
    # raises NotFound rather than Forbidden so it reads the same as a template that never existed.
    record = await conn.fetchrow(
        f"update resume_templates set {', '.join(assignments)} "
        f"where id = $1 and user_id = $2 returning {_COLUMNS}",
        *params,
    )
    if record is None:
        raise NotFound(_NOT_FOUND)
    return _row(record)


async def delete(conn: Any, user_id: str, template_id: str) -> None:
    result = await conn.execute(
        "delete from resume_templates where id = $1 and user_id = $2",
        template_id,
        user_id,
    )
    if result.endswith(" 0"):
        raise NotFound(_NOT_FOUND)
