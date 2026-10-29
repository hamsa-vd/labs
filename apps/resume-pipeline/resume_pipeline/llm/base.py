"""The LLM client protocol, the completion record, and strict JSON parsing (RG-023).

v1's clients returned a bare `str`. They return `Completion` here because RG-050 cannot report an
honest cost from a string: `telemetry.record_llm_call` needs the token counts the provider sent
back. Callers that only want the text read `.text`.

`parse_strict_json_object` moves here from v1's `claude_client.py` unchanged. The targeting and
review nodes depend on its fallback behaviour — models fence their JSON often enough that the
regex second attempt is load bearing, not defensive decoration.

`retry_async` lives here so both provider clients share one policy. The policy is deliberately
narrow: three attempts, exponential backoff with jitter, and only for a 429 or a 5xx. A 400 is a
prompt bug, and retrying a prompt bug spends the user's money three times to reach the same
failure.
"""

from __future__ import annotations

import asyncio
import json
import random
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

#: Total attempts, not retries: one call plus at most two retries.
RETRY_ATTEMPTS: int = 3
#: v1's `wait_exponential(multiplier=1, min=2, max=30)`, kept.
BACKOFF_MIN_SECONDS: float = 2.0
BACKOFF_MAX_SECONDS: float = 30.0
#: Jitter is a fraction of the computed delay, so two clients retrying together desynchronise.
BACKOFF_JITTER: float = 0.25

#: The v1 clients used a 60-second client timeout. Longer than that is a stuck request, not a slow
#: one, and the graph has a whole run's budget to think about.
CLIENT_TIMEOUT_SECONDS: float = 60.0


@dataclass(frozen=True)
class Completion:
    """One provider response, with the usage the cost ledger needs."""

    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""


@runtime_checkable
class LLMClient(Protocol):
    """What the graph needs from a model, real or fake.

    `stage` is part of the protocol because the fake needs it and the contract says the caller
    sets it rather than the client guessing. The real clients accept it and ignore it.
    """

    provider: str
    model: str

    async def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 6000,
        stage: str | None = None,
    ) -> Completion: ...


def parse_strict_json_object(raw: str) -> dict[str, Any]:
    """Parse a JSON object from Claude output, with regex fallback."""
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if not match:
            raise ValueError("Claude review did not contain a JSON object.") from None
        parsed = json.loads(match.group(0))

    if not isinstance(parsed, dict):
        raise ValueError("Claude review JSON must be an object.")
    return parsed


def backoff_delay(attempt: int) -> float:
    """Seconds to wait before attempt `attempt` (0-indexed), exponential with jitter."""
    base: float = min(BACKOFF_MAX_SECONDS, BACKOFF_MIN_SECONDS * float(2**attempt))
    return base + random.uniform(0.0, base * BACKOFF_JITTER)


async def retry_async[T](
    call: Callable[[], Awaitable[T]],
    *,
    is_retryable: Callable[[Exception], bool],
    on_exhausted: Callable[[Exception], Exception],
    attempts: int = RETRY_ATTEMPTS,
) -> T:
    """Run `call`, retrying only what `is_retryable` accepts, at most `attempts` times.

    An exception `is_retryable` rejects propagates immediately and untouched — that is how a 400
    reaches the caller after exactly one call. When every attempt is used up, the last failure is
    converted by `on_exhausted`, so the caller sees one named error rather than a raw SDK type.

    `asyncio.sleep` is looked up at call time rather than bound at import, so a test that patches
    it does not have to wait out a real backoff.
    """
    last: Exception = RuntimeError("The provider call was never attempted.")
    for attempt in range(max(1, attempts)):
        try:
            return await call()
        except Exception as exc:
            # `Exception`, not `BaseException`: a cancellation is not a provider failure and must
            # travel up untouched.
            if not is_retryable(exc):
                raise
            last = exc
            if attempt + 1 >= attempts:
                break
            await asyncio.sleep(backoff_delay(attempt))
    raise on_exhausted(last)


def status_code_of(exc: Exception) -> int | None:
    """Best-effort HTTP status for a provider exception.

    The SDK exception types are checked first by the callers; this covers the rest, including the
    stub SDK objects the retry tests inject, which carry a status rather than an SDK class.
    """
    for attribute in ("status_code", "status"):
        value = getattr(exc, attribute, None)
        if isinstance(value, bool):
            continue
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
    response = getattr(exc, "response", None)
    if response is not None:
        value = getattr(response, "status_code", None)
        if isinstance(value, int) and not isinstance(value, bool):
            return value
    return None


def is_retryable_status(status: int | None) -> bool:
    """429 and 5xx only. Everything else is the caller's problem to fix, not to repeat."""
    if status is None:
        return False
    return status == 429 or 500 <= status < 600


def is_auth_status(status: int | None) -> bool:
    return status in (401, 403)
