from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from resume_agent.llm.catalog import fetch_anthropic_models, fetch_openai_models


class FakeOpenAIModels:
    def list(self):
        return SimpleNamespace(
            data=[
                SimpleNamespace(id="gpt-4.1-mini"),
                SimpleNamespace(id="text-embedding-3-small"),
                SimpleNamespace(id="gpt-4o"),
            ]
        )


class FakeAnthropicModels:
    def list(self):
        return SimpleNamespace(
            data=[
                SimpleNamespace(id="claude-3-5-sonnet-latest"),
                SimpleNamespace(id="claude-haiku-4-5"),
            ]
        )


def test_fetch_openai_models_filters_non_generation_models() -> None:
    result = fetch_openai_models("key", client=SimpleNamespace(models=FakeOpenAIModels()))
    assert result.error is None
    assert result.models == ["gpt-4.1-mini", "gpt-4o"]


def test_fetch_anthropic_models_returns_account_models() -> None:
    result = fetch_anthropic_models("key", client=SimpleNamespace(models=FakeAnthropicModels()))
    assert result.error is None
    assert result.models == ["claude-3-5-sonnet-latest", "claude-haiku-4-5"]


def test_model_fetch_without_keys_uses_proxy_or_empty() -> None:
    # When proxy is unreachable, expect empty list (not hardcoded fallback)
    with patch("resume_agent.llm.catalog._fetch_proxy_models", return_value=None):
        openai_result = fetch_openai_models("")
        anthropic_result = fetch_anthropic_models("")
    assert openai_result.models == []
    assert anthropic_result.models == []
    assert openai_result.error is not None
    assert anthropic_result.error is not None
