"""Cross-tenant reads (WP3 §6, acceptance criterion 10).

This service trusts ascend's identity assertion, which means a bug in ascend that passes the wrong
`X-Ascend-User` is exactly one missing `where user_id = $n` away from being a cross-tenant read. The
contract's answer is that scoping lives in the repository, not in the caller, and that the refusal
is `NotFound` rather than `Forbidden`.

That choice is the interesting one, and these tests hold it to the letter. `Forbidden` on somebody
else's row confirms the row exists; so does a distinctive message. A user probing ids must not be
able to tell "there is no such application" from "there is one and it is not yours", so the last
test in this file compares the two messages with their ids normalised away, and fails if they
differ.
"""

from __future__ import annotations

import hashlib
import re
import uuid
from typing import Any

import asyncpg
import pytest

from resume_pipeline.errors import NotFound
from tests.repositories.conftest import as_str, field

TEX = b"\\documentclass{article}\\begin{document}Hello\\end{document}"
TEX_HASH = hashlib.sha256(TEX).hexdigest()
MIGRATION_KEY = "v1/liv-ex/senior-backend-engineer"

UUID_PATTERN = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)


def _normalise(message: str) -> str:
    return UUID_PATTERN.sub("<id>", message)


@pytest.fixture
async def application_a(applications_repo: Any, conn: asyncpg.Connection, user_a: str) -> str:
    application_id: str = await applications_repo.create(
        conn,
        user_a,
        company="Liv-ex Ltd.",
        role="Senior Backend Engineer",
        jd_text="A job description.",
        jd_source_type="text",
        jd_url=None,
        origin="generated",
        status="draft",
    )
    await conn.execute(
        "update applications set migrated_from = $2 where id = $1",
        uuid.UUID(application_id),
        MIGRATION_KEY,
    )
    return application_id


@pytest.fixture
async def run_a(conn: asyncpg.Connection, user_a: str, application_a: str) -> str:
    row = await conn.fetchrow(
        "insert into resume_runs (user_id, application_id) values ($1, $2) returning id",
        uuid.UUID(user_a),
        uuid.UUID(application_a),
    )
    return str(row["id"])


@pytest.fixture
async def document_a(
    documents_repo: Any, conn: asyncpg.Connection, user_a: str, application_a: str, run_a: str
) -> str:
    return await documents_repo.insert(  # type: ignore[no-any-return]
        conn,
        user_a,
        application_id=application_a,
        run_id=run_a,
        kind="resume_tex",
        storage_path=f"{user_a}/{application_a}/{run_a}/resume_tex.tex",
        byte_size=len(TEX),
        content_hash=TEX_HASH,
        content_type="text/plain",
    )


# ─── applications ─────────────────────────────────────────────────────────────


async def test_b_cannot_get_as_row(
    applications_repo: Any, conn: asyncpg.Connection, user_b: str, application_a: str
) -> None:
    with pytest.raises(NotFound):
        await applications_repo.get(conn, user_b, application_a)


async def test_b_cannot_update_as_row(
    applications_repo: Any,
    conn: asyncpg.Connection,
    user_b: str,
    application_a: str,
) -> None:
    with pytest.raises(NotFound):
        await applications_repo.update_tracking(
            conn, user_b, application_a, next_action="Owned by someone else"
        )

    stored = await conn.fetchrow(
        "select next_action from applications where id = $1", uuid.UUID(application_a)
    )
    assert stored["next_action"] is None, "the write landed on another tenant's row"


async def test_bs_list_does_not_contain_as_rows(
    applications_repo: Any, conn: asyncpg.Connection, user_b: str, application_a: str
) -> None:
    rows, _ = await applications_repo.list_for_user(conn, user_b)
    assert application_a not in {as_str(field(row, "id")) for row in rows}


async def test_b_cannot_find_as_migration_key(
    applications_repo: Any, conn: asyncpg.Connection, user_b: str, application_a: str
) -> None:
    assert await applications_repo.find_by_migration_key(conn, user_b, MIGRATION_KEY) is None


async def test_b_cannot_reach_as_row_by_query(
    applications_repo: Any, conn: asyncpg.Connection, user_b: str, application_a: str
) -> None:
    rows, _ = await applications_repo.list_for_user(conn, user_b, query="Liv-ex")
    assert rows == []


# ─── documents ────────────────────────────────────────────────────────────────


async def test_b_cannot_get_as_document(
    documents_repo: Any, conn: asyncpg.Connection, user_b: str, document_a: str
) -> None:
    with pytest.raises(NotFound):
        await documents_repo.get(conn, user_b, document_a)


async def test_b_cannot_list_as_run_documents(
    documents_repo: Any, conn: asyncpg.Connection, user_b: str, run_a: str, document_a: str
) -> None:
    assert await documents_repo.list_for_run(conn, user_b, run_a) == []


async def test_b_cannot_find_as_document_by_hash(
    documents_repo: Any, conn: asyncpg.Connection, user_b: str, document_a: str
) -> None:
    """A hash is guessable when the content is; it must not be a cross-tenant lookup key."""
    assert await documents_repo.find_by_hash(conn, user_b, "resume_tex", TEX_HASH) is None


# ─── runs ─────────────────────────────────────────────────────────────────────


async def test_b_cannot_get_as_run(
    runs_repo: Any, conn: asyncpg.Connection, user_b: str, run_a: str
) -> None:
    with pytest.raises(NotFound):
        await runs_repo.get(conn, user_b, run_a)


# ─── The refusal does not leak existence ──────────────────────────────────────


async def test_an_application_that_is_not_yours_reads_like_one_that_does_not_exist(
    applications_repo: Any, conn: asyncpg.Connection, user_b: str, application_a: str
) -> None:
    with pytest.raises(NotFound) as not_yours:
        await applications_repo.get(conn, user_b, application_a)
    with pytest.raises(NotFound) as no_such:
        await applications_repo.get(conn, user_b, str(uuid.uuid4()))

    assert _normalise(not_yours.value.message) == _normalise(no_such.value.message)
    assert not_yours.value.code == "not_found"
    assert not_yours.value.status == 404


async def test_a_document_that_is_not_yours_reads_like_one_that_does_not_exist(
    documents_repo: Any, conn: asyncpg.Connection, user_b: str, document_a: str
) -> None:
    with pytest.raises(NotFound) as not_yours:
        await documents_repo.get(conn, user_b, document_a)
    with pytest.raises(NotFound) as no_such:
        await documents_repo.get(conn, user_b, str(uuid.uuid4()))

    assert _normalise(not_yours.value.message) == _normalise(no_such.value.message)


async def test_the_refusal_names_neither_the_owner_nor_the_row(
    applications_repo: Any,
    conn: asyncpg.Connection,
    user_a: str,
    user_b: str,
    application_a: str,
) -> None:
    with pytest.raises(NotFound) as excinfo:
        await applications_repo.get(conn, user_b, application_a)

    message = excinfo.value.message
    assert user_a not in message
    assert "Liv-ex" not in message
    for word in ("owner", "belongs", "permission", "another user", "not yours"):
        assert word not in message.lower(), f"the refusal admits the row exists: {message}"
