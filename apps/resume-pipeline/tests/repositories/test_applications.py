"""`resume_pipeline.repositories.applications` (WP3 §6).

There is one `applications` table and the tracker and the generator are two views of it, so the
repository's job is to write the generator's columns onto the same row the Gmail sync already owns.
Everything here is asserted against the database rather than against the returned object: the
contract names `ApplicationRow` without saying what it is, so the tests read columns through a
helper that copes with a record, a mapping or a dataclass, and check the row in Postgres directly
wherever the column is the point.

Each test runs inside a transaction that is rolled back, which has one consequence worth knowing:
`now()` is the transaction timestamp, so every row a test creates shares an `updated_at`. The
ordering assertions therefore exercise the `id desc` tiebreak — which is the half of
`(updated_at desc, id desc)` that actually makes a cursor stable.
"""

from __future__ import annotations

import uuid
from typing import Any

import asyncpg
import pytest

from resume_pipeline.errors import NotFound
from tests.repositories.conftest import as_str, field

COMPANY = "Liv-ex Ltd."
ROLE = "Senior Backend Engineer"
JD_TEXT = "We are hiring a senior backend engineer to own our order settlement platform."
JD_URL = "https://example.invalid/jobs/1"


async def _create(
    repo: Any,
    conn: asyncpg.Connection,
    user_id: str,
    *,
    company: str = COMPANY,
    role: str = ROLE,
    status: str = "draft",
    origin: str = "generated",
) -> str:
    return await repo.create(  # type: ignore[no-any-return]
        conn,
        user_id,
        company=company,
        role=role,
        jd_text=JD_TEXT,
        jd_source_type="text",
        jd_url=JD_URL,
        origin=origin,
        status=status,
    )


async def _row(conn: asyncpg.Connection, application_id: str) -> asyncpg.Record:
    row = await conn.fetchrow(
        "select * from applications where id = $1", uuid.UUID(application_id)
    )
    assert row is not None, "the application was not written"
    return row


# ─── create ───────────────────────────────────────────────────────────────────


async def test_create_returns_a_uuid(
    applications_repo: Any, conn: asyncpg.Connection, user_a: str
) -> None:
    application_id = await _create(applications_repo, conn, user_a)

    assert isinstance(application_id, str)
    uuid.UUID(application_id)  # raises if it is not one


async def test_create_writes_the_row_for_that_user(
    applications_repo: Any, conn: asyncpg.Connection, user_a: str
) -> None:
    application_id = await _create(applications_repo, conn, user_a)
    row = await _row(conn, application_id)

    assert str(row["user_id"]) == user_a
    assert row["company_display"] == COMPANY
    assert row["role_title"] == ROLE
    assert row["jd_text"] == JD_TEXT
    assert row["jd_source_type"] == "text"
    assert row["jd_url"] == JD_URL
    assert row["origin"] == "generated"
    assert row["current_status"] == "draft"


async def test_create_defaults_to_draft(
    applications_repo: Any, conn: asyncpg.Connection, user_a: str
) -> None:
    application_id = await applications_repo.create(
        conn,
        user_a,
        company=COMPANY,
        role=ROLE,
        jd_text=JD_TEXT,
        jd_source_type="text",
        jd_url=None,
        origin="generated",
    )
    assert (await _row(conn, application_id))["current_status"] == "draft"


async def test_create_computes_both_slugs_with_slugify(
    applications_repo: Any, conn: asyncpg.Connection, user_a: str
) -> None:
    application_id = await _create(
        applications_repo,
        conn,
        user_a,
        company="Café Liv-ex Ltd.",
        role="Senior Backend Engineer — Platform",
    )
    row = await _row(conn, application_id)

    assert row["company_slug"] == "cafe-liv-ex-ltd"
    assert row["role_slug"] == "senior-backend-engineer-platform"


async def test_slugs_fall_back_rather_than_going_empty(
    applications_repo: Any, conn: asyncpg.Connection, user_a: str
) -> None:
    application_id = await _create(applications_repo, conn, user_a, company="!!!", role="???")
    row = await _row(conn, application_id)

    assert row["company_slug"] == "untitled"
    assert row["role_slug"] == "untitled"


async def test_create_accepts_a_null_jd_url(
    applications_repo: Any, conn: asyncpg.Connection, user_a: str
) -> None:
    application_id = await applications_repo.create(
        conn,
        user_a,
        company=COMPANY,
        role=ROLE,
        jd_text=JD_TEXT,
        jd_source_type="text",
        jd_url=None,
        origin="generated",
        status="draft",
    )
    assert (await _row(conn, application_id))["jd_url"] is None


# ─── get ──────────────────────────────────────────────────────────────────────


async def test_get_returns_the_owners_row(
    applications_repo: Any, conn: asyncpg.Connection, user_a: str
) -> None:
    application_id = await _create(applications_repo, conn, user_a)

    row = await applications_repo.get(conn, user_a, application_id)

    assert as_str(field(row, "id")) == application_id
    assert as_str(field(row, "user_id")) == user_a
    assert field(row, "company_display", "company") == COMPANY


async def test_get_on_an_unknown_id_raises_not_found(
    applications_repo: Any, conn: asyncpg.Connection, user_a: str
) -> None:
    with pytest.raises(NotFound):
        await applications_repo.get(conn, user_a, str(uuid.uuid4()))


# ─── list_for_user ────────────────────────────────────────────────────────────


async def test_list_returns_only_this_users_applications(
    applications_repo: Any, conn: asyncpg.Connection, user_a: str, user_b: str
) -> None:
    mine = {await _create(applications_repo, conn, user_a) for _ in range(3)}
    await _create(applications_repo, conn, user_b)

    rows, _ = await applications_repo.list_for_user(conn, user_a)

    assert {as_str(field(row, "id")) for row in rows} == mine


async def test_list_orders_newest_first_with_a_stable_tiebreak(
    applications_repo: Any, conn: asyncpg.Connection, user_a: str
) -> None:
    for _ in range(5):
        await _create(applications_repo, conn, user_a)

    rows, _ = await applications_repo.list_for_user(conn, user_a)

    keys = [
        (field(row, "updated_at"), uuid.UUID(as_str(field(row, "id"))))
        for row in rows
    ]
    assert keys == sorted(keys, reverse=True), "expected (updated_at desc, id desc)"


async def test_list_honours_limit(
    applications_repo: Any, conn: asyncpg.Connection, user_a: str
) -> None:
    for _ in range(4):
        await _create(applications_repo, conn, user_a)

    rows, cursor = await applications_repo.list_for_user(conn, user_a, limit=2)

    assert len(rows) == 2
    assert cursor, "a truncated page must hand back a cursor"


async def test_cursor_pagination_walks_every_row_exactly_once(
    applications_repo: Any, conn: asyncpg.Connection, user_a: str
) -> None:
    created = {await _create(applications_repo, conn, user_a) for _ in range(5)}

    seen: list[str] = []
    cursor: str | None = None
    for _ in range(10):  # a bound, so a broken cursor fails instead of hanging
        rows, cursor = await applications_repo.list_for_user(
            conn, user_a, limit=2, cursor=cursor
        )
        seen.extend(as_str(field(row, "id")) for row in rows)
        if cursor is None:
            break

    assert cursor is None, "pagination did not terminate"
    assert len(seen) == len(set(seen)), "a row was returned on two pages"
    assert set(seen) == created


async def test_the_last_page_has_no_cursor(
    applications_repo: Any, conn: asyncpg.Connection, user_a: str
) -> None:
    await _create(applications_repo, conn, user_a)

    rows, cursor = await applications_repo.list_for_user(conn, user_a, limit=50)

    assert len(rows) == 1
    assert cursor is None


async def test_list_filters_by_status(
    applications_repo: Any, conn: asyncpg.Connection, user_a: str
) -> None:
    draft = await _create(applications_repo, conn, user_a, status="draft")
    applied = await _create(applications_repo, conn, user_a, status="applied")

    rows, _ = await applications_repo.list_for_user(conn, user_a, status="applied")
    ids = {as_str(field(row, "id")) for row in rows}

    assert applied in ids
    assert draft not in ids


async def test_list_filters_by_query(
    applications_repo: Any, conn: asyncpg.Connection, user_a: str, unique: str
) -> None:
    wanted = await _create(applications_repo, conn, user_a, company=f"Zyxwv {unique} Labs")
    other = await _create(applications_repo, conn, user_a, company="Presidio")

    rows, _ = await applications_repo.list_for_user(conn, user_a, query=unique)
    ids = {as_str(field(row, "id")) for row in rows}

    assert wanted in ids
    assert other not in ids


async def test_a_query_that_matches_nothing_returns_nothing(
    applications_repo: Any, conn: asyncpg.Connection, user_a: str
) -> None:
    await _create(applications_repo, conn, user_a)

    rows, cursor = await applications_repo.list_for_user(
        conn, user_a, query="qqqqzzzz-no-such-company"
    )

    assert rows == []
    assert cursor is None


async def test_a_user_with_nothing_gets_an_empty_page(
    applications_repo: Any, conn: asyncpg.Connection, user_b: str
) -> None:
    rows, cursor = await applications_repo.list_for_user(conn, user_b)
    assert rows == []
    assert cursor is None


# ─── update_tracking ──────────────────────────────────────────────────────────


async def test_update_tracking_writes_the_fields(
    applications_repo: Any, conn: asyncpg.Connection, user_a: str
) -> None:
    application_id = await _create(applications_repo, conn, user_a)

    row = await applications_repo.update_tracking(
        conn,
        user_a,
        application_id,
        next_action="Send a follow-up note",
        current_round="Technical screen",
    )

    assert field(row, "next_action") == "Send a follow-up note"
    assert field(row, "current_round") == "Technical screen"

    stored = await _row(conn, application_id)
    assert stored["next_action"] == "Send a follow-up note"
    assert stored["current_round"] == "Technical screen"


async def test_update_tracking_leaves_other_columns_alone(
    applications_repo: Any, conn: asyncpg.Connection, user_a: str
) -> None:
    application_id = await _create(applications_repo, conn, user_a)

    await applications_repo.update_tracking(conn, user_a, application_id, next_action="Wait")

    stored = await _row(conn, application_id)
    assert stored["company_display"] == COMPANY
    assert stored["jd_text"] == JD_TEXT


async def test_update_tracking_on_an_unknown_id_raises_not_found(
    applications_repo: Any, conn: asyncpg.Connection, user_a: str
) -> None:
    with pytest.raises(NotFound):
        await applications_repo.update_tracking(
            conn, user_a, str(uuid.uuid4()), next_action="Wait"
        )


async def test_update_tracking_refuses_a_column_it_does_not_own(
    applications_repo: Any, conn: asyncpg.Connection, user_a: str
) -> None:
    """`**fields` reaches a `set` clause, so the column names must come off an allowlist."""
    application_id = await _create(applications_repo, conn, user_a)

    with pytest.raises(Exception) as excinfo:  # noqa: B017
        async with conn.transaction():
            await applications_repo.update_tracking(
                conn, user_a, application_id, definitely_not_a_column="x"
            )

    assert not isinstance(excinfo.value, NotFound), "a bad field name is not a missing row"
    assert (await _row(conn, application_id))["company_display"] == COMPANY


# ─── find_by_migration_key ────────────────────────────────────────────────────


async def test_find_by_migration_key_finds_the_row(
    applications_repo: Any, conn: asyncpg.Connection, user_a: str, unique: str
) -> None:
    application_id = await _create(applications_repo, conn, user_a)
    key = f"v1/{unique}/liv-ex-senior-backend-engineer"
    await conn.execute(
        "update applications set migrated_from = $2 where id = $1",
        uuid.UUID(application_id),
        key,
    )

    row = await applications_repo.find_by_migration_key(conn, user_a, key)

    assert row is not None
    assert as_str(field(row, "id")) == application_id


async def test_find_by_migration_key_returns_none_when_unseen(
    applications_repo: Any, conn: asyncpg.Connection, user_a: str, unique: str
) -> None:
    assert await applications_repo.find_by_migration_key(conn, user_a, f"v1/{unique}") is None


async def test_find_by_migration_key_is_scoped_to_the_user(
    applications_repo: Any, conn: asyncpg.Connection, user_a: str, user_b: str, unique: str
) -> None:
    """Two users may migrate directories with the same key; neither sees the other's row."""
    application_id = await _create(applications_repo, conn, user_a)
    key = f"v1/{unique}/liv-ex"
    await conn.execute(
        "update applications set migrated_from = $2 where id = $1",
        uuid.UUID(application_id),
        key,
    )

    assert await applications_repo.find_by_migration_key(conn, user_b, key) is None
