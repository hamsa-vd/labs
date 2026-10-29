"""Per-model token prices (RG-050).

Money is `Decimal` everywhere. A float cost accumulated over a few hundred calls drifts, and the
drift lands in a number a user is shown and may be billed on.

A model that is not in this table is a **hard failure**, not a zero. Recording zero for an
unpriced model is how a cost bug survives to production: the run succeeds, the dashboard says the
month cost nothing, and nobody looks again until the provider invoice arrives. `price_for` raises
`UpstreamFailed` naming the model instead, so the gap is found on the first call.

`as_of` records when each row was last checked against the provider's published list price.
A slightly stale price is acceptable — the figure is an estimate either way. A missing row is not.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING

from resume_pipeline.errors import UpstreamFailed

if TYPE_CHECKING:  # pragma: no cover - import cycle: telemetry imports this module.
    from resume_pipeline.telemetry import LlmUsage

TOKENS_PER_MTOK = Decimal(1_000_000)

_ANTHROPIC_AS_OF = "2026-06-24"
_OPENAI_AS_OF = "2026-06-24"


@dataclass(frozen=True)
class ModelPrice:
    input_per_mtok: Decimal
    output_per_mtok: Decimal
    as_of: str


def _anthropic(input_price: str, output_price: str) -> ModelPrice:
    return ModelPrice(Decimal(input_price), Decimal(output_price), _ANTHROPIC_AS_OF)


def _openai(input_price: str, output_price: str) -> ModelPrice:
    return ModelPrice(Decimal(input_price), Decimal(output_price), _OPENAI_AS_OF)


#: Current text models for both providers, plus the ids v1 actually named in its defaults
#: (`claude-3-5-sonnet-latest`, `gpt-4.1-mini`) so a migrated run does not fail on its own history.
PRICES: dict[str, ModelPrice] = {
    # --- Anthropic, current generation -------------------------------------------------
    "claude-fable-5-1": _anthropic("10.00", "50.00"),
    "claude-fable-5": _anthropic("10.00", "50.00"),
    "claude-opus-5": _anthropic("5.00", "25.00"),
    "claude-opus-4-8": _anthropic("5.00", "25.00"),
    "claude-opus-4-7": _anthropic("5.00", "25.00"),
    "claude-opus-4-6": _anthropic("5.00", "25.00"),
    "claude-sonnet-5": _anthropic("2.00", "10.00"),
    "claude-sonnet-4-6": _anthropic("3.00", "15.00"),
    "claude-haiku-4-5": _anthropic("1.00", "5.00"),
    # --- Anthropic, previous generations still selectable ------------------------------
    "claude-opus-4-5": _anthropic("5.00", "25.00"),
    "claude-sonnet-4-5": _anthropic("3.00", "15.00"),
    "claude-3-7-sonnet-latest": _anthropic("3.00", "15.00"),
    "claude-3-5-sonnet-latest": _anthropic("3.00", "15.00"),
    "claude-3-5-sonnet-20241022": _anthropic("3.00", "15.00"),
    "claude-3-5-haiku-latest": _anthropic("0.80", "4.00"),
    "claude-3-5-haiku-20241022": _anthropic("0.80", "4.00"),
    # --- OpenAI ------------------------------------------------------------------------
    "gpt-5": _openai("1.25", "10.00"),
    "gpt-5-mini": _openai("0.25", "2.00"),
    "gpt-5-nano": _openai("0.05", "0.40"),
    "gpt-4.1": _openai("2.00", "8.00"),
    "gpt-4.1-mini": _openai("0.40", "1.60"),
    "gpt-4.1-nano": _openai("0.10", "0.40"),
    "gpt-4o": _openai("2.50", "10.00"),
    "gpt-4o-mini": _openai("0.15", "0.60"),
    "o3": _openai("2.00", "8.00"),
    "o3-mini": _openai("1.10", "4.40"),
    "o4-mini": _openai("1.10", "4.40"),
}


def price_for(model: str) -> ModelPrice:
    """Return the price row for `model`, or raise naming it.

    Naming the model in the error is the point: the operator's next action is to add that exact
    string to `PRICES`, and an error that says only "unknown model" does not tell them which.
    """
    try:
        return PRICES[model]
    except KeyError:
        raise UpstreamFailed(
            f"There is no price on record for the model {model}, so the run was stopped rather "
            "than recording a cost of zero. Add the model to the pricing table, then try again.",
            details={"model": model},
        ) from None


def cost_of(model: str, usage: LlmUsage) -> Decimal:
    """Cost of one call, exact, in US dollars."""
    price = price_for(model)
    charged = (
        Decimal(usage.input_tokens) * price.input_per_mtok
        + Decimal(usage.output_tokens) * price.output_per_mtok
    )
    return charged / TOKENS_PER_MTOK
