"""Local fixtures for the WP4 LLM tests.

Four things live here, none of which belong in the shared `tests/conftest.py`:

1. **Lazy module fixtures.** WP4's source is written by a different agent, so these tests must
   *collect* cleanly before it exists. Importing inside a fixture turns "the module is not written
   yet" into a test failure rather than a collection error, which is what the blind protocol needs.
   This mirrors `tests/latex/conftest.py`.

2. **Class and constructor discovery for the two provider clients.** The contract fixes the module
   paths (`resume_pipeline/llm/anthropic.py`, `openai.py`) and the `complete` signature, but names
   neither the client classes nor the keyword the SDK object is injected through. Rather than guess
   one spelling and call a correct implementation broken, `client_class` finds the single class in
   the module that implements `complete`, and `build_client` finds the constructor parameters for
   the key and for the injected SDK. Every assertion in the suite is still the contract's; only the
   spelling of the seam is discovered.

3. **A no-wait clock.** The contract mandates exponential backoff with jitter. Real backoff would
   make the retry suite take tens of seconds, so `slept` replaces `asyncio.sleep` and `time.sleep`
   with recorders. Tests that care assert on the recorded waits instead of enduring them.

4. **A recording stub SDK.** Retries are proven by driving the real client class with a scripted
   SDK object, never by patching the transport: "it retried" and "it retried without asking the
   network" are different claims, and only the second one is testable offline.

No fixture here reaches a socket. The suite-wide guard in `tests/conftest.py` stays armed for
every test in this directory.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import importlib
import inspect
import os
import tempfile
import time
import types
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

TESTS_DIR = Path(__file__).resolve().parents[1]
LLM_FIXTURE_DIR = TESTS_DIR / "fixtures" / "llm"
SEED_PROMPT_DIR = TESTS_DIR.parent / "seed" / "prompts"

#: A string no real implementation can produce by accident. Used to prove a secret does not
#: reach a rendered form; grep the rendered output for it and the test is unambiguous.
SENTINEL_SECRET = "sk-ant-SENTINEL-do-not-render-3f9c1a7b"

#: 32 bytes before base64, which is what the contract requires of the master key.
TESTS_MASTER_KEY_BYTES = b"ascend-tests-master-key-032bytes"

# `resume_pipeline.settings` resolves at import and refuses to load without these, so any test
# that imports the crypto or factory modules needs them present first. They belong in the shared
# `tests/conftest.py` — several packages have the same need — but that file is WP2's and not ours
# to edit, so they are provisioned here with `setdefault`: a real value in the environment always
# wins, and `tests/latex/conftest.py` provisions the same names the same way.
#
# Nothing here reaches anything. The socket guard forbids connections, and the database URL names
# a database no test in this package opens.
FALLBACK_SETTINGS_ENV = {
    "RESUME_DATABASE_URL": "postgresql://ascend:ascend@127.0.0.1:55432/ascend_tests",
    "RESUME_SERVICE_TOKEN": "tests-service-token",
    "RESUME_DOCUMENTS_DIR": str(Path(tempfile.gettempdir()) / "ascend-tests-documents"),
    "RESUME_DOCUMENT_URL_SECRET": "tests-document-url-secret",
    "RESUME_MASTER_KEY": base64.urlsafe_b64encode(TESTS_MASTER_KEY_BYTES).decode(),
    "RESUME_LATEX_SERVICE_URL": "http://latex.invalid",
    "RESUME_LLM_MODE": "fake",
}


def ensure_settings_env() -> None:
    for name, value in FALLBACK_SETTINGS_ENV.items():
        os.environ.setdefault(name, value)


ensure_settings_env()


def pytest_configure(config: pytest.Config) -> None:
    ensure_settings_env()


# ─── Lazy module fixtures ─────────────────────────────────────────────────────


def _import(name: str) -> types.ModuleType:
    ensure_settings_env()
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError as exc:  # pragma: no cover - only before WP4 source lands
        pytest.fail(f"WP4 has not provided `{name}` yet ({exc}).", pytrace=False)


@pytest.fixture(scope="session")
def base_mod() -> types.ModuleType:
    """`resume_pipeline.llm.base` — `Completion`, `LLMClient`, `parse_strict_json_object`."""
    return _import("resume_pipeline.llm.base")


@pytest.fixture(scope="session")
def anthropic_mod() -> types.ModuleType:
    """`resume_pipeline.llm.anthropic` — the port of v1's `claude_client.py`."""
    return _import("resume_pipeline.llm.anthropic")


@pytest.fixture(scope="session")
def openai_mod() -> types.ModuleType:
    """`resume_pipeline.llm.openai` — the port of v1's `openai_client.py`."""
    return _import("resume_pipeline.llm.openai")


@pytest.fixture(scope="session")
def catalog_mod() -> types.ModuleType:
    """`resume_pipeline.llm.catalog` — selectable models per provider."""
    return _import("resume_pipeline.llm.catalog")


@pytest.fixture(scope="session")
def pricing_mod() -> types.ModuleType:
    """`resume_pipeline.llm.pricing` — WP3's price table, cross-checked against the catalogue."""
    return _import("resume_pipeline.llm.pricing")


@pytest.fixture(scope="session")
def fake_mod() -> types.ModuleType:
    """`resume_pipeline.llm.fake` — the offline client the whole suite runs on."""
    return _import("resume_pipeline.llm.fake")


@pytest.fixture(scope="session")
def factory_mod() -> types.ModuleType:
    """`resume_pipeline.llm.factory` — `clients_for_run`, `RunClients`, `ModelSelection`."""
    return _import("resume_pipeline.llm.factory")


@pytest.fixture(scope="session")
def credentials_mod() -> types.ModuleType:
    """`resume_pipeline.llm.credentials` — `RunCredentials`, `resolve_for_run`."""
    return _import("resume_pipeline.llm.credentials")


@pytest.fixture(scope="session")
def crypto_mod() -> types.ModuleType:
    """`resume_pipeline.crypto` — `seal` and `open_sealed`."""
    return _import("resume_pipeline.crypto")


@pytest.fixture(scope="session")
def llm_fixture_dir() -> Path:
    return LLM_FIXTURE_DIR


@pytest.fixture(scope="session")
def seed_prompt_bodies() -> dict[str, str]:
    """The real seeded prompt bodies, keyed by stage.

    The fake has to infer a stage from the prompts the pipeline actually sends, so stage
    inference is exercised against these rather than against invented text.
    """
    return {
        "targeting": (SEED_PROMPT_DIR / "targeting_brief.md").read_text(encoding="utf-8"),
        "generation": (SEED_PROMPT_DIR / "generator.md").read_text(encoding="utf-8"),
        "review": (SEED_PROMPT_DIR / "reviewer.md").read_text(encoding="utf-8"),
        "revision": (SEED_PROMPT_DIR / "reviser.md").read_text(encoding="utf-8"),
        "cover_letter": (SEED_PROMPT_DIR / "cover_letter.md").read_text(encoding="utf-8"),
    }


# ─── No-wait clock ────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def slept(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Record every backoff wait instead of serving it.

    Returns the list of requested durations in order, so a test can assert that backoff happened
    and how often, without the suite paying for it. `tenacity.nap` sleeps through `time.sleep`
    and `tenacity.asyncio` through `asyncio.sleep`, both looked up at call time.
    """
    waits: list[float] = []
    real_async_sleep = asyncio.sleep

    async def _record_async(delay: float, *args: Any, **kwargs: Any) -> Any:
        waits.append(float(delay))
        return await real_async_sleep(0)

    def _record_sync(delay: float) -> None:
        waits.append(float(delay))

    monkeypatch.setattr(asyncio, "sleep", _record_async)
    monkeypatch.setattr(time, "sleep", _record_sync)
    return waits


# ─── Provider client seams ────────────────────────────────────────────────────

#: Constructor parameter names an implementation might use for the injected SDK object.
SDK_PARAM_NAMES = ("client", "sdk", "sdk_client", "raw_client", "api_client", "transport")
#: Constructor parameter names an implementation might use for the BYOK key.
KEY_PARAM_NAMES = ("api_key", "key", "secret")

TEST_API_KEY = "sk-test-not-a-real-key"


def client_class(module: types.ModuleType) -> type:
    """The one class in `module` that implements the `LLMClient` protocol."""
    candidates = [
        obj
        for name, obj in vars(module).items()
        if isinstance(obj, type)
        and not name.startswith("_")
        and getattr(obj, "__module__", "") == module.__name__
        and callable(getattr(obj, "complete", None))
    ]
    if len(candidates) == 1:
        return candidates[0]
    named = [obj for obj in candidates if "client" in obj.__name__.lower()]
    if len(named) == 1:
        return named[0]
    pytest.fail(
        f"`{module.__name__}` must expose exactly one class with a `complete` method "
        f"(the LLMClient implementation); found {[obj.__name__ for obj in candidates]}.",
        pytrace=False,
    )


def build_client(
    module: types.ModuleType,
    *,
    model: str,
    api_key: str = TEST_API_KEY,
    sdk: Any | None = None,
    **extra: Any,
) -> Any:
    """Construct the module's client with `api_key` and, when given, an injected SDK object."""
    cls = client_class(module)
    params = inspect.signature(cls).parameters
    kwargs: dict[str, Any] = {}
    if "model" in params:
        kwargs["model"] = model

    key_param = next((name for name in KEY_PARAM_NAMES if name in params), None)
    if key_param is None:
        pytest.fail(
            f"`{cls.__name__}` takes no API key in its constructor. The contract requires the "
            "key to be passed in, with no `os.getenv` fallback.",
            pytrace=False,
        )
    kwargs[key_param] = api_key

    if sdk is not None:
        sdk_param = next((name for name in SDK_PARAM_NAMES if name in params), None)
        if sdk_param is None:
            pytest.fail(
                f"`{cls.__name__}` offers no seam to inject an SDK object (looked for "
                f"{list(SDK_PARAM_NAMES)}). The retry policy must be provable without a network.",
                pytrace=False,
            )
        kwargs[sdk_param] = sdk

    kwargs.update(extra)
    return cls(**kwargs)


# ─── Scripted stub SDK ────────────────────────────────────────────────────────


class Dual:
    """A value usable whether the client calls the SDK synchronously or awaits it.

    The contract fixes `async def complete` but not whether the port wraps the sync SDK or uses
    the async one. Both are legitimate readings, and neither should decide whether the retry
    policy is tested.
    """

    def __init__(self, value: Any) -> None:
        object.__setattr__(self, "_value", value)

    def __getattr__(self, name: str) -> Any:
        return getattr(object.__getattribute__(self, "_value"), name)

    def __await__(self) -> Any:
        async def _resolved() -> Any:
            return object.__getattribute__(self, "_value")

        return _resolved().__await__()


@dataclass
class Usage:
    """Anthropic-shaped usage."""

    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class TextBlock:
    text: str
    type: str = "text"


@dataclass
class AnthropicResponse:
    content: list[Any]
    usage: Usage | None = None
    model: str = "claude-test"
    stop_reason: str = "end_turn"
    id: str = "msg_stub"


@dataclass
class OpenAIUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class OpenAIMessage:
    content: str | None
    role: str = "assistant"


@dataclass
class OpenAIChoice:
    message: OpenAIMessage
    finish_reason: str = "stop"
    index: int = 0


@dataclass
class OpenAIResponse:
    choices: list[OpenAIChoice]
    usage: OpenAIUsage | None = None
    model: str = "gpt-test"
    id: str = "chatcmpl_stub"


def anthropic_reply(
    *texts: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    usage: bool = True,
    model: str = "claude-test",
) -> AnthropicResponse:
    return AnthropicResponse(
        content=[TextBlock(text) for text in texts],
        usage=Usage(input_tokens, output_tokens) if usage else None,
        model=model,
    )


def openai_reply(
    text: str | None,
    *,
    input_tokens: int = 0,
    output_tokens: int = 0,
    usage: bool = True,
    model: str = "gpt-test",
) -> OpenAIResponse:
    return OpenAIResponse(
        choices=[OpenAIChoice(OpenAIMessage(text))],
        usage=(
            OpenAIUsage(input_tokens, output_tokens, input_tokens + output_tokens)
            if usage
            else None
        ),
        model=model,
    )


class _Endpoint:
    def __init__(self, sdk: StubSDK) -> None:
        self._sdk = sdk

    def create(self, **kwargs: Any) -> Any:
        return self._sdk._invoke(kwargs)


@dataclass
class StubSDK:
    """A scripted stand-in for `Anthropic` / `OpenAI`.

    `outcomes` is consumed one per call; the last entry repeats forever, so a single error means
    "always fails". An entry that is an exception is raised, anything else is returned.
    """

    outcomes: list[Any]
    kind: str = "anthropic"
    calls: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.kind == "anthropic":
            self.messages = _Endpoint(self)
        else:
            self.chat = types.SimpleNamespace(completions=_Endpoint(self))

    @property
    def call_count(self) -> int:
        return len(self.calls)

    def _invoke(self, kwargs: dict[str, Any]) -> Any:
        self.calls.append(kwargs)
        index = min(len(self.calls) - 1, len(self.outcomes) - 1)
        outcome = self.outcomes[index]
        if isinstance(outcome, BaseException):
            raise outcome
        return Dual(outcome)


class Row(dict):
    """A row that answers to both `row["provider"]` and `row.provider`, the way a Record does."""

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError as exc:  # pragma: no cover - a missing column is a test bug
            raise AttributeError(name) from exc


@dataclass
class RecordingConnection:
    """An asyncpg-shaped connection that serves fixed rows and records every query.

    Queries are recorded rather than matched: the SQL is the implementation's business, but *how
    many* times the keys are read and *whether the user id was passed* are the contract's.
    """

    rows: list[Row] = field(default_factory=list)
    queries: list[tuple[str, tuple[Any, ...]]] = field(default_factory=list)

    async def fetch(self, query: str, *args: Any) -> list[Row]:
        self.queries.append((query, args))
        return list(self.rows)

    async def fetchrow(self, query: str, *args: Any) -> Row | None:
        self.queries.append((query, args))
        return self.rows[0] if self.rows else None

    async def fetchval(self, query: str, *args: Any) -> Any:
        self.queries.append((query, args))
        if not self.rows:
            return None
        return next(iter(self.rows[0].values()))

    async def execute(self, query: str, *args: Any) -> str:
        self.queries.append((query, args))
        return "SELECT 0"

    @property
    def query_count(self) -> int:
        return len(self.queries)

    @property
    def all_args(self) -> list[Any]:
        return [arg for _, args in self.queries for arg in args]


def key_row(
    crypto_mod: types.ModuleType,
    user_id: str,
    provider: str,
    secret: str,
    *,
    label: str = "default",
) -> Row:
    """A `resume_api_keys` row with a real sealed ciphertext in it."""
    return Row(
        id=f"00000000-0000-4000-8000-{abs(hash((provider, label))) % 10**12:012d}",
        user_id=user_id,
        provider=provider,
        ciphertext=crypto_mod.seal(user_id, secret),
        last_four=secret[-4:],
        label=label,
        created_at=None,
        last_used_at=None,
    )


class ExplodingConnection:
    """A database connection that fails the test if anything touches it.

    Used to prove `clients_for_run` in fake mode reads no keys: an assertion that no query ran is
    stronger than an assertion that the right rows came back.
    """

    def __init__(self) -> None:
        self.touched: list[str] = []

    def __getattr__(self, name: str) -> Any:
        self.touched.append(name)
        raise AssertionError(
            f"The database was touched (`conn.{name}`) when it must not have been. In fake mode "
            "no key is read and no connection is used."
        )


def prompt_digest(user_prompt: str) -> str:
    """`sha256(user_prompt)[:16]` — the fixture file stem the contract specifies."""
    return hashlib.sha256(user_prompt.encode("utf-8")).hexdigest()[:16]
