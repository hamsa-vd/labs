"""`resume_pipeline.repositories.documents` (WP3 §6).

"The row is the index; nothing lists the directory to find a file." That sentence is the whole
design: a stray file under the blob root is inert because no code path discovers it, and a document
only exists once this table says it does. So every `put` is paired with an `insert` here, and the
lookups this table supports — by id, by run, by content hash — are the only ways a file is ever
found again.

`find_by_hash` is what makes a re-run cheap: the same resume compiled twice hashes the same and the
second run reuses the first document instead of writing a duplicate. It is scoped by user like
everything else, because a hash collision across tenants would otherwise hand one user's file to
another.
"""

from __future__ import annotations

import hashlib
import uuid
from typing import Any

import asyncpg
import pytest

from resume_pipeline.errors import Conflict, NotFound
from tests.repositories.conftest import as_str, field

TEX = b"\\documentclass{article}\\begin{document}Hello\\end{document}"
TEX_HASH = hashlib.sha256(TEX).hexdigest()
PDF_HASH = hashlib.sha256(b"%PDF-1.7\n").hexdigest()


async def _application(repo: Any, conn: asyncpg.Connection, user_id: str) -> str:
    return await repo.create(  # type: ignore[no-any-return]
        conn,
        user_id,
        company="Liv-ex Ltd.",
        role="Senior Backend Engineer",
        jd_text="A job description.",
        jd_source_type="text",
        jd_url=None,
        origin="generated",
        status="draft",
    )


async def _run(conn: asyncpg.Connection, user_id: str, application_id: str) -> str:
    row = await conn.fetchrow(
        "insert into resume_runs (user_id, application_id) values ($1, $2) returning id",
        uuid.UUID(user_id),
        uuid.UUID(application_id),
    )
    return str(row["id"])


def _path(user_id: str, application_id: str, run_id: str | None, kind: str, ext: str) -> str:
    return f"{user_id}/{application_id}/{run_id or '_'}/{kind}{ext}"


async def _insert(
    repo: Any,
    conn: asyncpg.Connection,
    user_id: str,
    *,
    application_id: str,
    run_id: str | None,
    kind: str = "resume_tex",
    storage_path: str | None = None,
    content_hash: str = TEX_HASH,
    content_type: str = "text/plain",
    byte_size: int = len(TEX),
) -> str:
    return await repo.insert(  # type: ignore[no-any-return]
        conn,
        user_id,
        application_id=application_id,
        run_id=run_id,
        kind=kind,
        storage_path=storage_path or _path(user_id, application_id, run_id, kind, ".tex"),
        byte_size=byte_size,
        content_hash=content_hash,
        content_type=content_type,
    )


@pytest.fixture
async def application(applications_repo: Any, conn: asyncpg.Connection, user_a: str) -> str:
    return await _application(applications_repo, conn, user_a)


@pytest.fixture
async def run(conn: asyncpg.Connection, user_a: str, application: str) -> str:
    return await _run(conn, user_a, application)


# ─── insert ───────────────────────────────────────────────────────────────────


async def test_insert_returns_a_uuid_and_writes_every_column(
    documents_repo: Any, conn: asyncpg.Connection, user_a: str, application: str, run: str
) -> None:
    storage_path = _path(user_a, application, run, "resume_tex", ".tex")

    document_id = await _insert(
        documents_repo, conn, user_a, application_id=application, run_id=run,
        storage_path=storage_path,
    )

    uuid.UUID(document_id)
    row = await conn.fetchrow(
        "select * from resume_documents where id = $1", uuid.UUID(document_id)
    )
    assert row is not None
    assert str(row["user_id"]) == user_a
    assert str(row["application_id"]) == application
    assert str(row["run_id"]) == run
    assert row["kind"] == "resume_tex"
    assert row["storage_path"] == storage_path
    assert row["byte_size"] == len(TEX)
    assert row["content_hash"] == TEX_HASH
    assert row["content_type"] == "text/plain"


async def test_insert_accepts_a_document_with_no_run(
    documents_repo: Any, conn: asyncpg.Connection, user_a: str, application: str
) -> None:
    """An imported resume and a job description exist before any run does."""
    document_id = await _insert(
        documents_repo, conn, user_a, application_id=application, run_id=None, kind="jd",
        storage_path=_path(user_a, application, None, "jd", ".txt"),
    )

    row = await conn.fetchrow(
        "select run_id from resume_documents where id = $1", uuid.UUID(document_id)
    )
    assert row["run_id"] is None


async def test_two_documents_cannot_share_a_storage_path(
    documents_repo: Any, conn: asyncpg.Connection, user_a: str, application: str, run: str
) -> None:
    """One path, one row. Otherwise the index disagrees with the disk."""
    storage_path = _path(user_a, application, run, "resume_tex", ".tex")
    await _insert(
        documents_repo, conn, user_a, application_id=application, run_id=run,
        storage_path=storage_path,
    )

    with pytest.raises((Conflict, asyncpg.UniqueViolationError)):
        async with conn.transaction():
            await _insert(
                documents_repo, conn, user_a, application_id=application, run_id=run,
                storage_path=storage_path,
            )

    count = await conn.fetchval(
        "select count(*) from resume_documents where storage_path = $1", storage_path
    )
    assert count == 1


# ─── get ──────────────────────────────────────────────────────────────────────


async def test_get_returns_the_document(
    documents_repo: Any, conn: asyncpg.Connection, user_a: str, application: str, run: str
) -> None:
    document_id = await _insert(
        documents_repo, conn, user_a, application_id=application, run_id=run
    )

    row = await documents_repo.get(conn, user_a, document_id)

    assert as_str(field(row, "id")) == document_id
    assert field(row, "kind") == "resume_tex"
    assert field(row, "content_hash") == TEX_HASH


async def test_get_on_an_unknown_id_raises_not_found(
    documents_repo: Any, conn: asyncpg.Connection, user_a: str
) -> None:
    with pytest.raises(NotFound):
        await documents_repo.get(conn, user_a, str(uuid.uuid4()))


# ─── list_for_run ─────────────────────────────────────────────────────────────


async def test_list_for_run_returns_that_runs_documents(
    documents_repo: Any, conn: asyncpg.Connection, user_a: str, application: str, run: str
) -> None:
    tex = await _insert(
        documents_repo, conn, user_a, application_id=application, run_id=run,
        kind="resume_tex", storage_path=_path(user_a, application, run, "resume_tex", ".tex"),
    )
    pdf = await _insert(
        documents_repo, conn, user_a, application_id=application, run_id=run,
        kind="resume_pdf", storage_path=_path(user_a, application, run, "resume_pdf", ".pdf"),
        content_hash=PDF_HASH, content_type="application/pdf",
    )
    other_run = await _run(conn, user_a, application)
    await _insert(
        documents_repo, conn, user_a, application_id=application, run_id=other_run,
        storage_path=_path(user_a, application, other_run, "resume_tex", ".tex"),
    )

    rows = await documents_repo.list_for_run(conn, user_a, run)

    assert {as_str(field(row, "id")) for row in rows} == {tex, pdf}


async def test_list_for_an_unknown_run_is_empty(
    documents_repo: Any, conn: asyncpg.Connection, user_a: str
) -> None:
    assert await documents_repo.list_for_run(conn, user_a, str(uuid.uuid4())) == []


# ─── find_by_hash ─────────────────────────────────────────────────────────────


async def test_find_by_hash_finds_the_document(
    documents_repo: Any, conn: asyncpg.Connection, user_a: str, application: str, run: str
) -> None:
    document_id = await _insert(
        documents_repo, conn, user_a, application_id=application, run_id=run
    )

    row = await documents_repo.find_by_hash(conn, user_a, "resume_tex", TEX_HASH)

    assert row is not None
    assert as_str(field(row, "id")) == document_id


async def test_find_by_hash_is_scoped_by_kind(
    documents_repo: Any, conn: asyncpg.Connection, user_a: str, application: str, run: str
) -> None:
    await _insert(documents_repo, conn, user_a, application_id=application, run_id=run)

    assert await documents_repo.find_by_hash(conn, user_a, "resume_pdf", TEX_HASH) is None


async def test_find_by_hash_returns_none_for_an_unseen_hash(
    documents_repo: Any, conn: asyncpg.Connection, user_a: str, application: str, run: str
) -> None:
    await _insert(documents_repo, conn, user_a, application_id=application, run_id=run)

    unseen = hashlib.sha256(b"something else entirely").hexdigest()
    assert await documents_repo.find_by_hash(conn, user_a, "resume_tex", unseen) is None
