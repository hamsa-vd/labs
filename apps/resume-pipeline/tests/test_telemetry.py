"""`resume_pipeline.telemetry.record_llm_call` (WP3 §3, acceptance criterion 9).

Cost accounting is the one place in this service where being approximately right is worse than
failing, because an approximate cost looks exactly like a correct one on a dashboard. Two rules
follow from the contract and both are tested against a real database, since "inserts one row and
increments two aggregates in the same transaction" is a claim about SQL.

**Accumulation is per node and per run.** Three calls spanning two providers must produce three
rows, one summed `cost_usd` on the run, and a `token_usage` rollup keyed by node — with money
carried as a string so that no `float` ever touches it.

**An unpriced model is a hard failure.** Not a zero, not a null: `UpstreamFailed` naming the model,
with nothing written. A silent zero is how a cost bug survives to production.

The fixtures come from `tests/repositories/conftest.py` because a conftest cannot reach up a
directory and this module needs the same loopback-Postgres arrangement.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator
from decimal import Decimal
from typing import Any

import asyncpg
import pytest

from resume_pipeline.errors import UpstreamFailed
from tests.repositories.conftest import (
    allow_localhost_sockets,
    create_user,
    import_module_or_fail,
    open_connection,
    require_database_url,
)

UNPRICED_MODEL = "gpt-nonexistent-9000"


@pytest.fixture(autouse=True)
def _loopback_postgres(monkeypatch: pytest.MonkeyPatch) -> None:
    allow_localhost_sockets(monkeypatch)


@pytest.fixture
def database_url(_loopback_postgres: None) -> str:
    return require_database_url()


@pytest.fixture(scope="session")
def telemetry() -> Any:
    return import_module_or_fail("resume_pipeline.telemetry")


@pytest.fixture(scope="session")
def pricing() -> Any:
    return import_module_or_fail("resume_pipeline.llm.pricing")


@pytest.fixture
async def conn(database_url: str) -> AsyncIterator[asyncpg.Connection]:
    connection = await open_connection(database_url)
    transaction = connection.transaction()
    await transaction.start()
    try:
        yield connection
    finally:
        await transaction.rollback()
        await connection.close()


@pytest.fixture
async def user_id(conn: asyncpg.Connection) -> str:
    return await create_user(conn)


@pytest.fixture
async def run_id(conn: asyncpg.Connection, user_id: str) -> str:
    application = await conn.fetchrow(
        """
        insert into applications
            (user_id, company_norm, company_display, role_title, first_seen_at,
             current_status, status_as_of, origin)
        values ($1, 'liv-ex', 'Liv-ex Ltd.', 'Senior Backend Engineer', now(),
                'draft', now(), 'generated')
        returning id
        """,
        uuid.UUID(user_id),
    )
    run = await conn.fetchrow(
        "insert into resume_runs (user_id, application_id) values ($1, $2) returning id",
        uuid.UUID(user_id),
        application["id"],
    )
    return str(run["id"])


def _model(pricing: Any, marker: str) -> str:
    for model in sorted(pricing.PRICES):
        if marker in model.lower():
            return model
    pytest.fail(f"the pricing table has no {marker} model to account for", pytrace=False)


async def _run_row(conn: asyncpg.Connection, run_id: str) -> asyncpg.Record:
    row = await conn.fetchrow(
        "select cost_usd, token_usage from resume_runs where id = $1", uuid.UUID(run_id)
    )
    assert row is not None
    return row


def _usage_rollup(row: asyncpg.Record) -> dict[str, Any]:
    raw = row["token_usage"]
    return json.loads(raw) if isinstance(raw, str) else dict(raw)


# ─── Criterion 9: three calls, two providers ──────────────────────────────────


async def test_three_calls_across_two_providers_accumulate(
    telemetry: Any, pricing: Any, conn: asyncpg.Connection, user_id: str, run_id: str
) -> None:
    openai_model = _model(pricing, "gpt")
    anthropic_model = _model(pricing, "claude")

    first_usage = telemetry.LlmUsage(input_tokens=1_000, output_tokens=500)
    second_usage = telemetry.LlmUsage(input_tokens=2_000, output_tokens=700)
    third_usage = telemetry.LlmUsage(input_tokens=3_000, output_tokens=900)

    first = await telemetry.record_llm_call(
        conn, run_id=run_id, user_id=user_id, node="generate", provider="openai",
        model=openai_model, usage=first_usage, latency_ms=1_200,
    )
    second = await telemetry.record_llm_call(
        conn, run_id=run_id, user_id=user_id, node="generate", provider="openai",
        model=openai_model, usage=second_usage, latency_ms=900,
    )
    third = await telemetry.record_llm_call(
        conn, run_id=run_id, user_id=user_id, node="review", provider="anthropic",
        model=anthropic_model, usage=third_usage, latency_ms=2_500,
    )

    # Each call returns its own cost, as a Decimal.
    assert first == pricing.cost_of(openai_model, first_usage)
    assert second == pricing.cost_of(openai_model, second_usage)
    assert third == pricing.cost_of(anthropic_model, third_usage)
    for cost in (first, second, third):
        assert isinstance(cost, Decimal)

    # Three rows, with the counts and the provider on each.
    rows = await conn.fetch(
        "select * from resume_llm_calls where run_id = $1 order by created_at, id",
        uuid.UUID(run_id),
    )
    assert len(rows) == 3
    assert [row["provider"] for row in rows].count("openai") == 2
    assert [row["provider"] for row in rows].count("anthropic") == 1
    assert {row["node"] for row in rows} == {"generate", "review"}
    assert all(str(row["user_id"]) == user_id for row in rows)
    assert sum(row["input_tokens"] for row in rows) == 6_000
    assert sum(row["output_tokens"] for row in rows) == 2_100
    assert sum(row["cost_usd"] for row in rows) == first + second + third

    # One summed cost on the run.
    run_row = await _run_row(conn, run_id)
    assert run_row["cost_usd"] == first + second + third

    # And a rollup keyed by node.
    usage = _usage_rollup(run_row)
    assert usage["generate"]["input_tokens"] == 3_000
    assert usage["generate"]["output_tokens"] == 1_200
    assert usage["generate"]["calls"] == 2
    assert Decimal(usage["generate"]["cost_usd"]) == first + second

    assert usage["review"]["input_tokens"] == 3_000
    assert usage["review"]["output_tokens"] == 900
    assert usage["review"]["calls"] == 1
    assert Decimal(usage["review"]["cost_usd"]) == third


async def test_money_in_the_rollup_is_a_string_not_a_float(
    telemetry: Any, pricing: Any, conn: asyncpg.Connection, user_id: str, run_id: str
) -> None:
    """A float here is a rounding error waiting for a big enough number of calls."""
    model = _model(pricing, "claude")
    await telemetry.record_llm_call(
        conn, run_id=run_id, user_id=user_id, node="review", provider="anthropic",
        model=model, usage=telemetry.LlmUsage(input_tokens=1_000, output_tokens=1_000),
    )

    usage = _usage_rollup(await _run_row(conn, run_id))
    assert isinstance(usage["review"]["cost_usd"], str)
    assert isinstance(usage["review"]["input_tokens"], int)
    assert isinstance(usage["review"]["calls"], int)


async def test_the_first_call_starts_the_rollup_from_zero(
    telemetry: Any, pricing: Any, conn: asyncpg.Connection, user_id: str, run_id: str
) -> None:
    model = _model(pricing, "gpt")
    cost = await telemetry.record_llm_call(
        conn, run_id=run_id, user_id=user_id, node="targeting", provider="openai",
        model=model, usage=telemetry.LlmUsage(input_tokens=100, output_tokens=50),
    )

    run_row = await _run_row(conn, run_id)
    assert run_row["cost_usd"] == cost
    assert _usage_rollup(run_row)["targeting"]["calls"] == 1


async def test_the_prompts_key_the_run_service_owns_is_not_clobbered(
    telemetry: Any, pricing: Any, conn: asyncpg.Connection, user_id: str, run_id: str
) -> None:
    """`token_usage` carries a `prompts` key written elsewhere; a rollup must merge, not replace."""
    await conn.execute(
        "update resume_runs set token_usage = $2 where id = $1",
        uuid.UUID(run_id),
        json.dumps({"prompts": {"generation": "v3"}}),
    )

    model = _model(pricing, "gpt")
    await telemetry.record_llm_call(
        conn, run_id=run_id, user_id=user_id, node="generate", provider="openai",
        model=model, usage=telemetry.LlmUsage(input_tokens=10, output_tokens=10),
    )

    usage = _usage_rollup(await _run_row(conn, run_id))
    assert usage["prompts"] == {"generation": "v3"}
    assert usage["generate"]["calls"] == 1


async def test_latency_is_recorded_and_optional(
    telemetry: Any, pricing: Any, conn: asyncpg.Connection, user_id: str, run_id: str
) -> None:
    model = _model(pricing, "gpt")
    await telemetry.record_llm_call(
        conn, run_id=run_id, user_id=user_id, node="generate", provider="openai",
        model=model, usage=telemetry.LlmUsage(input_tokens=10, output_tokens=10),
        latency_ms=1_234,
    )
    await telemetry.record_llm_call(
        conn, run_id=run_id, user_id=user_id, node="review", provider="openai",
        model=model, usage=telemetry.LlmUsage(input_tokens=10, output_tokens=10),
    )

    rows = await conn.fetch(
        "select node, latency_ms from resume_llm_calls where run_id = $1", uuid.UUID(run_id)
    )
    latencies = {row["node"]: row["latency_ms"] for row in rows}
    assert latencies["generate"] == 1_234
    assert latencies["review"] is None


async def test_a_zero_token_call_is_still_recorded(
    telemetry: Any, pricing: Any, conn: asyncpg.Connection, user_id: str, run_id: str
) -> None:
    """A cached or refused call cost nothing, but it happened and the count says so."""
    model = _model(pricing, "gpt")
    cost = await telemetry.record_llm_call(
        conn, run_id=run_id, user_id=user_id, node="generate", provider="openai",
        model=model, usage=telemetry.LlmUsage(),
    )

    assert cost == Decimal(0)
    count = await conn.fetchval(
        "select count(*) from resume_llm_calls where run_id = $1", uuid.UUID(run_id)
    )
    assert count == 1


# ─── Criterion 9: an unpriced model fails loudly ──────────────────────────────


async def test_an_unpriced_model_raises_rather_than_recording_zero(
    telemetry: Any, conn: asyncpg.Connection, user_id: str, run_id: str
) -> None:
    with pytest.raises(UpstreamFailed) as excinfo:
        async with conn.transaction():
            await telemetry.record_llm_call(
                conn, run_id=run_id, user_id=user_id, node="generate", provider="openai",
                model=UNPRICED_MODEL,
                usage=telemetry.LlmUsage(input_tokens=1_000, output_tokens=1_000),
            )

    assert UNPRICED_MODEL in str(excinfo.value)


async def test_an_unpriced_model_writes_nothing_at_all(
    telemetry: Any, conn: asyncpg.Connection, user_id: str, run_id: str
) -> None:
    with pytest.raises(UpstreamFailed):
        async with conn.transaction():
            await telemetry.record_llm_call(
                conn, run_id=run_id, user_id=user_id, node="generate", provider="openai",
                model=UNPRICED_MODEL,
                usage=telemetry.LlmUsage(input_tokens=1_000, output_tokens=1_000),
            )

    count = await conn.fetchval(
        "select count(*) from resume_llm_calls where run_id = $1", uuid.UUID(run_id)
    )
    assert count == 0

    run_row = await _run_row(conn, run_id)
    assert run_row["cost_usd"] == Decimal(0)
    assert "generate" not in _usage_rollup(run_row)


# ─── The table holds counts, never text ───────────────────────────────────────


async def test_nothing_resembling_a_prompt_is_stored(
    telemetry: Any, pricing: Any, conn: asyncpg.Connection, user_id: str, run_id: str
) -> None:
    """RG-050: this table answers "what did that cost" without retaining what was said."""
    model = _model(pricing, "claude")
    await telemetry.record_llm_call(
        conn, run_id=run_id, user_id=user_id, node="review", provider="anthropic",
        model=model, usage=telemetry.LlmUsage(input_tokens=10, output_tokens=10),
    )

    row = await conn.fetchrow(
        "select * from resume_llm_calls where run_id = $1", uuid.UUID(run_id)
    )
    text_columns = {
        key for key, value in dict(row).items() if isinstance(value, str) and len(value) > 200
    }
    assert text_columns == set()
