"""Runs and their event log (RG-032, A5).

Thin. No business logic, no LLM, no HTTP — the run *service* decides what a run does; this module
only reads and writes the rows.

`resume_run_events` carries no `user_id` of its own, so every event read and write goes through
an ownership check on the parent run first. The events table is the SSE replay log, and `seq` is
unique per run, which is what makes a reconnect-at-seq return exactly one event rather than a
duplicate or a gap.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from resume_pipeline.errors import NotFound, ValidationFailed

_COLUMNS = """
    id, user_id, application_id, status, kind, template_id,
    recommended_template_key, template_reason, targeting_brief, resume_review,
    resume_score, cover_letter_score, fix_resolution_matrix, revision_count,
    ats, warnings, compile_errors, token_usage, cost_usd, budget, error,
    started_at, finished_at, created_at, updated_at
"""

_NOT_FOUND = "That run was not found. Check the run and try again."

#: Columns the run service may write after creation. `cost_usd` and `token_usage` are absent on
#: purpose: they belong to `telemetry.record_llm_call`, which advances them together with the
#: `resume_llm_calls` row so the two can never disagree.
UPDATABLE_FIELDS: frozenset[str] = frozenset(
    {
        "status",
        "template_id",
        "recommended_template_key",
        "template_reason",
        "targeting_brief",
        "resume_review",
        "resume_score",
        "cover_letter_score",
        "fix_resolution_matrix",
        "revision_count",
        "ats",
        "warnings",
        "compile_errors",
        "budget",
        "error",
        "started_at",
        "finished_at",
    }
)

#: jsonb columns. asyncpg sends a Python dict as an unknown type, so these are serialised here
#: and cast in the statement.
_JSON_FIELDS: frozenset[str] = frozenset(
    {
        "targeting_brief",
        "resume_review",
        "fix_resolution_matrix",
        "ats",
        "compile_errors",
        "budget",
    }
)


@dataclass(frozen=True)
class RunRow:
    id: str
    user_id: str
    application_id: str
    status: str
    kind: str
    template_id: str | None
    recommended_template_key: str | None
    template_reason: str | None
    targeting_brief: dict[str, Any] | None
    resume_review: dict[str, Any] | None
    resume_score: Decimal | None
    cover_letter_score: Decimal | None
    fix_resolution_matrix: Any
    revision_count: int
    ats: dict[str, Any] | None
    warnings: list[str]
    compile_errors: dict[str, Any]
    token_usage: dict[str, Any]
    cost_usd: Decimal
    budget: dict[str, Any]
    error: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime | None
    updated_at: datetime | None


@dataclass(frozen=True)
class RunEventRow:
    id: str
    run_id: str
    seq: int
    node: str
    status: str
    label: str
    payload: dict[str, Any]
    created_at: datetime | None


def _json(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, str):
        return json.loads(value)
    return value


def _row(record: Any) -> RunRow:
    data = dict(record)
    return RunRow(
        id=str(data["id"]),
        user_id=str(data["user_id"]),
        application_id=str(data["application_id"]),
        status=data["status"],
        kind=data["kind"],
        template_id=str(data["template_id"]) if data["template_id"] else None,
        recommended_template_key=data["recommended_template_key"],
        template_reason=data["template_reason"],
        targeting_brief=_json(data["targeting_brief"], None),
        resume_review=_json(data["resume_review"], None),
        resume_score=data["resume_score"],
        cover_letter_score=data["cover_letter_score"],
        fix_resolution_matrix=_json(data["fix_resolution_matrix"], []),
        revision_count=data["revision_count"],
        ats=_json(data["ats"], None),
        warnings=list(data["warnings"] or []),
        compile_errors=_json(data["compile_errors"], {}),
        token_usage=_json(data["token_usage"], {}),
        cost_usd=data["cost_usd"],
        budget=_json(data["budget"], {}),
        error=data["error"],
        started_at=data["started_at"],
        finished_at=data["finished_at"],
        created_at=data["created_at"],
        updated_at=data["updated_at"],
    )


def _event_row(record: Any) -> RunEventRow:
    data = dict(record)
    return RunEventRow(
        id=str(data["id"]),
        run_id=str(data["run_id"]),
        seq=data["seq"],
        node=data["node"],
        status=data["status"],
        label=data["label"],
        payload=_json(data["payload"], {}),
        created_at=data["created_at"],
    )


async def create(
    conn: Any,
    user_id: str,
    *,
    application_id: str,
    kind: str = "generate",
    status: str = "queued",
    template_id: str | None = None,
    budget: dict[str, Any] | None = None,
) -> str:
    record = await conn.fetchrow(
        """
        insert into resume_runs (user_id, application_id, kind, status, template_id, budget)
        values ($1, $2, $3, $4, $5, $6::jsonb)
        returning id
        """,
        user_id,
        application_id,
        kind,
        status,
        template_id,
        json.dumps(budget or {}),
    )
    return str(record["id"])


async def get(conn: Any, user_id: str, run_id: str) -> RunRow:
    record = await conn.fetchrow(
        f"select {_COLUMNS} from resume_runs where id = $1 and user_id = $2",
        run_id,
        user_id,
    )
    if record is None:
        raise NotFound(_NOT_FOUND)
    return _row(record)


async def list_for_user(conn: Any, user_id: str, *, limit: int = 50) -> list[RunRow]:
    records = await conn.fetch(
        f"select {_COLUMNS} from resume_runs where user_id = $1 "
        "order by created_at desc, id desc limit $2",
        user_id,
        max(1, min(int(limit), 200)),
    )
    return [_row(record) for record in records]


async def list_for_application(
    conn: Any, user_id: str, application_id: str, *, limit: int = 50
) -> list[RunRow]:
    records = await conn.fetch(
        f"select {_COLUMNS} from resume_runs where user_id = $1 and application_id = $2 "
        "order by created_at desc, id desc limit $3",
        user_id,
        application_id,
        max(1, min(int(limit), 200)),
    )
    return [_row(record) for record in records]


async def update(conn: Any, user_id: str, run_id: str, **fields: Any) -> RunRow:
    unknown = sorted(set(fields) - UPDATABLE_FIELDS)
    if unknown:
        raise ValidationFailed(
            f"Those fields cannot be updated on a run: {', '.join(unknown)}. "
            "Remove them and try again.",
            details={"fields": unknown},
        )
    if not fields:
        return await get(conn, user_id, run_id)

    assignments: list[str] = []
    params: list[Any] = [run_id, user_id]
    for name, value in fields.items():
        if name in _JSON_FIELDS:
            params.append(json.dumps(value) if value is not None else None)
            assignments.append(f"{name} = ${len(params)}::jsonb")
        else:
            params.append(value)
            assignments.append(f"{name} = ${len(params)}")

    record = await conn.fetchrow(
        f"update resume_runs set {', '.join(assignments)} "
        f"where id = $1 and user_id = $2 returning {_COLUMNS}",
        *params,
    )
    if record is None:
        raise NotFound(_NOT_FOUND)
    return _row(record)


async def append_event(
    conn: Any,
    user_id: str,
    run_id: str,
    *,
    node: str,
    status: str,
    label: str,
    payload: dict[str, Any] | None = None,
) -> RunEventRow:
    """Append the next event for a run and return it.

    `seq` is allocated from the run's own maximum inside the statement, so two concurrent
    appends collide on `resume_run_events_run_seq_key` rather than both claiming the same number.
    """
    owned = await conn.fetchval(
        "select 1 from resume_runs where id = $1 and user_id = $2",
        run_id,
        user_id,
    )
    if owned is None:
        raise NotFound(_NOT_FOUND)

    record = await conn.fetchrow(
        """
        insert into resume_run_events (run_id, seq, node, status, label, payload)
        values (
            $1,
            (select coalesce(max(seq), 0) + 1 from resume_run_events where run_id = $1),
            $2, $3, $4, $5::jsonb
        )
        returning id, run_id, seq, node, status, label, payload, created_at
        """,
        run_id,
        node,
        status,
        label,
        json.dumps(payload or {}),
    )
    return _event_row(record)


async def list_events(
    conn: Any, user_id: str, run_id: str, *, after_seq: int = 0, limit: int = 500
) -> list[RunEventRow]:
    owned = await conn.fetchval(
        "select 1 from resume_runs where id = $1 and user_id = $2",
        run_id,
        user_id,
    )
    if owned is None:
        raise NotFound(_NOT_FOUND)

    records = await conn.fetch(
        """
        select id, run_id, seq, node, status, label, payload, created_at
          from resume_run_events
         where run_id = $1 and seq > $2
         order by seq asc
         limit $3
        """,
        run_id,
        after_seq,
        max(1, min(int(limit), 2000)),
    )
    return [_event_row(record) for record in records]
