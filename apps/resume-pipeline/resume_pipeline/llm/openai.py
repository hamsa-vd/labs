"""OpenAI client (RG-023). Ported from v1's `resume_agent/llm/openai_client.py`.

`_build_extra_params` and `_supports_temperature` come across verbatim. They are scar tissue from
real breakage: reasoning models and `gpt-5` take `max_completion_tokens` instead of `max_tokens`
and reject any temperature but the default, and a request that gets either wrong is rejected
outright. They look like clutter and they are not.

Also unchanged: the 60-second client timeout, the retryable exception set, the authentication
failure that is never retried, and the empty-response check.

Changed, and only this: `complete` is async and returns `Completion`; the key is a constructor
argument with **no `os.getenv` fallback** (v2 is BYOK, and an environment fallback would spend the
operator's money on a user's run); three attempts on a 429 or a 5xx only, then `UpstreamFailed`.
"""

from __future__ import annotations

import logging
from typing import Any

from resume_pipeline.errors import MissingApiKey, UpstreamFailed
from resume_pipeline.llm.base import (
    CLIENT_TIMEOUT_SECONDS,
    RETRY_ATTEMPTS,
    Completion,
    is_auth_status,
    is_retryable_status,
    retry_async,
    status_code_of,
)

logger = logging.getLogger(__name__)

PROVIDER = "openai"
DEFAULT_MODEL = "gpt-4.1-mini"
DEFAULT_TEMPERATURE = 0.2

_REASONING_MODELS = ("o1", "o2", "o3", "o4")
_COMPLETION_TOKENS_MODELS = ("gpt-5",)
_DEFAULT_TEMPERATURE_ONLY_MODELS = ("gpt-5",)  # these models only accept temperature=1 (the default)


def _build_extra_params(model: str, max_tokens: int) -> dict[str, Any]:
    m = model.lower()
    if any(m.startswith(p) for p in _REASONING_MODELS + _COMPLETION_TOKENS_MODELS):
        return {"max_completion_tokens": max_tokens}
    return {"max_tokens": max_tokens}


def _supports_temperature(model: str) -> bool:
    """Return True only if the model accepts a non-default temperature value."""
    m = model.lower()
    if any(m.startswith(p) for p in _REASONING_MODELS + _DEFAULT_TEMPERATURE_ONLY_MODELS):
        return False
    return True


class OpenAIClient:
    """An `LLMClient` backed by the OpenAI chat completions API."""

    provider: str = PROVIDER

    def __init__(
        self,
        *,
        model: str = DEFAULT_MODEL,
        api_key: str | None = None,
        base_url: str | None = None,
        temperature: float = DEFAULT_TEMPERATURE,
        client: Any | None = None,
        attempts: int = RETRY_ATTEMPTS,
    ) -> None:
        self.model = model
        self.temperature = temperature
        self.base_url = base_url
        self.attempts = attempts
        if client is not None:
            # An injected SDK object (a stub in tests, a shared client in production) carries its
            # own credentials.
            self._client = client
            return
        if not api_key:
            raise MissingApiKey(
                "This run needs an OpenAI key. Add one in settings and start the run again.",
                details={"provider": PROVIDER},
            )
        from openai import AsyncOpenAI

        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url or None,
            timeout=CLIENT_TIMEOUT_SECONDS,
        )

    async def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 6000,
        stage: str | None = None,
    ) -> Completion:
        """Call the model once, retrying only a 429 or a 5xx. `stage` is ignored here."""

        async def _call() -> Completion:
            return await self._once(
                system_prompt=system_prompt, user_prompt=user_prompt, max_tokens=max_tokens
            )

        return await retry_async(
            _call,
            is_retryable=self._is_retryable,
            on_exhausted=self._exhausted,
            attempts=self.attempts,
        )

    # ─── Internals ────────────────────────────────────────────────────────────

    async def _once(self, *, system_prompt: str, user_prompt: str, max_tokens: int) -> Completion:
        params: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            **_build_extra_params(self.model, max_tokens),
        }
        if _supports_temperature(self.model):
            params["temperature"] = self.temperature

        try:
            response = await self._client.chat.completions.create(**params)
        except Exception as exc:
            named = self._translate(exc)
            if named is exc:
                raise
            raise named from exc

        usage = getattr(response, "usage", None)
        input_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
        output_tokens = int(getattr(usage, "completion_tokens", 0) or 0)

        # v1 tested the raw content and returned `content.strip()`, so a whitespace-only response
        # passed the check and reached the parser as an empty string. The Anthropic port stripped
        # before checking; this now does the same, which is the only difference from v1 here.
        content = (response.choices[0].message.content or "").strip()
        if not content:
            raise UpstreamFailed(
                "OpenAI returned an empty response. Start the run again.",
                details={"provider": PROVIDER, "model": self.model},
            )
        return Completion(
            text=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=self.model,
        )

    def _translate(self, exc: Exception) -> Exception:
        """Turn an SDK failure into either a named error or something the retry loop will take."""
        if _is_auth_error(exc):
            return MissingApiKey(
                "OpenAI rejected your key. Replace it in settings and start the run again.",
                details={"provider": PROVIDER},
            )
        if self._is_retryable(exc):
            return exc
        return UpstreamFailed(
            "OpenAI could not complete the request. Check the model selection and try again.",
            details={"provider": PROVIDER, "model": self.model},
        )

    @staticmethod
    def _is_retryable(exc: Exception) -> bool:
        if isinstance(exc, MissingApiKey | UpstreamFailed):
            return False
        if _is_auth_error(exc):
            return False
        if _is_transport_error(exc):
            # A timeout or a dropped connection: v1 retried both and so does this.
            return True
        return is_retryable_status(status_code_of(exc))

    def _exhausted(self, last: Exception) -> Exception:
        status = status_code_of(last)
        logger.warning(
            "OpenAI call failed after %d attempts | model=%s status=%s",
            self.attempts,
            self.model,
            status,
        )
        return UpstreamFailed(
            "OpenAI is not responding after three attempts. Wait a moment and start the run again.",
            details={"provider": PROVIDER, "model": self.model, "retryable": True},
        )


def _is_auth_error(exc: Exception) -> bool:
    try:
        from openai import AuthenticationError, PermissionDeniedError

        if isinstance(exc, AuthenticationError | PermissionDeniedError):
            return True
    except Exception:  # pragma: no cover - the SDK is a hard dependency
        pass
    return is_auth_status(status_code_of(exc))


def _is_transport_error(exc: Exception) -> bool:
    try:
        from openai import APIConnectionError, APITimeoutError, RateLimitError

        return isinstance(exc, RateLimitError | APITimeoutError | APIConnectionError)
    except Exception:  # pragma: no cover - the SDK is a hard dependency
        return False
