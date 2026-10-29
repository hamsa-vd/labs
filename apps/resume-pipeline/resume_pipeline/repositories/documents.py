"""Document index (RG-006, A6).

The row is the index. Nothing lists the document directory to find a file, so a stray file on
disk is inert and a deleted row is a deleted document regardless of what the filesystem still
holds. Every `BlobStore.put` is paired with an `insert` here; a put without an insert produces
bytes nobody can reach.

`content_hash` is what makes the compile cache real: a `.tex` that hashes to a PDF already
produced does not need Tectonic run over it again.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from resume_pipeline.errors import NotFound

_COLUMNS = """
    id, user_id, application_id, run_id, kind, storage_path,
    byte_size, content_hash, content_type, created_at
"""

_NOT_FOUND = "That document was not found. Check the document and try again."


@dataclass(frozen=True)
class DocumentRow:
    id: str
    user_id: str
    application_id: str
    run_id: str | None
    kind: str
    storage_path: str
    byte_size: int
    content_hash: str
    content_type: str
    created_at: datetime | None = None


def _row(record: Any) -> DocumentRow:
    data = dict(record)
    return DocumentRow(
        id=str(data["id"]),
        user_id=str(data["user_id"]),
        application_id=str(data["application_id"]),
        run_id=str(data["run_id"]) if data["run_id"] else None,
        kind=data["kind"],
        storage_path=data["storage_path"],
        byte_size=data["byte_size"],
        content_hash=data["content_hash"],
        content_type=data["content_type"],
        created_at=data["created_at"],
    )


async def insert(
    conn: Any,
    user_id: str,
    *,
    application_id: str,
    run_id: str | None,
    kind: str,
    storage_path: str,
    byte_size: int,
    content_hash: str,
    content_type: str,
) -> str:
    record = await conn.fetchrow(
        """
        insert into resume_documents
            (user_id, application_id, run_id, kind, storage_path, byte_size, content_hash, content_type)
        values ($1, $2, $3, $4, $5, $6, $7, $8)
        returning id
        """,
        user_id,
        application_id,
        run_id,
        kind,
        storage_path,
        byte_size,
        content_hash,
        content_type,
    )
    return str(record["id"])


async def get(conn: Any, user_id: str, document_id: str) -> DocumentRow:
    record = await conn.fetchrow(
        f"select {_COLUMNS} from resume_documents where id = $1 and user_id = $2",
        document_id,
        user_id,
    )
    if record is None:
        raise NotFound(_NOT_FOUND)
    return _row(record)


async def list_for_run(conn: Any, user_id: str, run_id: str) -> list[DocumentRow]:
    records = await conn.fetch(
        f"select {_COLUMNS} from resume_documents where user_id = $1 and run_id = $2 "
        "order by created_at asc, id asc",
        user_id,
        run_id,
    )
    return [_row(record) for record in records]


async def list_for_application(
    conn: Any, user_id: str, application_id: str, *, kind: str | None = None
) -> list[DocumentRow]:
    records = await conn.fetch(
        f"select {_COLUMNS} from resume_documents "
        "where user_id = $1 and application_id = $2 and ($3::text is null or kind = $3) "
        "order by created_at desc, id desc",
        user_id,
        application_id,
        kind,
    )
    return [_row(record) for record in records]


async def find_by_hash(
    conn: Any, user_id: str, kind: str, content_hash: str
) -> DocumentRow | None:
    """Cache lookup. Returns `None` rather than raising: absence is the expected miss."""
    record = await conn.fetchrow(
        f"select {_COLUMNS} from resume_documents "
        "where user_id = $1 and kind = $2 and content_hash = $3 "
        "order by created_at desc limit 1",
        user_id,
        kind,
        content_hash,
    )
    return _row(record) if record is not None else None


async def delete(conn: Any, user_id: str, document_id: str) -> None:
    result = await conn.execute(
        "delete from resume_documents where id = $1 and user_id = $2",
        document_id,
        user_id,
    )
    if result.endswith(" 0"):
        raise NotFound(_NOT_FOUND)
