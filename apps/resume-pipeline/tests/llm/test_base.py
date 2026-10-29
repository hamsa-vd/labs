"""`resume_pipeline.llm.base` — the shape every provider returns (WP4 §1).

v1's clients returned a bare `str`. The one change the port makes is `Completion`, and it is not
cosmetic: RG-050 cannot report an honest cost from a string, so `input_tokens` and `output_tokens`
have to travel with the text or telemetry invents them. These tests pin the dataclass down —
fields, defaults, immutability — because three other packages destructure it.
"""

from __future__ import annotations

import dataclasses
import inspect
from types import ModuleType
from typing import Any

import pytest

EXPECTED_FIELDS = ("text", "input_tokens", "output_tokens", "model")


def test_completion_carries_the_four_contract_fields_in_order(base_mod: ModuleType) -> None:
    names = tuple(f.name for f in dataclasses.fields(base_mod.Completion))

    assert names == EXPECTED_FIELDS


def test_completion_needs_only_the_text(base_mod: ModuleType) -> None:
    completion = base_mod.Completion("Hello.")

    assert completion.text == "Hello."


def test_completion_token_counts_default_to_zero_and_model_to_empty(base_mod: ModuleType) -> None:
    completion = base_mod.Completion("Hello.")

    assert completion.input_tokens == 0
    assert completion.output_tokens == 0
    assert completion.model == ""


def test_completion_accepts_the_counts_and_the_model(base_mod: ModuleType) -> None:
    completion = base_mod.Completion(
        text="Hello.", input_tokens=120, output_tokens=45, model="claude-sonnet-4-5"
    )

    assert completion.text == "Hello."
    assert completion.input_tokens == 120
    assert completion.output_tokens == 45
    assert completion.model == "claude-sonnet-4-5"


def test_completion_is_frozen(base_mod: ModuleType) -> None:
    completion = base_mod.Completion("Hello.")

    with pytest.raises(dataclasses.FrozenInstanceError):
        completion.text = "Something else."  # type: ignore[misc]


def test_two_completions_with_the_same_values_are_equal(base_mod: ModuleType) -> None:
    first = base_mod.Completion("Hello.", 1, 2, "m")
    second = base_mod.Completion("Hello.", 1, 2, "m")

    assert first == second


# ─── The protocol ─────────────────────────────────────────────────────────────


def test_llm_client_is_a_protocol(base_mod: ModuleType) -> None:
    assert getattr(base_mod.LLMClient, "_is_protocol", False) is True


def test_llm_client_declares_provider_model_and_complete(base_mod: ModuleType) -> None:
    annotations = getattr(base_mod.LLMClient, "__annotations__", {})

    assert "provider" in annotations
    assert "model" in annotations
    assert callable(getattr(base_mod.LLMClient, "complete", None))


def test_complete_takes_keyword_prompts_and_a_six_thousand_token_default(
    base_mod: ModuleType,
) -> None:
    params = inspect.signature(base_mod.LLMClient.complete).parameters

    assert params["system_prompt"].kind is inspect.Parameter.KEYWORD_ONLY
    assert params["user_prompt"].kind is inspect.Parameter.KEYWORD_ONLY
    assert params["max_tokens"].default == 6000


def test_a_conforming_class_satisfies_the_protocol_structurally(base_mod: ModuleType) -> None:
    """A minimal conforming client is what the graph will hold; nothing else is required of it."""

    class Minimal:
        provider = "fake"
        model = "fake-model"

        async def complete(
            self, *, system_prompt: str, user_prompt: str, max_tokens: int = 6000
        ) -> Any:
            return base_mod.Completion(text=user_prompt)

    client = Minimal()

    assert client.provider == "fake"
    assert inspect.iscoroutinefunction(client.complete)


def test_parse_strict_json_object_lives_here(base_mod: ModuleType) -> None:
    """It moves out of v1's `claude_client.py`: the targeting and review nodes both need it, and
    neither should have to import a provider module to parse a response."""
    assert callable(base_mod.parse_strict_json_object)
