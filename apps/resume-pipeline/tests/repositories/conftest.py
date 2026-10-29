"""Fixtures for the WP3 repository tests.

Three things live here.

**A hole in the suite-wide socket guard, for loopback Postgres only.** `tests/conftest.py` is
autouse and correct — no test in this repository may reach the network — but a repository is a
statement about SQL, and a repository test that mocks the database tests nothing. So this conftest
re-patches the socket API with an allowlist: `127.0.0.1`, `localhost`, `::1` and unix sockets go
through, everything else still raises `NetworkAccessAttempted`. The shared guard is not edited.

**Opt-in database discovery.** `RESUME_DATABASE_URL`, then `TEST_DATABASE_URL`. With neither set
the tests skip and the default suite stays offline.

**Transactional isolation.** Every test runs inside a transaction that is rolled back afterwards,
so a repeated run is idempotent and two agents can share one dev database without tripping over
each other's rows. Emails are unique per run on top of that, so even a rollback that does not
happen cannot collide.

`tests/test_telemetry.py` imports the helpers below rather than duplicating them; a conftest cannot
reach up a directory, and telemetry's accumulation test needs the same database.
"""

from __future__ import annotations

import asyncio
import os
import re
import socket
import uuid
from collections.abc import AsyncIterator, Iterator
from typing import Any

import asyncpg
import pytest

from tests.conftest import NetworkAccessAttempted

DB_URL_ENVS = ("RESUME_DATABASE_URL", "TEST_DATABASE_URL")

LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1", "0.0.0.0", ""}

# Captured at import time, before `tests/conftest.py::_no_network` monkeypatches them.
_REAL = {
    "connect": socket.socket.connect,
    "connect_ex": socket.socket.connect_ex,
    "sendto": socket.socket.sendto,
    "create_connection": socket.create_connection,
    "getaddrinfo": socket.getaddrinfo,
}


# ─── Socket guard: loopback Postgres only ─────────────────────────────────────


def _is_local(address: Any) -> bool:
    if isinstance(address, tuple) and address:
        return str(address[0]) in LOCAL_HOSTS
    if isinstance(address, str):
        return address.startswith("/")  # a unix domain socket
    return False


def _refuse(address: Any) -> NetworkAccessAttempted:
    return NetworkAccessAttempted(
        f"A test tried to reach {address!r}. Repository tests may talk to a loopback Postgres "
        "and nothing else."
    )


def allow_localhost_sockets(monkeypatch: pytest.MonkeyPatch) -> None:
    """Re-open the socket API for loopback addresses only, on top of the shared guard."""

    def connect(self: socket.socket, address: Any) -> Any:
        if not _is_local(address):
            raise _refuse(address)
        return _REAL["connect"](self, address)

    def connect_ex(self: socket.socket, address: Any) -> Any:
        if not _is_local(address):
            raise _refuse(address)
        return _REAL["connect_ex"](self, address)

    def create_connection(address: Any, *args: Any, **kwargs: Any) -> Any:
        if not _is_local(address):
            raise _refuse(address)
        return _REAL["create_connection"](address, *args, **kwargs)

    def getaddrinfo(host: Any, *args: Any, **kwargs: Any) -> Any:
        if str(host) not in LOCAL_HOSTS:
            raise _refuse(host)
        return _REAL["getaddrinfo"](host, *args, **kwargs)

    monkeypatch.setattr(socket.socket, "connect", connect)
    monkeypatch.setattr(socket.socket, "connect_ex", connect_ex)
    monkeypatch.setattr(socket, "create_connection", create_connection)
    monkeypatch.setattr(socket, "getaddrinfo", getaddrinfo)


@pytest.fixture(autouse=True)
def _loopback_postgres(monkeypatch: pytest.MonkeyPatch) -> None:
    allow_localhost_sockets(monkeypatch)


# ─── Database discovery ───────────────────────────────────────────────────────


def candidate_database_urls() -> list[tuple[str, str]]:
    """Every configured URL, in the contract's order of preference."""
    found = []
    for name in DB_URL_ENVS:
        value = os.environ.get(name, "").strip()
        if value:
            found.append((name, value))
    return found


def _sanitise(url: str) -> str:
    """A DSN without its credentials, safe to put in a skip message."""
    return re.sub(r"//[^/@]*@", "//", url)


_PROBE_CACHE: dict[str, str | None] = {}


def probe(url: str) -> str | None:
    """`None` when the database answers, otherwise the reason it did not.

    Other packages in this suite provision a fallback `RESUME_DATABASE_URL` so that
    `resume_pipeline.settings` can import, and that fallback points at a database that does not
    exist. A configured URL is therefore not proof of a database, and "skip cleanly when absent"
    has to mean "when absent or unreachable" or the default suite errors instead of skipping.
    """
    if url in _PROBE_CACHE:
        return _PROBE_CACHE[url]

    async def attempt() -> str | None:
        try:
            connection = await asyncpg.connect(url)
        except Exception as exc:  # noqa: BLE001 - any failure to reach it means the same thing
            return f"{type(exc).__name__}: {exc}"
        await connection.close()
        return None

    reason = asyncio.run(attempt())
    _PROBE_CACHE[url] = reason
    return reason


def require_database_url() -> str:
    candidates = candidate_database_urls()
    if not candidates:
        pytest.skip(
            "No database. Set RESUME_DATABASE_URL (or TEST_DATABASE_URL) to a Postgres "
            "instance with the resume generator migrations applied."
        )

    reasons = []
    for name, url in candidates:
        reason = probe(url)
        if reason is None:
            return url
        reasons.append(f"{name} ({_sanitise(url)}): {reason}")

    pytest.skip("No reachable database. " + "; ".join(reasons))


@pytest.fixture
def database_url(_loopback_postgres: None) -> str:
    # Function-scoped, because the probe needs the socket allowlist above to be in place.
    return require_database_url()


# ─── Connections and rows ─────────────────────────────────────────────────────


async def open_connection(url: str) -> asyncpg.Connection:
    return await asyncpg.connect(url)


async def create_user(conn: asyncpg.Connection) -> str:
    """One `app_users` row with an email unique to this run."""
    email = f"wp3-test-{uuid.uuid4().hex}@example.invalid"
    row = await conn.fetchrow("insert into app_users (email) values ($1) returning id", email)
    return str(row["id"])


@pytest.fixture
async def conn(database_url: str) -> AsyncIterator[asyncpg.Connection]:
    """A connection inside a transaction that is always rolled back."""
    connection = await open_connection(database_url)
    transaction = connection.transaction()
    await transaction.start()
    try:
        yield connection
    finally:
        await transaction.rollback()
        await connection.close()


@pytest.fixture
async def user_a(conn: asyncpg.Connection) -> str:
    return await create_user(conn)


@pytest.fixture
async def user_b(conn: asyncpg.Connection) -> str:
    return await create_user(conn)


# ─── Lazy module imports ──────────────────────────────────────────────────────


def import_module_or_fail(name: str) -> Any:
    import importlib

    try:
        return importlib.import_module(name)
    except ModuleNotFoundError as exc:  # pragma: no cover - only before WP3 source lands
        pytest.fail(f"WP3 has not provided `{name}` yet ({exc}).", pytrace=False)


@pytest.fixture(scope="session")
def applications_repo() -> Any:
    return import_module_or_fail("resume_pipeline.repositories.applications")


@pytest.fixture(scope="session")
def documents_repo() -> Any:
    return import_module_or_fail("resume_pipeline.repositories.documents")


@pytest.fixture(scope="session")
def runs_repo() -> Any:
    return import_module_or_fail("resume_pipeline.repositories.runs")


# ─── Row access ───────────────────────────────────────────────────────────────

_MISSING = object()


def field(row: Any, *names: str) -> Any:
    """Read a column from a row without assuming it is a mapping, a record or a dataclass.

    The contract names `ApplicationRow` and `DocumentRow` but does not say what they are, so this
    suite asserts on values rather than on the container.
    """
    for name in names:
        value = getattr(row, name, _MISSING)
        if value is not _MISSING:
            return value
        try:
            return row[name]
        except (TypeError, KeyError, IndexError):
            continue
    raise AssertionError(f"row {row!r} has none of the fields {names}")


def as_str(value: Any) -> str:
    return str(value) if value is not None else ""


@pytest.fixture
def unique() -> Iterator[str]:
    """A token unique to this test, for building company names that cannot collide."""
    yield uuid.uuid4().hex[:12]
