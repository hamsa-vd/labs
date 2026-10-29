"""Selectable models per provider, and live model listing (RG-023).

Ported from v1's `resume_agent/llm/catalog.py` with every local-CLI bridge removed. v1 fell back
to models discovered from an installed CLI when no key was present; the reuse map drops that path
rather than porting it, so a missing key now produces an explanatory `ModelListResult` instead.

Two halves:

* `CATALOG` is the static list the settings UI offers. Every model in it must have a price in
  `llm/pricing.py`; a catalogued model with no price would record a zero-cost run.
* `fetch_*_models` are the live listings v1 used, kept because a user with a key should be able to
  see what their own account can reach. Both take an injected `client` so nothing in a test has to
  touch the network.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from resume_pipeline.errors import ValidationFailed

#: The providers this package can build a client for. The key table also accepts `openrouter`,
#: which has no client here yet.
PROVIDERS: tuple[str, ...] = ("openai", "anthropic")

#: Models offered in the UI, per provider. Kept deliberately short: every entry is a promise that
#: `pricing.py` knows what it costs.
CATALOG: dict[str, tuple[str, ...]] = {
    "openai": (
        "gpt-5",
        "gpt-5-mini",
        "gpt-4.1",
        "gpt-4.1-mini",
        "gpt-4o",
        "gpt-4o-mini",
    ),
    "anthropic": (
        "claude-opus-4-5",
        "claude-sonnet-4-5",
        "claude-haiku-4-5",
        "claude-3-5-sonnet-latest",
    ),
}

#: v1's split, preserved: a strong model reviews, a generation model writes, a cheap model revises.
#: v1's generation default was `gpt-4.1-mini`, its review default `claude-3-5-sonnet-latest`, and
#: its revision default fell back to the generation model.
DEFAULT_GENERATION_MODEL: str = "gpt-4.1-mini"
DEFAULT_REVIEW_MODEL: str = "claude-3-5-sonnet-latest"
DEFAULT_REVISION_MODEL: str = "gpt-4.1-mini"

#: Prefixes used to place a model that is not in `CATALOG` — a user pinning a dated snapshot, say.
_OPENAI_PREFIXES: tuple[str, ...] = ("gpt-", "o1", "o2", "o3", "o4", "chatgpt-")
_ANTHROPIC_PREFIXES: tuple[str, ...] = ("claude-",)


@dataclass(frozen=True)
class ModelListResult:
    models: list[str]
    error: str | None = None


def models_for(provider: str) -> list[str]:
    """The catalogued models for one provider, or an empty list for an unknown provider."""
    return list(CATALOG.get(provider, ()))


def all_models() -> list[str]:
    """Every catalogued model, provider order preserved."""
    return [model for provider in CATALOG for model in CATALOG[provider]]


def provider_for(model: str) -> str:
    """Which provider serves `model`.

    Exact catalogue match first, then the naming prefix, so a snapshot id like
    `gpt-4.1-mini-2025-04-14` still routes. An unrecognisable model raises rather than guessing:
    guessing wrong means reaching for the wrong user's key.
    """
    for provider, models in CATALOG.items():
        if model in models:
            return provider
    lowered = model.lower().strip()
    if lowered.startswith(_ANTHROPIC_PREFIXES):
        return "anthropic"
    if lowered.startswith(_OPENAI_PREFIXES):
        return "openai"
    raise ValidationFailed(
        f"The model {model} is not one this service can route. Choose a model from the list.",
        details={"model": model},
    )


def fetch_openai_models(
    api_key: str, base_url: str | None = None, client: Any | None = None
) -> ModelListResult:
    if not api_key:
        return ModelListResult([], "Add an OpenAI key to list the models your account can use.")
    try:
        if client is None:
            from openai import OpenAI

            client = OpenAI(api_key=api_key, base_url=base_url or None)
        response = client.models.list()
        model_ids = sorted({model.id for model in response.data if getattr(model, "id", "")})
        generation_models = [
            model_id for model_id in model_ids if _looks_like_generation_model(model_id)
        ]
        return ModelListResult(generation_models or model_ids, None)
    except Exception as exc:
        return ModelListResult([], f"Could not fetch OpenAI models: {exc}")


def fetch_anthropic_models(api_key: str, client: Any | None = None) -> ModelListResult:
    if not api_key:
        return ModelListResult([], "Add an Anthropic key to list the models your account can use.")
    try:
        if client is None:
            from anthropic import Anthropic

            client = Anthropic(api_key=api_key)
        response = client.models.list()
        data = getattr(response, "data", response)
        model_ids = sorted({model.id for model in data if getattr(model, "id", "")})
        return ModelListResult(model_ids, None)
    except Exception as exc:
        return ModelListResult([], f"Could not fetch Anthropic models: {exc}")


def _looks_like_generation_model(model_id: str) -> bool:
    lowered = model_id.lower()
    excluded = ["embedding", "moderation", "tts", "whisper", "dall-e", "image", "transcribe"]
    if any(marker in lowered for marker in excluded):
        return False
    included = ["gpt", "o1", "o3", "o4", "o5", "chat"]
    return any(marker in lowered for marker in included)
