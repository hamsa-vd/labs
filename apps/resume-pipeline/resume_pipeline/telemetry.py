"""Cost and token accounting for LLM calls (RG-050).

One call in, one `resume_llm_calls` row out, plus the run's running totals moved forward in the
same transaction. Splitting the insert from the rollup would let a crash between them produce a
run whose `cost_usd` disagrees with the sum of its own calls, and the disagreement would be
invisible until someone added the calls up by hand.

Nothing here touches prompt or completion text. `resume_llm_calls` has no column that could hold
it, by design: the table answers "what did that cost", not "what was said".
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from resume_pipeline.errors import NotFound
from resume_pipeline.llm.pricing import cost_of

#: Key the run service owns inside `token_usage`. Accumulation must leave it alone.
PROMPTS_KEY = "prompts"


@dataclass(frozen=True)
class LlmUsage:
    input_tokens: int = 0
    output_tokens: int = 0


def _merge_node_usage(
    existing: dict[str, Any], node: str, usage: LlmUsage, cost: Decimal
) -> dict[str, Any]:
    """Fold one call into the `token_usage` rollup.

    Money serialises as a string, never as a JSON number: a JSON number is a float on the way
    back out of every client in the stack, and a float is not a currency.
    """
    merged = dict(existing)
    previous = merged.get(node)
    if not isinstance(previous, dict):
        previous = {}
    previous_cost = Decimal(str(previous.get("cost_usd", "0")))
    merged[node] = {
        "input_tokens": int(previous.get("input_tokens", 0)) + usage.input_tokens,
        "output_tokens": int(previous.get("output_tokens", 0)) + usage.output_tokens,
        "calls": int(previous.get("calls", 0)) + 1,
        "cost_usd": str(previous_cost + cost),
    }
    return merged


async def record_llm_call(
    conn: Any,
    *,
    run_id: str,
    user_id: str,
    node: str,
    provider: str,
    model: str,
    usage: LlmUsage,
    latency_ms: int | None = None,
) -> Decimal:
    """Record one LLM call against a run and return what it cost.

    Raises `UpstreamFailed` before writing anything when the model has no price, and `NotFound`
    when the run is not this user's — the same answer a missing run gets, so the call cannot be
    used to discover that somebody else's run exists.
    """
    cost = cost_of(model, usage)

    row = await conn.fetchrow(
        "select token_usage from resume_runs where id = $1 and user_id = $2",
        run_id,
        user_id,
    )
    if row is None:
        raise NotFound("That run was not found. Check the run and try again.")

    await conn.execute(
        """
        insert into resume_llm_calls
            (user_id, run_id, node, provider, model, input_tokens, output_tokens, cost_usd, latency_ms)
        values ($1, $2, $3, $4, $5, $6, $7, $8::numeric, $9)
        """,
        user_id,
        run_id,
        node,
        provider,
        model,
        usage.input_tokens,
        usage.output_tokens,
        cost,
        latency_ms,
    )

    existing_raw = row["token_usage"]
    existing = json.loads(existing_raw) if isinstance(existing_raw, str) else dict(existing_raw or {})
    merged = _merge_node_usage(existing, node, usage, cost)

    await conn.execute(
        """
        update resume_runs
           set cost_usd = cost_usd + $3::numeric,
               token_usage = $4::jsonb
         where id = $1 and user_id = $2
        """,
        run_id,
        user_id,
        cost,
        json.dumps(merged),
    )
    return cost
