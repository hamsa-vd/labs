"""`resume_pipeline.llm.pricing` (WP3 §3).

Two rules from the contract shape every test here.

**Money is `Decimal`, never `float`.** A per-million-token rate multiplied by a token count in
binary floating point produces a cost that is very nearly right, and "very nearly right" summed
over a few thousand calls is a reconciliation problem nobody enjoys. So the type is asserted, not
just the value.

**A missing price is a hard failure.** `price_for` on an unknown model raises `UpstreamFailed`
naming the model. The alternative — returning zero — is how a cost bug reaches production wearing
a green dashboard.

The model *identifiers* are deliberately not pinned here: the contract says to populate the table
with current Anthropic and OpenAI text models and accepts that a rate can go slightly stale, so
this suite checks the shape of every entry and the presence of both providers rather than
asserting a price that will be wrong next quarter.
"""

from __future__ import annotations

import datetime as dt
import importlib
import re
from decimal import Decimal
from typing import Any

import pytest

from resume_pipeline.errors import UpstreamFailed

PRICING_MODULE = "resume_pipeline.llm.pricing"
TELEMETRY_MODULE = "resume_pipeline.telemetry"

ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@pytest.fixture(scope="module")
def pricing() -> Any:
    try:
        return importlib.import_module(PRICING_MODULE)
    except ModuleNotFoundError as exc:  # pragma: no cover - only before WP3 source lands
        pytest.fail(f"WP3 has not provided `{PRICING_MODULE}` yet ({exc}).", pytrace=False)


@pytest.fixture(scope="module")
def llm_usage() -> Any:
    try:
        return importlib.import_module(TELEMETRY_MODULE).LlmUsage
    except ModuleNotFoundError as exc:  # pragma: no cover - only before WP3 source lands
        pytest.fail(f"WP3 has not provided `{TELEMETRY_MODULE}` yet ({exc}).", pytrace=False)


def _models(pricing: Any) -> list[str]:
    return sorted(pricing.PRICES)


# ─── The table ────────────────────────────────────────────────────────────────


def test_prices_is_populated(pricing: Any) -> None:
    assert isinstance(pricing.PRICES, dict)
    # v1 ran three roles — generation, review, revision — and the contract asks for the cheap
    # revision models on top of those.
    assert len(pricing.PRICES) >= 4, "at minimum v1's three roles plus cheap revision models"


def test_both_providers_are_priced(pricing: Any) -> None:
    """v1 generated and revised on OpenAI and reviewed on Anthropic; both must be priceable."""
    models = " ".join(_models(pricing)).lower()
    assert "claude" in models, "no Anthropic model in the pricing table"
    assert "gpt" in models, "no OpenAI model in the pricing table"


def test_every_entry_is_a_decimal_priced_model_price(pricing: Any) -> None:
    for model, price in pricing.PRICES.items():
        assert isinstance(model, str) and model, f"bad model key: {model!r}"
        assert isinstance(price.input_per_mtok, Decimal), f"{model} input rate is not Decimal"
        assert isinstance(price.output_per_mtok, Decimal), f"{model} output rate is not Decimal"
        assert price.input_per_mtok > 0, f"{model} has a zero input rate"
        assert price.output_per_mtok > 0, f"{model} has a zero output rate"


def test_every_entry_carries_an_iso_as_of_date(pricing: Any) -> None:
    for model, price in pricing.PRICES.items():
        assert ISO_DATE.match(price.as_of), f"{model} as_of is not an ISO date: {price.as_of!r}"
        dt.date.fromisoformat(price.as_of)


def test_model_price_is_frozen(pricing: Any) -> None:
    price = next(iter(pricing.PRICES.values()))
    with pytest.raises(Exception):  # noqa: B017 - dataclasses raise FrozenInstanceError
        price.input_per_mtok = Decimal("1")


# ─── price_for ────────────────────────────────────────────────────────────────


def test_price_for_returns_the_table_entry(pricing: Any) -> None:
    model = _models(pricing)[0]
    assert pricing.price_for(model) is pricing.PRICES[model]


def test_price_for_an_unknown_model_raises_upstream_failed(pricing: Any) -> None:
    with pytest.raises(UpstreamFailed) as excinfo:
        pricing.price_for("gpt-nonexistent-9000")

    # Naming the model is the whole point: the operator needs to know which entry to add.
    assert "gpt-nonexistent-9000" in str(excinfo.value)
    assert excinfo.value.code == "upstream_failed"
    assert excinfo.value.status == 502


def test_price_for_does_not_fall_back_to_a_zero_price(pricing: Any) -> None:
    with pytest.raises(UpstreamFailed):
        pricing.price_for("")


# ─── cost_of ──────────────────────────────────────────────────────────────────


def test_cost_of_is_exact_decimal_arithmetic(pricing: Any, llm_usage: Any) -> None:
    model = _models(pricing)[0]
    price = pricing.PRICES[model]
    usage = llm_usage(input_tokens=1_000_000, output_tokens=1_000_000)

    cost = pricing.cost_of(model, usage)

    assert isinstance(cost, Decimal)
    assert cost == price.input_per_mtok + price.output_per_mtok


def test_cost_of_scales_with_tokens(pricing: Any, llm_usage: Any) -> None:
    model = _models(pricing)[0]
    price = pricing.PRICES[model]
    usage = llm_usage(input_tokens=12_345, output_tokens=6_789)

    expected = (
        price.input_per_mtok * Decimal(12_345) + price.output_per_mtok * Decimal(6_789)
    ) / Decimal(1_000_000)

    assert pricing.cost_of(model, usage) == expected


def test_cost_of_never_returns_a_float(pricing: Any, llm_usage: Any) -> None:
    for model in _models(pricing):
        cost = pricing.cost_of(model, llm_usage(input_tokens=1_000, output_tokens=1_000))
        assert isinstance(cost, Decimal)
        assert not isinstance(cost, float)


def test_cost_of_zero_usage_is_zero(pricing: Any, llm_usage: Any) -> None:
    model = _models(pricing)[0]
    assert pricing.cost_of(model, llm_usage()) == Decimal(0)


def test_cost_of_an_unknown_model_raises(pricing: Any, llm_usage: Any) -> None:
    with pytest.raises(UpstreamFailed) as excinfo:
        pricing.cost_of("claude-nonexistent-9000", llm_usage(input_tokens=10, output_tokens=10))
    assert "claude-nonexistent-9000" in str(excinfo.value)


def test_output_is_priced_at_least_as_high_as_input(pricing: Any) -> None:
    """Every current text model charges more for output than input; a swapped pair is a typo."""
    for model, price in pricing.PRICES.items():
        assert price.output_per_mtok >= price.input_per_mtok, f"{model} looks transposed"


# ─── LlmUsage ─────────────────────────────────────────────────────────────────


def test_llm_usage_defaults_to_zero(llm_usage: Any) -> None:
    usage = llm_usage()
    assert usage.input_tokens == 0
    assert usage.output_tokens == 0


def test_llm_usage_is_frozen(llm_usage: Any) -> None:
    usage = llm_usage(input_tokens=1, output_tokens=2)
    with pytest.raises(Exception):  # noqa: B017 - dataclasses raise FrozenInstanceError
        usage.input_tokens = 5
