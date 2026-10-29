"""The catalogue and the price table have to agree (WP4 §2, acceptance criterion 11).

Two different work packages own these files — the catalogue is WP4's, `pricing.py` is WP3's — and
nothing but this test connects them. A model a user can pick from the catalogue but which has no
price is not a cosmetic gap: `record_llm_call` raises `UpstreamFailed` on an unpriced model, so the
run dies *after* the money has been spent. The cross-check is the point of the test, which is why
it is written even while `pricing.py` is still being authored.

The catalogue's shape is not spelled out in the contract, so `catalogued_models` accepts any of the
handful of reasonable spellings rather than inventing one and failing a correct implementation for
it. What is asserted is the contract's claim: every model on offer, for every provider, has a
price.
"""

from __future__ import annotations

import inspect
from collections.abc import Mapping
from types import ModuleType
from typing import Any

import pytest

PROVIDERS = ("anthropic", "openai")

MAPPING_NAMES = ("CATALOG", "MODELS", "SELECTABLE_MODELS", "MODEL_CATALOG", "PROVIDER_MODELS")
NO_ARG_NAMES = ("catalog", "models", "selectable_models", "model_catalog", "all_models")
ONE_ARG_NAMES = ("models_for", "models_for_provider", "selectable_models", "list_models")


def _model_id(item: Any) -> str:
    if isinstance(item, str):
        return item
    if isinstance(item, Mapping):
        for key in ("id", "model", "name"):
            if key in item:
                return str(item[key])
    for attribute in ("id", "model", "name"):
        value = getattr(item, attribute, None)
        if isinstance(value, str):
            return value
    raise AssertionError(f"cannot read a model id out of {item!r}")


def _normalise(raw: Mapping[Any, Any]) -> dict[str, list[str]]:
    values = list(raw.values())
    if values and all(isinstance(value, str) for value in values):
        # model -> provider, the other way round.
        inverted: dict[str, list[str]] = {}
        for model, provider in raw.items():
            inverted.setdefault(str(provider), []).append(str(model))
        return inverted
    return {str(provider): [_model_id(item) for item in models] for provider, models in raw.items()}


def catalogued_models(catalog: ModuleType) -> dict[str, list[str]]:
    """Every selectable model, keyed by provider."""
    for name in MAPPING_NAMES:
        value = getattr(catalog, name, None)
        if isinstance(value, Mapping) and value:
            return _normalise(value)

    for name in NO_ARG_NAMES:
        function = getattr(catalog, name, None)
        if callable(function) and not inspect.signature(function).parameters:
            result = function()
            if isinstance(result, Mapping) and result:
                return _normalise(result)

    for name in ONE_ARG_NAMES:
        function = getattr(catalog, name, None)
        if callable(function) and len(inspect.signature(function).parameters) == 1:
            return {provider: [_model_id(m) for m in function(provider)] for provider in PROVIDERS}

    pytest.fail(
        "`resume_pipeline.llm.catalog` exposes no readable list of selectable models per "
        f"provider (looked for {list(MAPPING_NAMES)}, {list(NO_ARG_NAMES)}, {list(ONE_ARG_NAMES)}).",
        pytrace=False,
    )


@pytest.fixture
def catalogue(catalog_mod: ModuleType) -> dict[str, list[str]]:
    return catalogued_models(catalog_mod)


# ─── The catalogue ────────────────────────────────────────────────────────────


def test_both_providers_are_catalogued(catalogue: dict[str, list[str]]) -> None:
    assert set(PROVIDERS) <= set(catalogue)


@pytest.mark.parametrize("provider", PROVIDERS)
def test_each_provider_offers_at_least_one_model(
    catalogue: dict[str, list[str]], provider: str
) -> None:
    assert catalogue[provider]


def test_every_model_id_is_a_clean_string(catalogue: dict[str, list[str]]) -> None:
    for provider, models in catalogue.items():
        for model in models:
            assert isinstance(model, str), f"{provider} lists a non-string model"
            assert model == model.strip() != ""


def test_no_model_is_offered_under_two_providers(catalogue: dict[str, list[str]]) -> None:
    """The factory routes on the provider a model belongs to. A model in both lists makes that
    routing ambiguous, and the wrong key gets used."""
    seen: dict[str, str] = {}
    for provider, models in catalogue.items():
        for model in models:
            assert model not in seen, f"{model} is listed under both {seen.get(model)} and {provider}"
            seen[model] = provider


def test_the_catalogue_lists_no_duplicates(catalogue: dict[str, list[str]]) -> None:
    for provider, models in catalogue.items():
        assert len(models) == len(set(models)), f"{provider} lists a model twice"


def test_the_cli_proxy_paths_are_gone(catalog_mod: ModuleType) -> None:
    """v1 fell back to a local CLI proxy on `127.0.0.1:11435` when no key was present. v2 is BYOK
    and never speaks to a local proxy, so no trace of that path survives the port."""
    for name, value in vars(catalog_mod).items():
        assert "proxy" not in name.lower(), f"`{name}` is a leftover CLI-proxy path"
        if isinstance(value, str):
            assert "proxy" not in value.lower()
            assert "11435" not in value


def test_the_catalogue_does_not_fetch(catalog_mod: ModuleType, catalogue: dict[str, list[str]]) -> None:
    """v1 asked the provider for its model list. That cannot work here: reading the catalogue
    happens on a settings page, with no key to hand, and the socket guard would fail this test if
    a request were attempted."""
    assert catalogued_models(catalog_mod) == catalogue


# ─── The cross-check ──────────────────────────────────────────────────────────


def test_every_catalogued_model_has_a_price(
    catalogue: dict[str, list[str]], pricing_mod: ModuleType
) -> None:
    unpriced = [
        f"{provider}:{model}"
        for provider, models in catalogue.items()
        for model in models
        if model not in pricing_mod.PRICES
    ]

    assert unpriced == [], f"catalogued but unpriced: {unpriced}"


def test_price_for_answers_for_every_catalogued_model(
    catalogue: dict[str, list[str]], pricing_mod: ModuleType
) -> None:
    """`record_llm_call` calls `price_for` on every completed call. An unpriced model turns a
    finished run into a 502 after the tokens are already paid for."""
    for models in catalogue.values():
        for model in models:
            price = pricing_mod.price_for(model)
            assert price is not None


def test_every_catalogued_price_is_positive_and_dated(
    catalogue: dict[str, list[str]], pricing_mod: ModuleType
) -> None:
    for models in catalogue.values():
        for model in models:
            price = pricing_mod.price_for(model)
            assert price.input_per_mtok > 0, f"{model} is priced at zero input"
            assert price.output_per_mtok > 0, f"{model} is priced at zero output"
            assert price.as_of
