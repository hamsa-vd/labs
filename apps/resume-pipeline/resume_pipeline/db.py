"""The connection pool (RG-004).

One lazily created pool per process, reused. Nothing outside `repositories/` executes SQL: a
query written in a router or a graph node is a query nobody remembered to scope by `user_id`.

`transaction()` exists so that a caller can span several repository calls — recording an LLM call
and advancing a run, say — without either of them opening its own connection and losing
atomicity.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import asyncpg  # type: ignore[import-untyped]

from resume_pipeline.settings import get_settings

_pool: asyncpg.Pool[Any] | None = None
_lock = asyncio.Lock()

#: Small on purpose. This service is one process serving one user's ascend instance; a large pool
#: would only hold idle connections open against the same Postgres ascend itself is using.
MIN_POOL_SIZE = 1
MAX_POOL_SIZE = 10
COMMAND_TIMEOUT_SECONDS = 30.0


async def pool() -> asyncpg.Pool[Any]:
    global _pool
    if _pool is not None:
        return _pool
    async with _lock:
        if _pool is None:
            _pool = await asyncpg.create_pool(
                dsn=get_settings().database_url,
                min_size=MIN_POOL_SIZE,
                max_size=MAX_POOL_SIZE,
                command_timeout=COMMAND_TIMEOUT_SECONDS,
            )
    assert _pool is not None
    return _pool


async def close_pool() -> None:
    global _pool
    async with _lock:
        if _pool is not None:
            await _pool.close()
            _pool = None


@asynccontextmanager
async def connection() -> AsyncIterator[asyncpg.Connection[Any]]:
    acquired = await pool()
    async with acquired.acquire() as conn:
        yield conn


@asynccontextmanager
async def transaction() -> AsyncIterator[asyncpg.Connection[Any]]:
    async with connection() as conn, conn.transaction():
        yield conn
