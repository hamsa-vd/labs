"""`resume_pipeline.repositories.keys` (WP4 §7) — the BYOK key table.

`KeyRow` is the type that leaves this module, and the contract's requirement on it is structural
rather than behavioural: it has **no field capable of holding the secret**. Not a redacted one, not
one that happens to be empty — none. That is checked without a database, because it is a property
of the type and it is the property most likely to be lost in a later edit.

The rest needs Postgres and opts in: `RESUME_DATABASE_URL`, then `TEST_DATABASE_URL`. With neither
set the module skips and the default suite stays offline. The dev database at
`postgres://ascend:ascend@127.0.0.1:55432/ascend` is shared with other agents, so every test here
creates its own user and deletes it afterwards; nothing is reset, truncated, or migrated.

What the database tests are actually for is the join between this module and `crypto`: `upsert`
seals before writing, so the row in the table must be openable by `open_sealed` and must not
contain the plaintext. Reading the stored bytes is the only way to prove the sealing happened at
the boundary rather than somewhere later.
"""

from __future__ import annotations

import contextlib
import dataclasses
import importlib
import inspect
import os
import socket
import uuid
from collections.abc import AsyncIterator
from types import ModuleType
from typing import Any

import pytest

from resume_pipeline.errors import AppError, Forbidden
from tests.llm.conftest import FALLBACK_SETTINGS_ENV, SENTINEL_SECRET, ensure_settings_env

ensure_settings_env()

#: The placeholder the offline suite sets so `settings` can load. It names a database nobody
#: creates, so it must not be mistaken for "a database is available".
PLACEHOLDER_URLS = {FALLBACK_SETTINGS_ENV["RESUME_DATABASE_URL"]}

EXPECTED_FIELDS = ("id", "provider", "label", "last_four", "created_at", "last_used_at")

#: Substrings that betray a field able to hold a key. `last_four` is deliberately not one of them:
#: four characters is what the UI shows, and it is not the secret.
SECRET_ISH = ("cipher", "secret", "plaintext", "token", "api_key", "apikey", "material", "value")

ANTHROPIC_KEY = SENTINEL_SECRET
OPENAI_KEY = "sk-openai-SENTINEL-do-not-render-9d4e2c"

# Captured before `tests/conftest.py::_no_network` monkeypatches them.
_REAL_SOCKET_API = {
    "socket.connect": socket.socket.connect,
    "socket.connect_ex": socket.socket.connect_ex,
    "socket.sendto": socket.socket.sendto,
    "create_connection": socket.create_connection,
    "getaddrinfo": socket.getaddrinfo,
}


def database_url() -> str | None:
    for name in ("RESUME_DATABASE_URL", "TEST_DATABASE_URL"):
        value = os.environ.get(name, "").strip()
        if value and value not in PLACEHOLDER_URLS:
            return value
    return None


@pytest.fixture(scope="session")
def keys_repo() -> ModuleType:
    ensure_settings_env()
    try:
        return importlib.import_module("resume_pipeline.repositories.keys")
    except ModuleNotFoundError as exc:  # pragma: no cover - only before WP4 source lands
        pytest.fail(
            f"WP4 has not provided `resume_pipeline.repositories.keys` yet ({exc}).", pytrace=False
        )


@pytest.fixture(scope="session")
def crypto_module() -> ModuleType:
    ensure_settings_env()
    try:
        return importlib.import_module("resume_pipeline.crypto")
    except ModuleNotFoundError as exc:  # pragma: no cover - only before WP4 source lands
        pytest.fail(f"WP4 has not provided `resume_pipeline.crypto` yet ({exc}).", pytrace=False)


# ─── Structure, no database needed ────────────────────────────────────────────


def test_key_row_carries_exactly_the_contract_fields(keys_repo: ModuleType) -> None:
    names = tuple(f.name for f in dataclasses.fields(keys_repo.KeyRow))

    assert names == EXPECTED_FIELDS


def test_key_row_has_no_field_capable_of_holding_the_secret(keys_repo: ModuleType) -> None:
    """Not "a field that is usually empty" — no field at all. A `ciphertext` attribute on the type
    the API returns is one careless `asdict` away from being serialised to the browser."""
    for field in dataclasses.fields(keys_repo.KeyRow):
        lowered = field.name.lower()
        for marker in SECRET_ISH:
            assert marker not in lowered, f"`KeyRow.{field.name}` can hold a secret"


def test_a_key_row_renders_nothing_secret(keys_repo: ModuleType) -> None:
    row = keys_repo.KeyRow(
        id=str(uuid.uuid4()),
        provider="anthropic",
        label="default",
        last_four=ANTHROPIC_KEY[-4:],
        created_at=None,
        last_used_at=None,
    )

    rendered = f"{row!r} {row!s} {dataclasses.asdict(row)!r}"
    assert ANTHROPIC_KEY not in rendered
    assert ANTHROPIC_KEY[:-4] not in rendered


@pytest.mark.parametrize("name", ["list_for_user", "upsert", "delete", "mark_used"])
def test_the_repository_exposes_the_contract_functions(keys_repo: ModuleType, name: str) -> None:
    assert inspect.iscoroutinefunction(getattr(keys_repo, name))


# ─── Postgres ─────────────────────────────────────────────────────────────────


@pytest.fixture
def _allow_localhost_postgres(monkeypatch: pytest.MonkeyPatch) -> None:
    """Lift the suite-wide socket guard for the database tests only.

    The guard in `tests/conftest.py` is autouse and right: no unit test may open a socket. These
    tests talk to Postgres on localhost and are the exception, in the same shape as the container
    tests in `tests/latex/conftest.py`.
    """
    monkeypatch.setattr(socket.socket, "connect", _REAL_SOCKET_API["socket.connect"])
    monkeypatch.setattr(socket.socket, "connect_ex", _REAL_SOCKET_API["socket.connect_ex"])
    monkeypatch.setattr(socket.socket, "sendto", _REAL_SOCKET_API["socket.sendto"])
    monkeypatch.setattr(socket, "create_connection", _REAL_SOCKET_API["create_connection"])
    monkeypatch.setattr(socket, "getaddrinfo", _REAL_SOCKET_API["getaddrinfo"])


@pytest.fixture
async def conn(_allow_localhost_postgres: None) -> AsyncIterator[Any]:
    url = database_url()
    if not url:
        pytest.skip(
            "Neither RESUME_DATABASE_URL nor TEST_DATABASE_URL names a database; "
            "the key repository tests need Postgres."
        )
    asyncpg = importlib.import_module("asyncpg")
    connection = await asyncpg.connect(url)
    try:
        yield connection
    finally:
        await connection.close()


@pytest.fixture
async def user_id(conn: Any) -> AsyncIterator[str]:
    """A user of this test's own, removed afterwards. `resume_api_keys` cascades from it."""
    email = f"wp4-keys-{uuid.uuid4().hex}@tests.invalid"
    created = await conn.fetchval(
        "insert into app_users (email) values ($1) returning id::text", email
    )
    try:
        yield created
    finally:
        await conn.execute("delete from app_users where id = $1::uuid", created)


@pytest.fixture
async def other_user_id(conn: Any) -> AsyncIterator[str]:
    email = f"wp4-keys-other-{uuid.uuid4().hex}@tests.invalid"
    created = await conn.fetchval(
        "insert into app_users (email) values ($1) returning id::text", email
    )
    try:
        yield created
    finally:
        await conn.execute("delete from app_users where id = $1::uuid", created)


async def stored_rows(conn: Any, user_id: str) -> list[Any]:
    return await conn.fetch(
        "select id::text as id, provider, label, last_four, ciphertext, last_used_at "
        "from resume_api_keys where user_id = $1::uuid order by provider, label",
        user_id,
    )


async def test_upsert_returns_the_new_key_id(keys_repo: ModuleType, conn: Any, user_id: str) -> None:
    key_id = await keys_repo.upsert(
        conn, user_id, provider="anthropic", label="default", secret=ANTHROPIC_KEY
    )

    assert key_id
    assert uuid.UUID(str(key_id))


async def test_upsert_writes_one_row(keys_repo: ModuleType, conn: Any, user_id: str) -> None:
    await keys_repo.upsert(
        conn, user_id, provider="anthropic", label="default", secret=ANTHROPIC_KEY
    )

    rows = await stored_rows(conn, user_id)
    assert len(rows) == 1
    assert rows[0]["provider"] == "anthropic"
    assert rows[0]["label"] == "default"


async def test_upsert_seals_before_writing(
    keys_repo: ModuleType, crypto_module: ModuleType, conn: Any, user_id: str
) -> None:
    """The plaintext never reaches the column. This is the one test that reads the stored bytes,
    and it is the only way to prove the sealing happened at the boundary."""
    await keys_repo.upsert(
        conn, user_id, provider="anthropic", label="default", secret=ANTHROPIC_KEY
    )

    ciphertext = (await stored_rows(conn, user_id))[0]["ciphertext"]
    assert ANTHROPIC_KEY.encode("utf-8") not in bytes(ciphertext)
    assert crypto_module.open_sealed(user_id, bytes(ciphertext)) == ANTHROPIC_KEY


async def test_the_stored_ciphertext_belongs_to_that_user_alone(
    keys_repo: ModuleType, crypto_module: ModuleType, conn: Any, user_id: str, other_user_id: str
) -> None:
    await keys_repo.upsert(
        conn, user_id, provider="anthropic", label="default", secret=ANTHROPIC_KEY
    )

    ciphertext = bytes((await stored_rows(conn, user_id))[0]["ciphertext"])
    with pytest.raises(Forbidden):
        crypto_module.open_sealed(other_user_id, ciphertext)


async def test_last_four_comes_from_the_end_of_the_plaintext(
    keys_repo: ModuleType, conn: Any, user_id: str
) -> None:
    await keys_repo.upsert(
        conn, user_id, provider="anthropic", label="default", secret=ANTHROPIC_KEY
    )

    assert (await stored_rows(conn, user_id))[0]["last_four"] == ANTHROPIC_KEY[-4:]


async def test_upserting_the_same_provider_and_label_replaces_the_key(
    keys_repo: ModuleType, crypto_module: ModuleType, conn: Any, user_id: str
) -> None:
    """Rotation, not accumulation. The unique index on (user_id, provider, label) says the same
    thing; this says the repository honours it instead of raising."""
    rotated = "sk-ant-rotated-9999"

    await keys_repo.upsert(
        conn, user_id, provider="anthropic", label="default", secret=ANTHROPIC_KEY
    )
    await keys_repo.upsert(conn, user_id, provider="anthropic", label="default", secret=rotated)

    rows = await stored_rows(conn, user_id)
    assert len(rows) == 1
    assert rows[0]["last_four"] == rotated[-4:]
    assert crypto_module.open_sealed(user_id, bytes(rows[0]["ciphertext"])) == rotated


async def test_a_second_label_is_a_second_key(
    keys_repo: ModuleType, conn: Any, user_id: str
) -> None:
    await keys_repo.upsert(
        conn, user_id, provider="anthropic", label="default", secret=ANTHROPIC_KEY
    )
    await keys_repo.upsert(
        conn, user_id, provider="anthropic", label="work", secret="sk-ant-work-4321"
    )

    assert len(await stored_rows(conn, user_id)) == 2


async def test_list_for_user_returns_key_rows(
    keys_repo: ModuleType, conn: Any, user_id: str
) -> None:
    await keys_repo.upsert(
        conn, user_id, provider="anthropic", label="default", secret=ANTHROPIC_KEY
    )

    rows = await keys_repo.list_for_user(conn, user_id)

    assert len(rows) == 1
    assert isinstance(rows[0], keys_repo.KeyRow)
    assert rows[0].provider == "anthropic"
    assert rows[0].last_four == ANTHROPIC_KEY[-4:]
    assert rows[0].created_at is not None


async def test_list_for_user_never_renders_the_secret(
    keys_repo: ModuleType, conn: Any, user_id: str
) -> None:
    """Acceptance criterion 3 on the row that reaches the API. The sentinel is distinctive enough
    that finding it anywhere in the rendered list is unambiguous."""
    await keys_repo.upsert(
        conn, user_id, provider="anthropic", label="default", secret=ANTHROPIC_KEY
    )

    rows = await keys_repo.list_for_user(conn, user_id)

    rendered = f"{rows!r} {[dataclasses.asdict(row) for row in rows]!r}"
    assert ANTHROPIC_KEY not in rendered
    assert ANTHROPIC_KEY[:-4] not in rendered


async def test_list_for_user_is_scoped_to_the_user(
    keys_repo: ModuleType, conn: Any, user_id: str, other_user_id: str
) -> None:
    await keys_repo.upsert(
        conn, user_id, provider="anthropic", label="default", secret=ANTHROPIC_KEY
    )

    assert await keys_repo.list_for_user(conn, other_user_id) == []


async def test_list_for_user_sees_every_provider(
    keys_repo: ModuleType, conn: Any, user_id: str
) -> None:
    await keys_repo.upsert(
        conn, user_id, provider="anthropic", label="default", secret=ANTHROPIC_KEY
    )
    await keys_repo.upsert(conn, user_id, provider="openai", label="default", secret=OPENAI_KEY)

    providers = {row.provider for row in await keys_repo.list_for_user(conn, user_id)}

    assert providers == {"anthropic", "openai"}


async def test_delete_removes_the_key(keys_repo: ModuleType, conn: Any, user_id: str) -> None:
    key_id = await keys_repo.upsert(
        conn, user_id, provider="anthropic", label="default", secret=ANTHROPIC_KEY
    )

    await keys_repo.delete(conn, user_id, key_id)

    assert await stored_rows(conn, user_id) == []


async def test_delete_does_not_reach_another_users_key(
    keys_repo: ModuleType, conn: Any, user_id: str, other_user_id: str
) -> None:
    """Whether a cross-user delete raises or is a no-op is the implementation's call. That it
    leaves the row alone is not."""
    key_id = await keys_repo.upsert(
        conn, user_id, provider="anthropic", label="default", secret=ANTHROPIC_KEY
    )

    with contextlib.suppress(AppError):
        await keys_repo.delete(conn, other_user_id, key_id)

    assert len(await stored_rows(conn, user_id)) == 1


async def test_mark_used_stamps_the_key(keys_repo: ModuleType, conn: Any, user_id: str) -> None:
    """`last_used_at` is what the keys page shows to answer "is this key still in use". It starts
    null and only a run sets it."""
    await keys_repo.upsert(
        conn, user_id, provider="anthropic", label="default", secret=ANTHROPIC_KEY
    )
    assert (await stored_rows(conn, user_id))[0]["last_used_at"] is None

    await keys_repo.mark_used(conn, user_id, "anthropic")

    assert (await stored_rows(conn, user_id))[0]["last_used_at"] is not None


async def test_mark_used_touches_only_that_provider(
    keys_repo: ModuleType, conn: Any, user_id: str
) -> None:
    await keys_repo.upsert(
        conn, user_id, provider="anthropic", label="default", secret=ANTHROPIC_KEY
    )
    await keys_repo.upsert(conn, user_id, provider="openai", label="default", secret=OPENAI_KEY)

    await keys_repo.mark_used(conn, user_id, "anthropic")

    stamped = {row["provider"]: row["last_used_at"] for row in await stored_rows(conn, user_id)}
    assert stamped["anthropic"] is not None
    assert stamped["openai"] is None


async def test_mark_used_touches_only_that_user(
    keys_repo: ModuleType, conn: Any, user_id: str, other_user_id: str
) -> None:
    await keys_repo.upsert(
        conn, user_id, provider="anthropic", label="default", secret=ANTHROPIC_KEY
    )
    await keys_repo.upsert(
        conn, other_user_id, provider="anthropic", label="default", secret=OPENAI_KEY
    )

    await keys_repo.mark_used(conn, user_id, "anthropic")

    assert (await stored_rows(conn, other_user_id))[0]["last_used_at"] is None
