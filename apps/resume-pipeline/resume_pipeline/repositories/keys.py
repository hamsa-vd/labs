"""BYOK provider keys, stored sealed (RG-023).

`resume_api_keys` in migration 0006 is the schema of record: one row per
`(user_id, provider, label)`, the key itself in a `bytea` `ciphertext` column, and a `last_four`
for the settings screen so a user can tell two keys apart without either being shown.

`KeyRow` has no field that can hold the secret. Not a masked one, not an optional one — a struct
with nowhere to put a key cannot leak one, and that is a stronger guarantee than remembering to
redact. The only function that returns ciphertext is `fetch_ciphertext`, which exists so SQL stays
inside `repositories/` and is called by `llm/credentials.py` alone.

Every statement is scoped by `user_id`. Ascend holds the identity and passes the resolved user in;
a bug there must not become a cross-tenant read.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from resume_pipeline.crypto import seal
from resume_pipeline.errors import NotFound, ValidationFailed

#: The providers the `resume_api_keys` check constraint accepts.
ALLOWED_PROVIDERS: tuple[str, ...] = ("anthropic", "openai", "openrouter")

DEFAULT_LABEL = "default"

_COLUMNS = "id, provider, label, last_four, created_at, last_used_at"


@dataclass(frozen=True)
class KeyRow:
    """One stored key, as the settings screen sees it. No field can hold the secret."""

    id: str
    provider: str
    label: str
    last_four: str
    created_at: datetime
    last_used_at: datetime | None = None


async def list_for_user(conn: Any, user_id: str) -> list[KeyRow]:
    """Every key this user has stored, newest first. Never includes the ciphertext."""
    rows = await conn.fetch(
        f"select {_COLUMNS} from resume_api_keys "
        "where user_id = $1::uuid order by created_at desc, provider asc",
        user_id,
    )
    return [_to_row(row) for row in rows]


async def upsert(
    conn: Any,
    user_id: str,
    *,
    provider: str,
    label: str = DEFAULT_LABEL,
    secret: str,
) -> str:
    """Seal `secret` and store it for this user, returning the row id.

    Re-adding a key under the same `(provider, label)` replaces it. `last_four` comes from the
    plaintext here and nowhere else, because this is the only place the plaintext exists.
    """
    _require_provider(provider)
    cleaned = secret.strip()
    if not cleaned:
        raise ValidationFailed(
            "That key is empty. Paste the key from your provider and save again.",
            details={"provider": provider},
        )
    ciphertext = seal(user_id, cleaned)
    last_four = cleaned[-4:]
    row = await conn.fetchrow(
        """
        insert into resume_api_keys (user_id, provider, label, ciphertext, last_four)
        values ($1::uuid, $2, $3, $4, $5)
        on conflict (user_id, provider, label) do update
          set ciphertext = excluded.ciphertext,
              last_four = excluded.last_four,
              last_used_at = null
        returning id
        """,
        user_id,
        provider,
        label or DEFAULT_LABEL,
        ciphertext,
        last_four,
    )
    return str(row["id"])


async def delete(conn: Any, user_id: str, key_id: str) -> None:
    """Remove one key. Raises `NotFound` when this user has no such key."""
    row = await conn.fetchrow(
        "delete from resume_api_keys where id = $1::uuid and user_id = $2::uuid returning id",
        key_id,
        user_id,
    )
    if row is None:
        raise NotFound("That key is no longer stored. Refresh the page to see your current keys.")


async def mark_used(conn: Any, user_id: str, provider: str) -> None:
    """Stamp `last_used_at` for this user's key for `provider`. Silent when there is none."""
    await conn.execute(
        "update resume_api_keys set last_used_at = now() "
        "where user_id = $1::uuid and provider = $2",
        user_id,
        provider,
    )


async def fetch_ciphertexts(
    conn: Any, user_id: str, providers: Sequence[str]
) -> dict[str, bytes]:
    """Every sealed key this user has for `providers`, in one round trip.

    One query rather than one per provider: a run resolves its keys once, and the number of
    database round trips a run makes should not depend on how many models it happens to use. A
    provider with no row is simply absent from the result — deciding that a missing key is fatal
    belongs to the caller that knows which providers the run actually needs.

    When a user has more than one key for a provider, the most recently added one wins.
    """
    wanted = list(dict.fromkeys(providers))
    if not wanted:
        return {}
    rows = await conn.fetch(
        "select provider, ciphertext from resume_api_keys "
        "where user_id = $1::uuid and provider = any($2::text[]) "
        "order by created_at desc",
        user_id,
        wanted,
    )
    found: dict[str, bytes] = {}
    for row in rows:
        provider = row["provider"]
        if provider not in wanted or provider in found:
            continue
        ciphertext = row["ciphertext"]
        if ciphertext is not None:
            found[provider] = bytes(ciphertext)
    return found


async def fetch_ciphertext(conn: Any, user_id: str, provider: str) -> bytes | None:
    """The sealed key for this user and provider, or `None`.

    These two are the only ciphertext-returning functions in the module, and their only caller is
    `llm/credentials.resolve_for_run`.
    """
    found = await fetch_ciphertexts(conn, user_id, [provider])
    return found.get(provider)


def _require_provider(provider: str) -> None:
    if provider not in ALLOWED_PROVIDERS:
        raise ValidationFailed(
            f"{provider} is not a provider this service stores keys for. "
            f"Choose one of: {', '.join(ALLOWED_PROVIDERS)}.",
            details={"provider": provider},
        )


def _to_row(row: Any) -> KeyRow:
    return KeyRow(
        id=str(row["id"]),
        provider=row["provider"],
        label=row["label"],
        last_four=row["last_four"],
        created_at=row["created_at"],
        last_used_at=row["last_used_at"],
    )
