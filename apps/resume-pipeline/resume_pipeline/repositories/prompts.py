"""Prompt versions (RG-022, A4).

Same shared-to-read, private-to-write rule as `templates.py`: `user_id is null` is the system
default for a stage, a user's row overrides it, and nothing here can edit a system row.

The schema allows at most one active version per `(user_id, stage)`, so `activate` deactivates
the user's other versions of that stage in the same statement pair. Two live prompts for one
stage would make resolution pick one arbitrarily, and "arbitrarily" here means the resume a user
gets changes between runs for no reason they can see.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from resume_pipeline.errors import NotFound

_COLUMNS = "id, user_id, stage, body, version, is_active, created_at, updated_at"

_NOT_FOUND = "That prompt was not found. Check the prompt and try again."

STAGES: tuple[str, ...] = ("targeting", "generation", "review", "revision", "ats", "cover_letter")


@dataclass(frozen=True)
class PromptRow:
    id: str
    user_id: str | None
    stage: str
    version: int
    is_active: bool
    # `repr=False`: a prompt body is document text, kept out of log lines by default.
    body: str = field(repr=False, default="")
    created_at: datetime | None = None
    updated_at: datetime | None = None


def _row(record: Any) -> PromptRow:
    data = dict(record)
    return PromptRow(
        id=str(data["id"]),
        user_id=str(data["user_id"]) if data["user_id"] else None,
        stage=data["stage"],
        version=data["version"],
        is_active=data["is_active"],
        body=data["body"],
        created_at=data["created_at"],
        updated_at=data["updated_at"],
    )


async def get(conn: Any, user_id: str, prompt_id: str) -> PromptRow:
    record = await conn.fetchrow(
        f"select {_COLUMNS} from resume_prompts "
        "where id = $1 and (user_id = $2 or user_id is null)",
        prompt_id,
        user_id,
    )
    if record is None:
        raise NotFound(_NOT_FOUND)
    return _row(record)


async def get_active(conn: Any, user_id: str, stage: str) -> PromptRow:
    """The prompt a run should use for `stage`: the user's active version, else the system one."""
    record = await conn.fetchrow(
        f"select {_COLUMNS} from resume_prompts "
        "where stage = $2 and is_active and (user_id = $1 or user_id is null) "
        "order by user_id nulls last limit 1",
        user_id,
        stage,
    )
    if record is None:
        raise NotFound(_NOT_FOUND)
    return _row(record)


async def list_for_user(
    conn: Any, user_id: str, *, stage: str | None = None, include_system: bool = True
) -> list[PromptRow]:
    records = await conn.fetch(
        f"select {_COLUMNS} from resume_prompts "
        "where (user_id = $1 or ($2 and user_id is null)) "
        "  and ($3::text is null or stage = $3) "
        "order by user_id nulls last, stage asc, version desc",
        user_id,
        include_system,
        stage,
    )
    return [_row(record) for record in records]


async def create_version(
    conn: Any, user_id: str, *, stage: str, body: str, activate: bool = True
) -> str:
    """Write the next version of a user's prompt for `stage`.

    The version number is allocated from the user's own maximum for that stage, so a user's
    versions are 1, 2, 3 regardless of how many system versions exist.
    """
    if activate:
        await conn.execute(
            "update resume_prompts set is_active = false where user_id = $1 and stage = $2",
            user_id,
            stage,
        )
    record = await conn.fetchrow(
        """
        insert into resume_prompts (user_id, stage, body, version, is_active)
        values (
            $1, $2, $3,
            (select coalesce(max(version), 0) + 1 from resume_prompts where user_id = $1 and stage = $2),
            $4
        )
        returning id
        """,
        user_id,
        stage,
        body,
        activate,
    )
    return str(record["id"])


async def activate(conn: Any, user_id: str, prompt_id: str) -> PromptRow:
    """Make one of the user's versions the live one for its stage."""
    target = await conn.fetchrow(
        "select stage from resume_prompts where id = $1 and user_id = $2",
        prompt_id,
        user_id,
    )
    if target is None:
        raise NotFound(_NOT_FOUND)
    await conn.execute(
        "update resume_prompts set is_active = false where user_id = $1 and stage = $2",
        user_id,
        target["stage"],
    )
    record = await conn.fetchrow(
        f"update resume_prompts set is_active = true "
        f"where id = $1 and user_id = $2 returning {_COLUMNS}",
        prompt_id,
        user_id,
    )
    if record is None:
        raise NotFound(_NOT_FOUND)
    return _row(record)


async def delete(conn: Any, user_id: str, prompt_id: str) -> None:
    result = await conn.execute(
        "delete from resume_prompts where id = $1 and user_id = $2",
        prompt_id,
        user_id,
    )
    if result.endswith(" 0"):
        raise NotFound(_NOT_FOUND)
