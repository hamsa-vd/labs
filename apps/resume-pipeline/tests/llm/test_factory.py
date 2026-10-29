"""`clients_for_run` (WP4 §6) — what a run gets to call, and what it costs to find out.

Two acceptance criteria meet here and they pull in opposite directions.

**Fake mode costs nothing.** `LLM_MODE=fake` is the default everywhere except a deliberate live
run, so this path runs hundreds of times in CI. It must not read the key table, and it must not
care that the user has no keys at all. The test asserts that with a connection object that raises
on any attribute access: proving no query ran is stronger than proving the right rows came back.

**Live mode fails before it spends.** A missing key must raise `MissingApiKey` with the provider
in `details`, *before the graph starts*. A run that dies halfway has already paid for the calls it
made. "No LLM call was attempted" is asserted by making every client's `complete` explode — the
classes themselves, so it holds however the factory imported them.
"""

from __future__ import annotations

import dataclasses
import inspect
from types import ModuleType
from typing import Any

import pytest

from resume_pipeline.errors import MissingApiKey
from tests.llm.conftest import (
    SENTINEL_SECRET,
    ExplodingConnection,
    RecordingConnection,
    client_class,
    key_row,
)

USER = "22222222-2222-4222-8222-222222222222"
OPENAI_SENTINEL = "sk-openai-SENTINEL-do-not-render-9d4e2c"

ANTHROPIC_MODEL = "claude-sonnet-4-5"
OPENAI_MODEL = "gpt-4.1-mini"

ROLES = ("generation", "review", "revision")


def selection(factory_mod: ModuleType, generation: str, review: str, revision: str) -> Any:
    return factory_mod.ModelSelection(
        generation_model=generation, review_model=review, revision_model=revision
    )


def all_openai(factory_mod: ModuleType) -> Any:
    return selection(factory_mod, OPENAI_MODEL, OPENAI_MODEL, OPENAI_MODEL)


def all_anthropic(factory_mod: ModuleType) -> Any:
    return selection(factory_mod, ANTHROPIC_MODEL, ANTHROPIC_MODEL, ANTHROPIC_MODEL)


@pytest.fixture
def no_llm_call(
    monkeypatch: pytest.MonkeyPatch,
    anthropic_mod: ModuleType,
    openai_mod: ModuleType,
    fake_mod: ModuleType,
) -> None:
    """Make every client's `complete` fail, so "no LLM call was attempted" is provable."""

    async def _boom(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("An LLM call was attempted when none should have been.")

    monkeypatch.setattr(client_class(anthropic_mod), "complete", _boom)
    monkeypatch.setattr(client_class(openai_mod), "complete", _boom)
    monkeypatch.setattr(fake_mod.FakeLLMClient, "complete", _boom)


# ─── Shapes ───────────────────────────────────────────────────────────────────


def test_run_clients_holds_one_client_per_role(factory_mod: ModuleType) -> None:
    names = tuple(f.name for f in dataclasses.fields(factory_mod.RunClients))

    assert names == ROLES


def test_model_selection_names_one_model_per_role(factory_mod: ModuleType) -> None:
    names = tuple(f.name for f in dataclasses.fields(factory_mod.ModelSelection))

    assert names == ("generation_model", "review_model", "revision_model")


def test_clients_for_run_is_a_coroutine(factory_mod: ModuleType) -> None:
    assert inspect.iscoroutinefunction(factory_mod.clients_for_run)


def test_model_selection_has_v1s_split_as_its_default(factory_mod: ModuleType) -> None:
    """v1 ran a strong model for review, a generation model for writing, and a cheap one for
    revision. The contract says to preserve that as the default."""
    default = factory_mod.ModelSelection()

    assert default.generation_model
    assert default.review_model
    assert default.revision_model


def test_the_default_models_are_all_priced(factory_mod: ModuleType, pricing_mod: ModuleType) -> None:
    """A default nobody priced is a run that dies at the first cost rollup."""
    default = factory_mod.ModelSelection()

    for model in (default.generation_model, default.review_model, default.revision_model):
        assert model in pricing_mod.PRICES, f"{model} is a default with no price"


def test_the_default_revision_model_is_not_the_expensive_one(
    factory_mod: ModuleType, pricing_mod: ModuleType
) -> None:
    """"A cheap model revises" — the revision loop runs more often than anything else, so this is
    the one place where a careless default multiplies."""
    default = factory_mod.ModelSelection()
    revision = pricing_mod.price_for(default.revision_model)
    review = pricing_mod.price_for(default.review_model)

    assert revision.output_per_mtok <= review.output_per_mtok


# ─── Fake mode costs nothing ──────────────────────────────────────────────────


async def test_fake_mode_returns_three_fake_clients(
    factory_mod: ModuleType, fake_mod: ModuleType
) -> None:
    clients = await factory_mod.clients_for_run(
        ExplodingConnection(), USER, all_anthropic(factory_mod), mode="fake"
    )

    for role in ROLES:
        assert isinstance(getattr(clients, role), fake_mod.FakeLLMClient)


async def test_fake_mode_reads_no_keys_for_a_user_who_has_none(factory_mod: ModuleType) -> None:
    """Acceptance criterion 7. The connection raises on any attribute access, so a single query
    fails the test — including the one that would return an empty list."""
    conn = ExplodingConnection()

    await factory_mod.clients_for_run(conn, USER, all_anthropic(factory_mod), mode="fake")

    assert conn.touched == []


async def test_fake_mode_makes_no_network_call(factory_mod: ModuleType) -> None:
    """The suite-wide socket guard turns any connection attempt into a failure; this test exists
    to state the claim, and the guard enforces it."""
    clients = await factory_mod.clients_for_run(
        ExplodingConnection(), USER, all_openai(factory_mod), mode="fake"
    )

    completion = await clients.generation.complete(
        system_prompt="You are a resume tailoring system.",
        user_prompt="Return only a complete LaTeX document.",
    )

    assert "\\documentclass" in completion.text


async def test_fake_mode_ignores_a_selection_it_has_no_key_for(factory_mod: ModuleType) -> None:
    """A fake run must not require a key for the model it pretends to call, or no test of the
    graph can run without a seeded key table."""
    clients = await factory_mod.clients_for_run(
        ExplodingConnection(), USER, all_anthropic(factory_mod), mode="fake"
    )

    assert clients.review is not None


async def test_the_mode_defaults_to_the_settings_value(factory_mod: ModuleType, fake_mod: ModuleType) -> None:
    """`llm_mode` defaults to `fake`; live is opt-in, never the default. A stray dev process must
    not be able to spend the user's money by omission."""
    clients = await factory_mod.clients_for_run(
        ExplodingConnection(), USER, all_openai(factory_mod)
    )

    assert isinstance(clients.generation, fake_mod.FakeLLMClient)


# ─── Live mode fails before it spends ─────────────────────────────────────────


async def test_live_mode_raises_missing_api_key_when_the_provider_key_is_absent(
    factory_mod: ModuleType, no_llm_call: None
) -> None:
    conn = RecordingConnection([])

    with pytest.raises(MissingApiKey) as caught:
        await factory_mod.clients_for_run(conn, USER, all_anthropic(factory_mod), mode="live")

    assert caught.value.details["provider"] == "anthropic"


async def test_the_missing_key_error_names_the_provider_the_selection_needs(
    factory_mod: ModuleType, crypto_mod: ModuleType, no_llm_call: None
) -> None:
    """Only the providers the three models actually require are demanded. The user holding an
    OpenAI key and picking Claude gets told about Claude, not about keys in general."""
    conn = RecordingConnection([key_row(crypto_mod, USER, "openai", OPENAI_SENTINEL)])

    with pytest.raises(MissingApiKey) as caught:
        await factory_mod.clients_for_run(conn, USER, all_anthropic(factory_mod), mode="live")

    assert caught.value.details["provider"] == "anthropic"
    assert caught.value.code == "missing_api_key"


async def test_a_provider_the_run_does_not_use_is_not_required(
    factory_mod: ModuleType, crypto_mod: ModuleType
) -> None:
    conn = RecordingConnection([key_row(crypto_mod, USER, "openai", OPENAI_SENTINEL)])

    clients = await factory_mod.clients_for_run(conn, USER, all_openai(factory_mod), mode="live")

    assert clients.generation.provider == "openai"


async def test_the_missing_key_error_carries_no_key(
    factory_mod: ModuleType, crypto_mod: ModuleType, no_llm_call: None
) -> None:
    conn = RecordingConnection([key_row(crypto_mod, USER, "openai", OPENAI_SENTINEL)])

    with pytest.raises(MissingApiKey) as caught:
        await factory_mod.clients_for_run(conn, USER, all_anthropic(factory_mod), mode="live")

    rendered = f"{caught.value!s} {caught.value!r} {caught.value.details!r}"
    assert OPENAI_SENTINEL not in rendered
    assert SENTINEL_SECRET not in rendered


async def test_live_mode_routes_each_model_to_its_provider(
    factory_mod: ModuleType, crypto_mod: ModuleType
) -> None:
    conn = RecordingConnection(
        [
            key_row(crypto_mod, USER, "anthropic", SENTINEL_SECRET),
            key_row(crypto_mod, USER, "openai", OPENAI_SENTINEL),
        ]
    )
    chosen = selection(factory_mod, OPENAI_MODEL, ANTHROPIC_MODEL, OPENAI_MODEL)

    clients = await factory_mod.clients_for_run(conn, USER, chosen, mode="live")

    assert clients.generation.provider == "openai"
    assert clients.review.provider == "anthropic"
    assert clients.revision.provider == "openai"


async def test_live_mode_hands_each_client_its_model(
    factory_mod: ModuleType, crypto_mod: ModuleType
) -> None:
    conn = RecordingConnection(
        [
            key_row(crypto_mod, USER, "anthropic", SENTINEL_SECRET),
            key_row(crypto_mod, USER, "openai", OPENAI_SENTINEL),
        ]
    )
    chosen = selection(factory_mod, OPENAI_MODEL, ANTHROPIC_MODEL, OPENAI_MODEL)

    clients = await factory_mod.clients_for_run(conn, USER, chosen, mode="live")

    assert clients.generation.model == OPENAI_MODEL
    assert clients.review.model == ANTHROPIC_MODEL
    assert clients.revision.model == OPENAI_MODEL


async def test_live_mode_does_not_return_a_fake(
    factory_mod: ModuleType, fake_mod: ModuleType, crypto_mod: ModuleType
) -> None:
    """A live run that silently fell back to the fake would produce a plausible resume from no
    model at all, and the user would be charged nothing for a document that means nothing."""
    conn = RecordingConnection([key_row(crypto_mod, USER, "openai", OPENAI_SENTINEL)])

    clients = await factory_mod.clients_for_run(conn, USER, all_openai(factory_mod), mode="live")

    for role in ROLES:
        assert not isinstance(getattr(clients, role), fake_mod.FakeLLMClient)


async def test_live_mode_reads_the_keys_once_for_the_whole_run(
    factory_mod: ModuleType, crypto_mod: ModuleType
) -> None:
    conn = RecordingConnection([key_row(crypto_mod, USER, "openai", OPENAI_SENTINEL)])

    await factory_mod.clients_for_run(conn, USER, all_openai(factory_mod), mode="live")

    assert conn.query_count == 1


async def test_live_mode_scopes_the_key_lookup_to_the_user(
    factory_mod: ModuleType, crypto_mod: ModuleType
) -> None:
    conn = RecordingConnection([key_row(crypto_mod, USER, "openai", OPENAI_SENTINEL)])

    await factory_mod.clients_for_run(conn, USER, all_openai(factory_mod), mode="live")

    assert USER in conn.all_args


async def test_no_client_renders_its_key(
    factory_mod: ModuleType, crypto_mod: ModuleType
) -> None:
    conn = RecordingConnection(
        [
            key_row(crypto_mod, USER, "anthropic", SENTINEL_SECRET),
            key_row(crypto_mod, USER, "openai", OPENAI_SENTINEL),
        ]
    )
    chosen = selection(factory_mod, OPENAI_MODEL, ANTHROPIC_MODEL, OPENAI_MODEL)

    clients = await factory_mod.clients_for_run(conn, USER, chosen, mode="live")

    rendered = repr(clients)
    assert SENTINEL_SECRET not in rendered
    assert OPENAI_SENTINEL not in rendered
