"""Source of truth: companies, projects, bullets, skills (RG-020, A2).

Relational, not a text blob, because the evidence gate has to point a keyword at one specific
bullet under one specific company. A blob cannot make that claim, and a claim the system cannot
trace to a bullet is exactly the claim it must refuse to add to a resume.

Dates are text, not `date`: the candidate's record says "Jul 2022" and "Present", and coercing
those to a date invents a precision they never gave.

Every read and write carries `user_id = $n`. The child tables carry their own `user_id` column
(the schema denormalises it for this reason), so a bullet is scoped directly rather than through
a join that a future refactor could drop.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

from resume_pipeline.errors import NotFound, ValidationFailed

_COMPANY_COLUMNS = (
    "id, user_id, name, role_title, start_date, end_date, location, sort_order, "
    "created_at, updated_at"
)
_PROJECT_COLUMNS = (
    "id, user_id, company_id, name, summary, tech, sort_order, created_at, updated_at"
)
_BULLET_COLUMNS = (
    "id, user_id, company_id, project_id, text, metrics, tags, sort_order, "
    "created_at, updated_at"
)
_SKILL_COLUMNS = (
    "id, user_id, name, category, proficiency, years, evidence_bullet_ids, sort_order, "
    "created_at, updated_at"
)

_NOT_FOUND = "That source of truth entry was not found. Check the entry and try again."


@dataclass(frozen=True)
class CompanyRow:
    id: str
    user_id: str
    name: str
    role_title: str | None
    start_date: str | None
    end_date: str | None
    location: str | None
    sort_order: int
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class ProjectRow:
    id: str
    user_id: str
    company_id: str
    name: str
    summary: str | None
    tech: list[str]
    sort_order: int
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class BulletRow:
    id: str
    user_id: str
    company_id: str
    project_id: str | None
    text: str = field(repr=False, default="")
    metrics: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    sort_order: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class SkillRow:
    id: str
    user_id: str
    name: str
    category: str | None
    proficiency: str | None
    years: Decimal | None
    evidence_bullet_ids: list[str]
    sort_order: int
    created_at: datetime | None = None
    updated_at: datetime | None = None


def _company(record: Any) -> CompanyRow:
    data = dict(record)
    return CompanyRow(
        id=str(data["id"]),
        user_id=str(data["user_id"]),
        name=data["name"],
        role_title=data["role_title"],
        start_date=data["start_date"],
        end_date=data["end_date"],
        location=data["location"],
        sort_order=data["sort_order"],
        created_at=data["created_at"],
        updated_at=data["updated_at"],
    )


def _project(record: Any) -> ProjectRow:
    data = dict(record)
    return ProjectRow(
        id=str(data["id"]),
        user_id=str(data["user_id"]),
        company_id=str(data["company_id"]),
        name=data["name"],
        summary=data["summary"],
        tech=list(data["tech"] or []),
        sort_order=data["sort_order"],
        created_at=data["created_at"],
        updated_at=data["updated_at"],
    )


def _bullet(record: Any) -> BulletRow:
    data = dict(record)
    return BulletRow(
        id=str(data["id"]),
        user_id=str(data["user_id"]),
        company_id=str(data["company_id"]),
        project_id=str(data["project_id"]) if data["project_id"] else None,
        text=data["text"],
        metrics=list(data["metrics"] or []),
        tags=list(data["tags"] or []),
        sort_order=data["sort_order"],
        created_at=data["created_at"],
        updated_at=data["updated_at"],
    )


def _skill(record: Any) -> SkillRow:
    data = dict(record)
    return SkillRow(
        id=str(data["id"]),
        user_id=str(data["user_id"]),
        name=data["name"],
        category=data["category"],
        proficiency=data["proficiency"],
        years=data["years"],
        evidence_bullet_ids=[str(value) for value in (data["evidence_bullet_ids"] or [])],
        sort_order=data["sort_order"],
        created_at=data["created_at"],
        updated_at=data["updated_at"],
    )


def _check_fields(table: str, fields: dict[str, Any], allowed: frozenset[str]) -> None:
    unknown = sorted(set(fields) - allowed)
    if unknown:
        raise ValidationFailed(
            f"Those fields cannot be updated on a {table}: {', '.join(unknown)}. "
            "Remove them and try again.",
            details={"fields": unknown},
        )


async def _update(
    conn: Any,
    *,
    table: str,
    columns: str,
    label: str,
    user_id: str,
    row_id: str,
    allowed: frozenset[str],
    fields: dict[str, Any],
    getter: Any,
) -> Any:
    _check_fields(label, fields, allowed)
    if not fields:
        return await getter(conn, user_id, row_id)
    assignments: list[str] = []
    params: list[Any] = [row_id, user_id]
    for name, value in fields.items():
        params.append(value)
        assignments.append(f"{name} = ${len(params)}")
    record = await conn.fetchrow(
        f"update {table} set {', '.join(assignments)} "
        f"where id = $1 and user_id = $2 returning {columns}",
        *params,
    )
    if record is None:
        raise NotFound(_NOT_FOUND)
    return record


async def _delete(conn: Any, table: str, user_id: str, row_id: str) -> None:
    result = await conn.execute(
        f"delete from {table} where id = $1 and user_id = $2", row_id, user_id
    )
    if result.endswith(" 0"):
        raise NotFound(_NOT_FOUND)


# --- companies ---------------------------------------------------------------------------

COMPANY_FIELDS = frozenset({"name", "role_title", "start_date", "end_date", "location", "sort_order"})


async def create_company(
    conn: Any,
    user_id: str,
    *,
    name: str,
    role_title: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    location: str | None = None,
    sort_order: int = 0,
) -> str:
    record = await conn.fetchrow(
        """
        insert into sot_companies (user_id, name, role_title, start_date, end_date, location, sort_order)
        values ($1, $2, $3, $4, $5, $6, $7)
        returning id
        """,
        user_id,
        name,
        role_title,
        start_date,
        end_date,
        location,
        sort_order,
    )
    return str(record["id"])


async def get_company(conn: Any, user_id: str, company_id: str) -> CompanyRow:
    record = await conn.fetchrow(
        f"select {_COMPANY_COLUMNS} from sot_companies where id = $1 and user_id = $2",
        company_id,
        user_id,
    )
    if record is None:
        raise NotFound(_NOT_FOUND)
    return _company(record)


async def list_companies(conn: Any, user_id: str) -> list[CompanyRow]:
    records = await conn.fetch(
        f"select {_COMPANY_COLUMNS} from sot_companies where user_id = $1 "
        "order by sort_order asc, created_at asc",
        user_id,
    )
    return [_company(record) for record in records]


async def update_company(conn: Any, user_id: str, company_id: str, **fields: Any) -> CompanyRow:
    result = await _update(
        conn,
        table="sot_companies",
        columns=_COMPANY_COLUMNS,
        label="company",
        user_id=user_id,
        row_id=company_id,
        allowed=COMPANY_FIELDS,
        fields=fields,
        getter=get_company,
    )
    return result if isinstance(result, CompanyRow) else _company(result)


async def delete_company(conn: Any, user_id: str, company_id: str) -> None:
    await _delete(conn, "sot_companies", user_id, company_id)


# --- projects ----------------------------------------------------------------------------

PROJECT_FIELDS = frozenset({"company_id", "name", "summary", "tech", "sort_order"})


async def create_project(
    conn: Any,
    user_id: str,
    *,
    company_id: str,
    name: str,
    summary: str | None = None,
    tech: list[str] | None = None,
    sort_order: int = 0,
) -> str:
    record = await conn.fetchrow(
        """
        insert into sot_projects (user_id, company_id, name, summary, tech, sort_order)
        values ($1, $2, $3, $4, $5, $6)
        returning id
        """,
        user_id,
        company_id,
        name,
        summary,
        list(tech or []),
        sort_order,
    )
    return str(record["id"])


async def get_project(conn: Any, user_id: str, project_id: str) -> ProjectRow:
    record = await conn.fetchrow(
        f"select {_PROJECT_COLUMNS} from sot_projects where id = $1 and user_id = $2",
        project_id,
        user_id,
    )
    if record is None:
        raise NotFound(_NOT_FOUND)
    return _project(record)


async def list_projects(
    conn: Any, user_id: str, *, company_id: str | None = None
) -> list[ProjectRow]:
    records = await conn.fetch(
        f"select {_PROJECT_COLUMNS} from sot_projects "
        "where user_id = $1 and ($2::uuid is null or company_id = $2) "
        "order by sort_order asc, created_at asc",
        user_id,
        company_id,
    )
    return [_project(record) for record in records]


async def update_project(conn: Any, user_id: str, project_id: str, **fields: Any) -> ProjectRow:
    result = await _update(
        conn,
        table="sot_projects",
        columns=_PROJECT_COLUMNS,
        label="project",
        user_id=user_id,
        row_id=project_id,
        allowed=PROJECT_FIELDS,
        fields=fields,
        getter=get_project,
    )
    return result if isinstance(result, ProjectRow) else _project(result)


async def delete_project(conn: Any, user_id: str, project_id: str) -> None:
    await _delete(conn, "sot_projects", user_id, project_id)


# --- bullets -----------------------------------------------------------------------------

BULLET_FIELDS = frozenset({"company_id", "project_id", "text", "metrics", "tags", "sort_order"})


async def create_bullet(
    conn: Any,
    user_id: str,
    *,
    company_id: str,
    text: str,
    project_id: str | None = None,
    metrics: list[str] | None = None,
    tags: list[str] | None = None,
    sort_order: int = 0,
) -> str:
    record = await conn.fetchrow(
        """
        insert into sot_bullets (user_id, company_id, project_id, text, metrics, tags, sort_order)
        values ($1, $2, $3, $4, $5, $6, $7)
        returning id
        """,
        user_id,
        company_id,
        project_id,
        text,
        list(metrics or []),
        list(tags or []),
        sort_order,
    )
    return str(record["id"])


async def get_bullet(conn: Any, user_id: str, bullet_id: str) -> BulletRow:
    record = await conn.fetchrow(
        f"select {_BULLET_COLUMNS} from sot_bullets where id = $1 and user_id = $2",
        bullet_id,
        user_id,
    )
    if record is None:
        raise NotFound(_NOT_FOUND)
    return _bullet(record)


async def list_bullets(
    conn: Any,
    user_id: str,
    *,
    company_id: str | None = None,
    project_id: str | None = None,
) -> list[BulletRow]:
    records = await conn.fetch(
        f"select {_BULLET_COLUMNS} from sot_bullets "
        "where user_id = $1 "
        "  and ($2::uuid is null or company_id = $2) "
        "  and ($3::uuid is null or project_id = $3) "
        "order by sort_order asc, created_at asc",
        user_id,
        company_id,
        project_id,
    )
    return [_bullet(record) for record in records]


async def update_bullet(conn: Any, user_id: str, bullet_id: str, **fields: Any) -> BulletRow:
    result = await _update(
        conn,
        table="sot_bullets",
        columns=_BULLET_COLUMNS,
        label="bullet",
        user_id=user_id,
        row_id=bullet_id,
        allowed=BULLET_FIELDS,
        fields=fields,
        getter=get_bullet,
    )
    return result if isinstance(result, BulletRow) else _bullet(result)


async def delete_bullet(conn: Any, user_id: str, bullet_id: str) -> None:
    await _delete(conn, "sot_bullets", user_id, bullet_id)


# --- skills ------------------------------------------------------------------------------

SKILL_FIELDS = frozenset(
    {"name", "category", "proficiency", "years", "evidence_bullet_ids", "sort_order"}
)


async def create_skill(
    conn: Any,
    user_id: str,
    *,
    name: str,
    category: str | None = None,
    proficiency: str | None = None,
    years: Decimal | None = None,
    evidence_bullet_ids: list[str] | None = None,
    sort_order: int = 0,
) -> str:
    record = await conn.fetchrow(
        """
        insert into sot_skills
            (user_id, name, category, proficiency, years, evidence_bullet_ids, sort_order)
        values ($1, $2, $3, $4, $5, $6::uuid[], $7)
        returning id
        """,
        user_id,
        name,
        category,
        proficiency,
        years,
        list(evidence_bullet_ids or []),
        sort_order,
    )
    return str(record["id"])


async def get_skill(conn: Any, user_id: str, skill_id: str) -> SkillRow:
    record = await conn.fetchrow(
        f"select {_SKILL_COLUMNS} from sot_skills where id = $1 and user_id = $2",
        skill_id,
        user_id,
    )
    if record is None:
        raise NotFound(_NOT_FOUND)
    return _skill(record)


async def list_skills(conn: Any, user_id: str) -> list[SkillRow]:
    records = await conn.fetch(
        f"select {_SKILL_COLUMNS} from sot_skills where user_id = $1 "
        "order by sort_order asc, created_at asc",
        user_id,
    )
    return [_skill(record) for record in records]


async def update_skill(conn: Any, user_id: str, skill_id: str, **fields: Any) -> SkillRow:
    result = await _update(
        conn,
        table="sot_skills",
        columns=_SKILL_COLUMNS,
        label="skill",
        user_id=user_id,
        row_id=skill_id,
        allowed=SKILL_FIELDS,
        fields=fields,
        getter=get_skill,
    )
    return result if isinstance(result, SkillRow) else _skill(result)


async def delete_skill(conn: Any, user_id: str, skill_id: str) -> None:
    await _delete(conn, "sot_skills", user_id, skill_id)
