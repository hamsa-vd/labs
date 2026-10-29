"""`RunCredentials` and `resolve_for_run` (WP4 §5).

This is the one object in the system that holds a user's API keys in the clear. It exists for the
length of one run, inside the pipeline process, and the contract's requirement is blunt: a key is
never bound to a log context, never in an exception message, never written to `resume_runs` jsonb,
and never rendered by `repr`.

The tests below prove that by sealing a sentinel no implementation could produce by accident and
grepping every rendered form for it — `repr`, `str`, an f-string, `dataclasses.asdict`, a JSON
round trip, and the text of the error raised when a key is missing. A dataclass's default `repr`
prints every field, so `__repr__` has to be written by hand; this suite is what notices when it
was not.

The second claim is scoping. `resolve_for_run` reads keys for one user, once. A query that forgets
`user_id` reads another tenant's keys, and no other test in the system would catch it.
"""

from __future__ import annotations

import dataclasses
import inspect
import json
from types import ModuleType
from typing import Any

import pytest

from resume_pipeline.errors import MissingApiKey
from tests.llm.conftest import SENTINEL_SECRET, RecordingConnection, key_row

USER_A = "11111111-1111-4111-8111-111111111111"
OPENAI_SENTINEL = "sk-openai-SENTINEL-do-not-render-9d4e2c"


def credentials(credentials_mod: ModuleType, **keys: str) -> Any:
    return credentials_mod.RunCredentials(keys=keys)


# ─── require ──────────────────────────────────────────────────────────────────


def test_require_returns_the_key(credentials_mod: ModuleType) -> None:
    creds = credentials(credentials_mod, anthropic=SENTINEL_SECRET)

    assert creds.require("anthropic") == SENTINEL_SECRET


def test_require_raises_missing_api_key_for_a_provider_with_no_key(
    credentials_mod: ModuleType,
) -> None:
    creds = credentials(credentials_mod, anthropic=SENTINEL_SECRET)

    with pytest.raises(MissingApiKey):
        creds.require("openai")


def test_the_missing_key_error_names_the_provider_in_details(
    credentials_mod: ModuleType,
) -> None:
    """The UI routes the user to the right row of the keys page from `details.provider`. Without
    it the message is "add a key" with no way to know which."""
    creds = credentials(credentials_mod, anthropic=SENTINEL_SECRET)

    with pytest.raises(MissingApiKey) as caught:
        creds.require("openai")

    assert caught.value.details["provider"] == "openai"
    assert caught.value.code == "missing_api_key"
    assert caught.value.status == 400


def test_the_missing_key_error_carries_no_other_key(credentials_mod: ModuleType) -> None:
    creds = credentials(credentials_mod, anthropic=SENTINEL_SECRET, openrouter=OPENAI_SENTINEL)

    with pytest.raises(MissingApiKey) as caught:
        creds.require("openai")

    rendered = f"{caught.value!s} {caught.value!r} {caught.value.details!r}"
    assert SENTINEL_SECRET not in rendered
    assert OPENAI_SENTINEL not in rendered


def test_the_missing_key_message_follows_the_house_voice(credentials_mod: ModuleType) -> None:
    creds = credentials(credentials_mod)

    with pytest.raises(MissingApiKey) as caught:
        creds.require("anthropic")

    assert caught.value.message.strip() != ""
    assert "!" not in caught.value.message


def test_run_credentials_is_frozen(credentials_mod: ModuleType) -> None:
    creds = credentials(credentials_mod, anthropic=SENTINEL_SECRET)

    with pytest.raises((dataclasses.FrozenInstanceError, AttributeError, TypeError)):
        creds.keys = {}  # type: ignore[misc]


# ─── Nothing renders the key ──────────────────────────────────────────────────


def test_repr_does_not_render_the_key(credentials_mod: ModuleType) -> None:
    creds = credentials(credentials_mod, anthropic=SENTINEL_SECRET, openai=OPENAI_SENTINEL)

    assert SENTINEL_SECRET not in repr(creds)
    assert OPENAI_SENTINEL not in repr(creds)


def test_str_does_not_render_the_key(credentials_mod: ModuleType) -> None:
    creds = credentials(credentials_mod, anthropic=SENTINEL_SECRET)

    assert SENTINEL_SECRET not in str(creds)


def test_an_f_string_does_not_render_the_key(credentials_mod: ModuleType) -> None:
    """`f"{creds}"` and `f"{creds!r}"` are how a key reaches a log line by accident."""
    creds = credentials(credentials_mod, anthropic=SENTINEL_SECRET)

    assert SENTINEL_SECRET not in f"resolved {creds} for the run"
    assert SENTINEL_SECRET not in f"resolved {creds!r} for the run"


def test_a_container_holding_the_credentials_does_not_render_the_key(
    credentials_mod: ModuleType,
) -> None:
    """A structlog event dict holding the object renders it with `repr`, one level down."""
    creds = credentials(credentials_mod, anthropic=SENTINEL_SECRET)

    assert SENTINEL_SECRET not in repr({"credentials": creds})
    assert SENTINEL_SECRET not in repr([creds])


def test_asdict_does_not_serialise_the_key(credentials_mod: ModuleType) -> None:
    """Acceptance criterion 3 says "or a serialised form". `dataclasses.asdict` is the serialised
    form the run service would reach for when writing the run row, and a plain field is copied
    into it whatever `__repr__` does."""
    creds = credentials(credentials_mod, anthropic=SENTINEL_SECRET)

    rendered = json.dumps(dataclasses.asdict(creds), default=str)

    assert SENTINEL_SECRET not in rendered


def test_a_json_round_trip_does_not_carry_the_key(credentials_mod: ModuleType) -> None:
    creds = credentials(credentials_mod, anthropic=SENTINEL_SECRET)

    rendered = json.dumps({"credentials": creds}, default=str)

    assert SENTINEL_SECRET not in rendered


def test_the_keys_are_still_reachable_through_require(credentials_mod: ModuleType) -> None:
    """Hiding the keys from every rendered form must not hide them from the caller that needs
    them — otherwise the tests above pass on an object that cannot do its job."""
    creds = credentials(credentials_mod, anthropic=SENTINEL_SECRET, openai=OPENAI_SENTINEL)

    assert creds.require("anthropic") == SENTINEL_SECRET
    assert creds.require("openai") == OPENAI_SENTINEL


# ─── resolve_for_run ──────────────────────────────────────────────────────────


def test_resolve_for_run_is_a_coroutine(credentials_mod: ModuleType) -> None:
    assert inspect.iscoroutinefunction(credentials_mod.resolve_for_run)


async def test_resolve_for_run_decrypts_the_stored_key(
    credentials_mod: ModuleType, crypto_mod: ModuleType
) -> None:
    conn = RecordingConnection([key_row(crypto_mod, USER_A, "anthropic", SENTINEL_SECRET)])

    creds = await credentials_mod.resolve_for_run(conn, USER_A, ["anthropic"])

    assert creds.require("anthropic") == SENTINEL_SECRET


async def test_resolve_for_run_handles_several_providers(
    credentials_mod: ModuleType, crypto_mod: ModuleType
) -> None:
    conn = RecordingConnection(
        [
            key_row(crypto_mod, USER_A, "anthropic", SENTINEL_SECRET),
            key_row(crypto_mod, USER_A, "openai", OPENAI_SENTINEL),
        ]
    )

    creds = await credentials_mod.resolve_for_run(conn, USER_A, ["anthropic", "openai"])

    assert creds.require("anthropic") == SENTINEL_SECRET
    assert creds.require("openai") == OPENAI_SENTINEL


async def test_resolve_for_run_reads_the_keys_once(
    credentials_mod: ModuleType, crypto_mod: ModuleType
) -> None:
    """"Decrypts once per run" — a per-call read would put the ciphertext on the wire once per
    node and decrypt it a dozen times a run."""
    conn = RecordingConnection(
        [
            key_row(crypto_mod, USER_A, "anthropic", SENTINEL_SECRET),
            key_row(crypto_mod, USER_A, "openai", OPENAI_SENTINEL),
        ]
    )

    await credentials_mod.resolve_for_run(conn, USER_A, ["anthropic", "openai"])

    assert conn.query_count == 1


async def test_resolve_for_run_scopes_the_query_to_the_user(
    credentials_mod: ModuleType, crypto_mod: ModuleType
) -> None:
    """A query that forgets `user_id` reads another tenant's keys, and every row it gets back
    decrypts to nothing — which looks like "no key" rather than like a breach."""
    conn = RecordingConnection([key_row(crypto_mod, USER_A, "anthropic", SENTINEL_SECRET)])

    await credentials_mod.resolve_for_run(conn, USER_A, ["anthropic"])

    assert USER_A in conn.all_args


async def test_a_provider_with_no_row_is_simply_absent(
    credentials_mod: ModuleType, crypto_mod: ModuleType
) -> None:
    """Resolution does not raise; the preflight in the factory decides what a missing key means,
    so a run that needs only one of the two providers still starts."""
    conn = RecordingConnection([key_row(crypto_mod, USER_A, "anthropic", SENTINEL_SECRET)])

    creds = await credentials_mod.resolve_for_run(conn, USER_A, ["anthropic", "openai"])

    with pytest.raises(MissingApiKey) as caught:
        creds.require("openai")
    assert caught.value.details["provider"] == "openai"


async def test_resolved_credentials_hold_plaintext_not_ciphertext(
    credentials_mod: ModuleType, crypto_mod: ModuleType
) -> None:
    row = key_row(crypto_mod, USER_A, "anthropic", SENTINEL_SECRET)
    conn = RecordingConnection([row])

    creds = await credentials_mod.resolve_for_run(conn, USER_A, ["anthropic"])

    resolved = creds.require("anthropic")
    assert isinstance(resolved, str)
    assert resolved == SENTINEL_SECRET
    assert resolved.encode("utf-8") != row["ciphertext"]


async def test_resolved_credentials_do_not_render_the_key(
    credentials_mod: ModuleType, crypto_mod: ModuleType
) -> None:
    conn = RecordingConnection([key_row(crypto_mod, USER_A, "anthropic", SENTINEL_SECRET)])

    creds = await credentials_mod.resolve_for_run(conn, USER_A, ["anthropic"])

    assert SENTINEL_SECRET not in repr(creds)
    assert SENTINEL_SECRET not in str(creds)


async def test_no_key_at_all_still_resolves(credentials_mod: ModuleType) -> None:
    conn = RecordingConnection([])

    creds = await credentials_mod.resolve_for_run(conn, USER_A, ["anthropic"])

    with pytest.raises(MissingApiKey):
        creds.require("anthropic")
