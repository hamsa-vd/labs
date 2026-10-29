"""The two provider clients: retry policy and the v1 quirks the port must keep (WP4 §2).

Every test here drives the **real** client class with a scripted stub SDK object. Nothing is
patched at the transport, and the suite-wide socket guard stays armed, so "it retried" and "it
retried without asking the network" are both proven at once.

Three claims carry the weight:

- **A 429 is retried, three attempts in total, then `UpstreamFailed`.** Counted on the stub, not
  inferred from timing.
- **A 400 is called exactly once.** Retrying a 400 is retrying a prompt bug, and it spends the
  user's money to get the same answer three times. The call counter is the assertion; an exception
  type alone would not distinguish "rejected" from "rejected twice more first".
- **An authentication failure is named and immediate.** v1 turned it into a `RuntimeError`; v2
  turns it into an `AppError` so the API renders an envelope rather than a 500 — and never retries,
  because a wrong key stays wrong.

Backoff is recorded rather than served (see `slept` in `conftest.py`), so the exponential waits the
contract mandates are asserted, not endured.

The OpenAI parameter quirks are here too, and they are scar tissue: reasoning models and `gpt-5`
take `max_completion_tokens` and reject a non-default temperature. The tests assert on the kwargs
that actually reached the SDK, which is the only place that breakage ever showed up.
"""

from __future__ import annotations

import inspect
import sys
from dataclasses import dataclass
from types import ModuleType
from typing import Any

import anthropic
import openai
import pytest

from resume_pipeline.errors import AppError, UpstreamFailed
from tests.llm.conftest import (
    SENTINEL_SECRET,
    StubSDK,
    anthropic_reply,
    build_client,
    client_class,
    openai_reply,
)

ANTHROPIC_MODEL = "claude-sonnet-4-5"
OPENAI_MODEL = "gpt-4.1-mini"

SYSTEM_PROMPT = "You are a resume tailoring system."
USER_PROMPT = "Review the resume against the job description."


def _http_module(exc_cls: type) -> Any:
    """The httpx-alike the installed SDK builds its responses from."""
    module = sys.modules[exc_cls.__module__]
    for name in ("httpx2", "httpx"):
        candidate = getattr(module, name, None)
        if candidate is not None:
            return candidate
    import httpx

    return httpx


@dataclass
class Provider:
    """One provider's module plus the SDK shapes its client consumes."""

    name: str
    module: ModuleType
    sdk: Any
    model: str
    url: str

    def stub(self, *outcomes: Any) -> StubSDK:
        return StubSDK(list(outcomes), kind=self.name)

    def reply(self, text: str = "All good.", **kwargs: Any) -> Any:
        if self.name == "anthropic":
            return anthropic_reply(text, **kwargs)
        return openai_reply(text, **kwargs)

    def _response(self, status: int) -> Any:
        http = _http_module(self.sdk.APIStatusError)
        return http.Response(status, request=http.Request("POST", self.url))

    def error(self, kind: str) -> Exception:
        if kind == "rate_limit":
            return self.sdk.RateLimitError("stub", response=self._response(429), body=None)
        if kind == "bad_request":
            return self.sdk.BadRequestError("stub", response=self._response(400), body=None)
        if kind == "auth":
            return self.sdk.AuthenticationError("stub", response=self._response(401), body=None)
        if kind == "server":
            return self.sdk.InternalServerError("stub", response=self._response(500), body=None)
        http = _http_module(self.sdk.APIStatusError)
        request = http.Request("POST", self.url)
        if kind == "timeout":
            return self.sdk.APITimeoutError(request=request)
        if kind == "connection":
            return self.sdk.APIConnectionError(request=request)
        raise AssertionError(f"unknown error kind {kind}")


@pytest.fixture(params=["anthropic", "openai"])
def provider(
    request: pytest.FixtureRequest, anthropic_mod: ModuleType, openai_mod: ModuleType
) -> Provider:
    if request.param == "anthropic":
        return Provider(
            "anthropic", anthropic_mod, anthropic, ANTHROPIC_MODEL,
            "https://api.anthropic.com/v1/messages",
        )
    return Provider(
        "openai", openai_mod, openai, OPENAI_MODEL,
        "https://api.openai.com/v1/chat/completions",
    )


async def complete(client: Any, **overrides: Any) -> Any:
    kwargs: dict[str, Any] = {
        "system_prompt": SYSTEM_PROMPT,
        "user_prompt": USER_PROMPT,
        "max_tokens": 6000,
    }
    kwargs.update(overrides)
    return await client.complete(**kwargs)


# ─── Retry policy ─────────────────────────────────────────────────────────────


async def test_a_client_that_always_rate_limits_makes_three_attempts(
    provider: Provider,
) -> None:
    sdk = provider.stub(provider.error("rate_limit"))
    client = build_client(provider.module, model=provider.model, sdk=sdk)

    with pytest.raises(UpstreamFailed):
        await complete(client)

    assert sdk.call_count == 3


async def test_exhausted_rate_limit_retries_raise_upstream_failed(provider: Provider) -> None:
    sdk = provider.stub(provider.error("rate_limit"))
    client = build_client(provider.module, model=provider.model, sdk=sdk)

    with pytest.raises(UpstreamFailed) as caught:
        await complete(client)

    assert caught.value.code == "upstream_failed"
    assert caught.value.status == 502


async def test_backoff_waits_between_each_attempt(provider: Provider, slept: list[float]) -> None:
    """Three attempts means two waits, and neither of them is zero — a retry storm against a
    rate-limited endpoint is how a 429 becomes a ban."""
    sdk = provider.stub(provider.error("rate_limit"))
    client = build_client(provider.module, model=provider.model, sdk=sdk)

    with pytest.raises(UpstreamFailed):
        await complete(client)

    assert len(slept) == 2
    assert all(wait > 0 for wait in slept)


async def test_a_server_error_is_retried(provider: Provider) -> None:
    sdk = provider.stub(provider.error("server"))
    client = build_client(provider.module, model=provider.model, sdk=sdk)

    with pytest.raises(UpstreamFailed):
        await complete(client)

    assert sdk.call_count == 3


async def test_a_timeout_is_retried(provider: Provider) -> None:
    """v1 retried `APITimeoutError`; the port keeps that list exactly."""
    sdk = provider.stub(provider.error("timeout"))
    client = build_client(provider.module, model=provider.model, sdk=sdk)

    with pytest.raises(UpstreamFailed):
        await complete(client)

    assert sdk.call_count == 3


async def test_a_connection_error_is_retried(provider: Provider) -> None:
    sdk = provider.stub(provider.error("connection"))
    client = build_client(provider.module, model=provider.model, sdk=sdk)

    with pytest.raises(UpstreamFailed):
        await complete(client)

    assert sdk.call_count == 3


async def test_a_transient_rate_limit_recovers_on_the_third_attempt(provider: Provider) -> None:
    sdk = provider.stub(
        provider.error("rate_limit"),
        provider.error("rate_limit"),
        provider.reply("Recovered.", output_tokens=7),
    )
    client = build_client(provider.module, model=provider.model, sdk=sdk)

    completion = await complete(client)

    assert completion.text == "Recovered."
    assert sdk.call_count == 3


# ─── A 400 is a prompt bug, not a blip ────────────────────────────────────────


async def test_a_bad_request_is_called_exactly_once(provider: Provider) -> None:
    sdk = provider.stub(provider.error("bad_request"))
    client = build_client(provider.module, model=provider.model, sdk=sdk)

    with pytest.raises(Exception):  # noqa: B017 - the type is asserted separately
        await complete(client)

    assert sdk.call_count == 1


async def test_a_bad_request_does_not_wait(provider: Provider, slept: list[float]) -> None:
    sdk = provider.stub(provider.error("bad_request"))
    client = build_client(provider.module, model=provider.model, sdk=sdk)

    with pytest.raises(Exception):  # noqa: B017 - the type is asserted separately
        await complete(client)

    assert slept == []


async def test_a_bad_request_surfaces_as_an_application_error(provider: Provider) -> None:
    """Every failure the API returns renders through the `AppError` envelope; a raw SDK exception
    escaping the client becomes a 500 with a stack trace instead."""
    sdk = provider.stub(provider.error("bad_request"))
    client = build_client(provider.module, model=provider.model, sdk=sdk)

    with pytest.raises(AppError):
        await complete(client)


# ─── Authentication ───────────────────────────────────────────────────────────


async def test_an_authentication_failure_is_not_retried(provider: Provider) -> None:
    sdk = provider.stub(provider.error("auth"))
    client = build_client(provider.module, model=provider.model, sdk=sdk)

    with pytest.raises(Exception):  # noqa: B017 - the type is asserted separately
        await complete(client)

    assert sdk.call_count == 1


async def test_an_authentication_failure_raises_a_named_error(provider: Provider) -> None:
    """v1 raised a bare `RuntimeError`. "Converted to a named error" means it carries a code the
    UI can switch on, not the `internal_error` fallback."""
    sdk = provider.stub(provider.error("auth"))
    client = build_client(provider.module, model=provider.model, sdk=sdk)

    with pytest.raises(AppError) as caught:
        await complete(client)

    assert caught.value.code != "internal_error"


async def test_an_authentication_failure_does_not_wait(
    provider: Provider, slept: list[float]
) -> None:
    sdk = provider.stub(provider.error("auth"))
    client = build_client(provider.module, model=provider.model, sdk=sdk)

    with pytest.raises(Exception):  # noqa: B017 - the type is asserted separately
        await complete(client)

    assert slept == []


# ─── The key never appears in a failure ───────────────────────────────────────


@pytest.mark.parametrize("kind", ["rate_limit", "bad_request", "auth", "server", "connection"])
async def test_the_api_key_never_reaches_an_exception(provider: Provider, kind: str) -> None:
    sdk = provider.stub(provider.error(kind))
    client = build_client(provider.module, model=provider.model, api_key=SENTINEL_SECRET, sdk=sdk)

    with pytest.raises(Exception) as caught:  # noqa: B017 - any failure must stay clean
        await complete(client)

    rendered = f"{caught.value!r} {caught.value!s} {getattr(caught.value, 'details', {})!r}"
    assert SENTINEL_SECRET not in rendered


async def test_the_api_key_never_reaches_the_client_repr(provider: Provider) -> None:
    sdk = provider.stub(provider.reply())
    client = build_client(provider.module, model=provider.model, api_key=SENTINEL_SECRET, sdk=sdk)

    assert SENTINEL_SECRET not in repr(client)
    assert SENTINEL_SECRET not in str(client)


async def test_the_upstream_message_follows_the_house_voice(provider: Provider) -> None:
    sdk = provider.stub(provider.error("rate_limit"))
    client = build_client(provider.module, model=provider.model, api_key=SENTINEL_SECRET, sdk=sdk)

    with pytest.raises(UpstreamFailed) as caught:
        await complete(client)

    message = caught.value.message
    assert message.strip() != ""
    assert "!" not in message
    assert SENTINEL_SECRET not in message


async def test_the_exhausted_error_names_what_failed(provider: Provider) -> None:
    """"A retryable, named message" — the operator reading the log has to know which upstream
    gave up, and the run row records only this message."""
    sdk = provider.stub(provider.error("rate_limit"))
    client = build_client(provider.module, model=provider.model, sdk=sdk)

    with pytest.raises(UpstreamFailed) as caught:
        await complete(client)

    rendered = f"{caught.value.message} {caught.value.details}".lower()
    assert provider.name in rendered or provider.model.lower() in rendered


# ─── The key comes from the constructor, never the environment ────────────────


def test_the_client_does_not_fall_back_to_the_environment(
    provider: Provider, monkeypatch: pytest.MonkeyPatch
) -> None:
    """v2 is BYOK. An `os.getenv` fallback would spend the operator's key on a user's run, and it
    would do it silently."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", SENTINEL_SECRET)
    monkeypatch.setenv("OPENAI_API_KEY", SENTINEL_SECRET)
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-from-the-environment")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-from-the-environment")

    cls = client_class(provider.module)
    try:
        instance = cls(model=provider.model)  # type: ignore[call-arg]
    except Exception:
        return  # Refusing to construct without a key satisfies the contract.

    rendered = f"{instance!r} {getattr(instance, '__dict__', {})!r}"
    assert SENTINEL_SECRET not in rendered
    assert getattr(instance, "model", provider.model) == provider.model


def test_the_sixty_second_client_timeout_survives_the_port(provider: Provider) -> None:
    numbers = [
        value
        for value in vars(provider.module).values()
        if isinstance(value, int | float) and not isinstance(value, bool)
    ]

    assert any(float(value) == 60.0 for value in numbers), (
        f"`{provider.module.__name__}` has no 60-second timeout constant. v1 set the SDK client "
        "timeout to 60 seconds and the contract keeps it exactly."
    )


def test_the_client_declares_its_provider(provider: Provider) -> None:
    sdk = provider.stub(provider.reply())
    client = build_client(provider.module, model=provider.model, sdk=sdk)

    assert client.provider == provider.name
    assert client.model == provider.model


# ─── The success path ─────────────────────────────────────────────────────────


async def test_a_successful_call_returns_a_completion_with_the_usage(
    provider: Provider, base_mod: ModuleType
) -> None:
    sdk = provider.stub(
        provider.reply("The resume reads well.", input_tokens=1200, output_tokens=340)
    )
    client = build_client(provider.module, model=provider.model, sdk=sdk)

    completion = await complete(client)

    assert isinstance(completion, base_mod.Completion)
    assert completion.text == "The resume reads well."
    assert completion.input_tokens == 1200
    assert completion.output_tokens == 340


async def test_absent_usage_reports_zero_tokens(provider: Provider) -> None:
    """Zero, not `None` — telemetry sums these, and a `None` in the sum is a 500 at the end of a
    run the user already paid for."""
    sdk = provider.stub(provider.reply("No usage on this one.", usage=False))
    client = build_client(provider.module, model=provider.model, sdk=sdk)

    completion = await complete(client)

    assert completion.input_tokens == 0
    assert completion.output_tokens == 0


async def test_the_completion_reports_the_model(provider: Provider) -> None:
    sdk = provider.stub(provider.reply("Done.", model=provider.model))
    client = build_client(provider.module, model=provider.model, sdk=sdk)

    completion = await complete(client)

    assert completion.model == provider.model


async def test_the_prompts_reach_the_sdk(provider: Provider) -> None:
    sdk = provider.stub(provider.reply())
    client = build_client(provider.module, model=provider.model, sdk=sdk)

    await complete(client, system_prompt="SYSTEM-MARKER", user_prompt="USER-MARKER")

    sent = repr(sdk.calls[0])
    assert "SYSTEM-MARKER" in sent
    assert "USER-MARKER" in sent
    assert sdk.calls[0]["model"] == provider.model


async def test_the_system_prompt_is_not_concatenated_into_the_user_turn(
    provider: Provider,
) -> None:
    """The governance prompt is the system prompt. Folding it into the user turn would put
    instructions inside the same channel as the attacker-controlled job description."""
    sdk = provider.stub(provider.reply())
    client = build_client(provider.module, model=provider.model, sdk=sdk)

    await complete(client, system_prompt="SYSTEM-MARKER", user_prompt="USER-MARKER")

    call = sdk.calls[0]
    if provider.name == "anthropic":
        assert call["system"] == "SYSTEM-MARKER"
        assert call["messages"] == [{"role": "user", "content": "USER-MARKER"}]
    else:
        assert call["messages"] == [
            {"role": "system", "content": "SYSTEM-MARKER"},
            {"role": "user", "content": "USER-MARKER"},
        ]


# ─── Anthropic specifics ──────────────────────────────────────────────────────


async def test_anthropic_joins_its_text_blocks(anthropic_mod: ModuleType) -> None:
    """v1 joined the blocks with a newline and stripped the result. A model that answers in two
    blocks must not lose the second one."""
    sdk = StubSDK([anthropic_reply("First half.", "Second half.")], kind="anthropic")
    client = build_client(anthropic_mod, model=ANTHROPIC_MODEL, sdk=sdk)

    completion = await complete(client)

    assert completion.text == "First half.\nSecond half."


async def test_anthropic_skips_blocks_with_no_text(anthropic_mod: ModuleType) -> None:
    sdk = StubSDK([anthropic_reply("Only this.", "")], kind="anthropic")
    client = build_client(anthropic_mod, model=ANTHROPIC_MODEL, sdk=sdk)

    completion = await complete(client)

    assert completion.text == "Only this."


async def test_anthropic_rejects_an_empty_response(anthropic_mod: ModuleType) -> None:
    """v1's empty-response check, kept. An empty completion parsed as LaTeX produces an empty
    document that compiles to a blank page, which is worse than an error."""
    sdk = StubSDK([anthropic_reply()], kind="anthropic")
    client = build_client(anthropic_mod, model=ANTHROPIC_MODEL, sdk=sdk)

    with pytest.raises(AppError):
        await complete(client)


async def test_anthropic_does_not_retry_an_empty_response(anthropic_mod: ModuleType) -> None:
    sdk = StubSDK([anthropic_reply("   ")], kind="anthropic")
    client = build_client(anthropic_mod, model=ANTHROPIC_MODEL, sdk=sdk)

    with pytest.raises(AppError):
        await complete(client)

    assert sdk.call_count == 1


async def test_anthropic_passes_max_tokens_through(anthropic_mod: ModuleType) -> None:
    sdk = StubSDK([anthropic_reply("ok")], kind="anthropic")
    client = build_client(anthropic_mod, model=ANTHROPIC_MODEL, sdk=sdk)

    await complete(client, max_tokens=4321)

    assert sdk.calls[0]["max_tokens"] == 4321


# ─── OpenAI specifics: the model quirks ───────────────────────────────────────


async def test_openai_reads_the_first_choice(openai_mod: ModuleType) -> None:
    sdk = StubSDK([openai_reply("  The letter is ready.  ")], kind="openai")
    client = build_client(openai_mod, model=OPENAI_MODEL, sdk=sdk)

    completion = await complete(client)

    assert completion.text == "The letter is ready."


async def test_openai_maps_prompt_and_completion_tokens(openai_mod: ModuleType) -> None:
    """OpenAI calls them `prompt_tokens` and `completion_tokens`; `Completion` calls them input
    and output. Crossing those two over is a cost bug that never raises."""
    sdk = StubSDK([openai_reply("ok", input_tokens=900, output_tokens=120)], kind="openai")
    client = build_client(openai_mod, model=OPENAI_MODEL, sdk=sdk)

    completion = await complete(client)

    assert completion.input_tokens == 900
    assert completion.output_tokens == 120


@pytest.mark.parametrize("content", [None, "", "   "])
async def test_openai_rejects_an_empty_response(openai_mod: ModuleType, content: str | None) -> None:
    sdk = StubSDK([openai_reply(content)], kind="openai")
    client = build_client(openai_mod, model=OPENAI_MODEL, sdk=sdk)

    with pytest.raises(AppError):
        await complete(client)


@pytest.mark.parametrize("model", ["o1-preview", "o3-mini", "o4-mini", "gpt-5", "gpt-5-mini"])
def test_reasoning_and_gpt5_models_take_max_completion_tokens(
    openai_mod: ModuleType, model: str
) -> None:
    params = openai_mod._build_extra_params(model, 6000)

    assert params == {"max_completion_tokens": 6000}


@pytest.mark.parametrize("model", ["gpt-4.1-mini", "gpt-4o", "gpt-4.1"])
def test_ordinary_models_take_max_tokens(openai_mod: ModuleType, model: str) -> None:
    params = openai_mod._build_extra_params(model, 6000)

    assert params == {"max_tokens": 6000}


def test_the_extra_params_match_is_case_insensitive(openai_mod: ModuleType) -> None:
    assert openai_mod._build_extra_params("GPT-5", 10) == {"max_completion_tokens": 10}


@pytest.mark.parametrize("model", ["gpt-5", "gpt-5-mini", "o1", "o3-mini", "o4-mini"])
def test_these_models_reject_a_non_default_temperature(openai_mod: ModuleType, model: str) -> None:
    assert openai_mod._supports_temperature(model) is False


@pytest.mark.parametrize("model", ["gpt-4.1-mini", "gpt-4o-mini", "gpt-4-turbo"])
def test_ordinary_models_accept_a_temperature(openai_mod: ModuleType, model: str) -> None:
    assert openai_mod._supports_temperature(model) is True


async def test_a_gpt5_call_sends_max_completion_tokens_and_no_temperature(
    openai_mod: ModuleType,
) -> None:
    sdk = StubSDK([openai_reply("ok")], kind="openai")
    client = build_client(openai_mod, model="gpt-5", sdk=sdk)

    await complete(client, max_tokens=4096)

    call = sdk.calls[0]
    assert call["max_completion_tokens"] == 4096
    assert "max_tokens" not in call
    assert "temperature" not in call


async def test_a_reasoning_model_call_sends_max_completion_tokens_and_no_temperature(
    openai_mod: ModuleType,
) -> None:
    sdk = StubSDK([openai_reply("ok")], kind="openai")
    client = build_client(openai_mod, model="o3-mini", sdk=sdk)

    await complete(client, max_tokens=2048)

    call = sdk.calls[0]
    assert call["max_completion_tokens"] == 2048
    assert "temperature" not in call


async def test_an_ordinary_model_call_sends_max_tokens_and_a_temperature(
    openai_mod: ModuleType,
) -> None:
    sdk = StubSDK([openai_reply("ok")], kind="openai")
    client = build_client(openai_mod, model=OPENAI_MODEL, sdk=sdk)

    await complete(client, max_tokens=1234)

    call = sdk.calls[0]
    assert call["max_tokens"] == 1234
    assert "max_completion_tokens" not in call
    assert "temperature" in call


def test_complete_is_a_coroutine_taking_keyword_prompts(provider: Provider) -> None:
    cls = client_class(provider.module)
    params = inspect.signature(cls.complete).parameters

    assert inspect.iscoroutinefunction(cls.complete)
    assert params["system_prompt"].kind is inspect.Parameter.KEYWORD_ONLY
    assert params["user_prompt"].kind is inspect.Parameter.KEYWORD_ONLY
    assert params["max_tokens"].default == 6000
