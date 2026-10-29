"""Building the three clients one run needs (RG-023, RG-031).

Two modes, and the default is the cheap one.

`fake` touches neither the key table nor the network. That is what makes a full pipeline test free
and offline, so it must stay true even for a user with no keys at all — no lookup, no fallback, no
"just check whether they have one".

`live` resolves every provider the selection needs **before the graph starts**. A missing key is a
`MissingApiKey` carrying `details.provider` at that point, not a failure three nodes in. A run that
dies halfway has already spent money.

v1's split is the default selection: a strong model reviews, a generation model writes, a cheap
model revises.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from resume_pipeline.llm.anthropic import AnthropicClient
from resume_pipeline.llm.base import LLMClient
from resume_pipeline.llm.catalog import (
    DEFAULT_GENERATION_MODEL,
    DEFAULT_REVIEW_MODEL,
    DEFAULT_REVISION_MODEL,
    provider_for,
)
from resume_pipeline.llm.credentials import RunCredentials, resolve_for_run
from resume_pipeline.llm.fake import FakeLLMClient
from resume_pipeline.llm.openai import OpenAIClient

LLMMode = Literal["fake", "live"]


@dataclass(frozen=True)
class ModelSelection:
    """The model each of the three roles uses. Defaults are v1's split."""

    generation_model: str = DEFAULT_GENERATION_MODEL
    review_model: str = DEFAULT_REVIEW_MODEL
    revision_model: str = DEFAULT_REVISION_MODEL

    def providers(self) -> list[str]:
        """Every provider this selection needs a key for, in a stable order."""
        ordered = [
            provider_for(self.generation_model),
            provider_for(self.review_model),
            provider_for(self.revision_model),
        ]
        return list(dict.fromkeys(ordered))


#: v1's default split, as a value the API layer can hand back unchanged.
DEFAULT_SELECTION = ModelSelection()


@dataclass(frozen=True)
class RunClients:
    generation: LLMClient
    review: LLMClient
    revision: LLMClient


async def clients_for_run(
    conn: Any,
    user_id: str,
    selection: ModelSelection,
    *,
    mode: LLMMode | None = None,
) -> RunClients:
    """The three clients for one run. `mode` defaults to `settings.llm_mode`, which is `fake`."""
    resolved_mode = mode or configured_mode()
    if resolved_mode == "fake":
        # No database call, no key lookup, no socket — deliberately, and even when the user has no
        # keys at all.
        return RunClients(
            generation=FakeLLMClient(provider="fake", model=selection.generation_model),
            review=FakeLLMClient(provider="fake", model=selection.review_model),
            revision=FakeLLMClient(provider="fake", model=selection.revision_model),
        )

    providers = selection.providers()
    credentials = await resolve_for_run(conn, user_id, providers)
    # Check every provider before building anything. Raising here rather than inside the first
    # client's constructor is what makes "no key" a failure before the graph starts instead of one
    # discovered two nodes in, after the generation call has already been paid for.
    for provider in providers:
        credentials.require(provider)
    return RunClients(
        generation=_client_for(selection.generation_model, credentials),
        review=_client_for(selection.review_model, credentials),
        revision=_client_for(selection.revision_model, credentials),
    )


def configured_mode() -> LLMMode:
    """`settings.llm_mode`, or `fake` when settings are not importable yet.

    Falling back to `fake` rather than `live` is the only safe direction: the failure mode of a
    wrong guess here is a run that costs nothing, not a run that quietly spends a user's money.
    """
    try:
        from resume_pipeline.settings import get_settings
    except Exception:
        return "fake"
    mode = str(getattr(get_settings(), "llm_mode", "fake") or "fake").lower()
    return "live" if mode == "live" else "fake"


def _client_for(model: str, credentials: RunCredentials) -> LLMClient:
    provider = provider_for(model)
    api_key = credentials.require(provider)
    if provider == "anthropic":
        return AnthropicClient(model=model, api_key=api_key)
    return OpenAIClient(model=model, api_key=api_key)
