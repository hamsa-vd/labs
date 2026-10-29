"""Anthropic client (RG-023). Ported from v1's `resume_agent/llm/claude_client.py`.

What came across unchanged: the 60-second client timeout, the retryable exception set, the
authentication failure that is never retried, the join of the response's text blocks, and the
empty-response check.

What changed, and only this:

* `complete` is async and returns `Completion`, carrying the usage the cost ledger needs;
* the key is a constructor argument with **no `os.getenv` fallback**. v1 read `ANTHROPIC_API_KEY`
  from the environment. v2 is BYOK, and an environment fallback would quietly spend the operator's
  money on a user's run;
* three attempts rather than four, and only for a 429 or a 5xx. Exhausted retries raise
  `UpstreamFailed`.
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

PROVIDER = "anthropic"
DEFAULT_MODEL = "claude-3-5-sonnet-latest"
DEFAULT_TEMPERATURE = 0.0


class AnthropicClient:
    """An `LLMClient` backed by the Anthropic Messages API."""

    provider: str = PROVIDER

    def __init__(
        self,
        *,
        model: str = DEFAULT_MODEL,
        api_key: str | None = None,
        temperature: float = DEFAULT_TEMPERATURE,
        client: Any | None = None,
        attempts: int = RETRY_ATTEMPTS,
    ) -> None:
        self.model = model
        self.temperature = temperature
        self.attempts = attempts
        if client is not None:
            # An injected SDK object (a stub in tests, a shared client in production) carries its
            # own credentials.
            self._client = client
            return
        if not api_key:
            raise MissingApiKey(
                "This run needs an Anthropic key. Add one in settings and start the run again.",
                details={"provider": PROVIDER},
            )
        from anthropic import AsyncAnthropic

        self._client = AsyncAnthropic(api_key=api_key, timeout=CLIENT_TIMEOUT_SECONDS)

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
        try:
            response = await self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
        except Exception as exc:
            named = self._translate(exc)
            if named is exc:
                raise
            raise named from exc

        usage = getattr(response, "usage", None)
        input_tokens = int(getattr(usage, "input_tokens", 0) or 0)
        output_tokens = int(getattr(usage, "output_tokens", 0) or 0)

        parts = [getattr(block, "text", None) for block in response.content]
        content = "\n".join(p for p in parts if p).strip()
        if not content:
            raise UpstreamFailed(
                "Anthropic returned an empty response. Start the run again.",
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
                "Anthropic rejected your key. Replace it in settings and start the run again.",
                details={"provider": PROVIDER},
            )
        if self._is_retryable(exc):
            return exc
        return UpstreamFailed(
            "Anthropic could not complete the request. Check the model selection and try again.",
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
            "Anthropic call failed after %d attempts | model=%s status=%s",
            self.attempts,
            self.model,
            status,
        )
        return UpstreamFailed(
            "Anthropic is not responding after three attempts. Wait a moment and start the run "
            "again.",
            details={"provider": PROVIDER, "model": self.model, "retryable": True},
        )


def _is_auth_error(exc: Exception) -> bool:
    try:
        from anthropic import AuthenticationError, PermissionDeniedError

        if isinstance(exc, AuthenticationError | PermissionDeniedError):
            return True
    except Exception:  # pragma: no cover - the SDK is a hard dependency
        pass
    return is_auth_status(status_code_of(exc))


def _is_transport_error(exc: Exception) -> bool:
    try:
        from anthropic import APIConnectionError, APITimeoutError, RateLimitError

        return isinstance(exc, RateLimitError | APITimeoutError | APIConnectionError)
    except Exception:  # pragma: no cover - the SDK is a hard dependency
        return False
