# WP4 — LLM providers, BYOK keys, and the offline fake

Discharges RG-023, RG-031, and the fake-client half of RG-008.

Root: `apps/resume-pipeline/`.

This package is what makes the whole pipeline testable. `LLM_MODE=fake` is the default everywhere
except a deliberate live run, so a full generation — revision loops included — runs in under two
seconds, offline, for nothing. A test that reaches a provider is a bug, and the socket guard in
`tests/conftest.py` makes it a failing one.

`resume_pipeline/pipeline/budgets.py` already exists (WP2) with `RunBudget`, `clamp_budget`,
`SERVER_CEILINGS`, and the `MAX_*` constants. Import it; do not redefine it.

---

## 1. `resume_pipeline/llm/base.py`

```python
@dataclass(frozen=True)
class Completion:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""

class LLMClient(Protocol):
    provider: str
    model: str
    async def complete(self, *, system_prompt: str, user_prompt: str, max_tokens: int = 6000) -> Completion: ...
```

v1's clients returned a bare `str`. They now return `Completion` so token counts reach
`telemetry.record_llm_call` — RG-050 cannot report an honest cost from a string. Callers that want
the text read `.text`.

`parse_strict_json_object(raw: str) -> dict[str, Any]` moves here from v1's `claude_client.py`,
**verbatim**: try `json.loads`, fall back to the first `{...}` match with `DOTALL`, raise
`ValueError` when neither yields a dict. The review and targeting nodes depend on it, and it
already handles fenced output.

## 2. `resume_pipeline/llm/anthropic.py` and `openai.py`

Ports of v1's `claude_client.py` and `openai_client.py`. Keep, exactly:
- the 60-second client timeout;
- retry on `RateLimitError`, `APITimeoutError`, `APIConnectionError` only;
- `AuthenticationError` converted to a named error, never retried;
- OpenAI's `_build_extra_params` and `_supports_temperature` model quirks — reasoning models and
  `gpt-5` take `max_completion_tokens` and reject a non-default temperature. That logic is scar
  tissue from real breakage; do not tidy it away;
- Anthropic's empty-response check, and the joining of text blocks.

What changes:
- `async def complete` returning `Completion`, with `input_tokens`/`output_tokens` read from the
  response usage (0 when absent).
- The key is passed to the constructor. **No `os.getenv` fallback.** v1 read the environment; v2 is
  BYOK and an env fallback would silently spend the operator's money on a user's run.
- Retries: 3 attempts total, exponential backoff with jitter, on 429 and 5xx only. A 400 is never
  retried — that is a prompt bug and retrying burns the user's money. Exhausted retries raise
  `UpstreamFailed` with a retryable, named message.

`resume_pipeline/llm/catalog.py` — ported from v1 minus every CLI-proxy path (`cli_proxy` is
dropped, per the reuse map). It lists selectable models per provider and must agree with
`pricing.py`: a test asserts every catalogued model has a price.

## 3. `resume_pipeline/llm/fake.py`

```python
class FakeLLMClient:
    provider: str
    model: str
    def __init__(self, *, stage_responses: Mapping[str, str] | None = None,
                 fixtures_dir: Path | None = None, provider: str = "fake",
                 model: str = "fake-model") -> None: ...
    calls: list[dict[str, Any]]          # one record per call: stage, system, user, at
    async def complete(self, *, system_prompt, user_prompt, max_tokens=6000) -> Completion: ...
```

Implements `LLMClient`. It must return **schema-valid output for every stage**, because the graph
parses what it returns:
- `targeting` and `review` → strict JSON that `parse_strict_json_object` accepts. A review response
  must carry a `resume` object with a `category_scores` map covering all eight rubric categories,
  plus `must_fix` and `fix_resolution` lists, so `attach_scores` produces a real number.
- `generation`, `revision`, `cover_letter` → LaTeX that actually compiles: a complete document
  with `\documentclass`, `\begin{document}` and `\end{document}`.

Resolution order for a response: an explicit `stage_responses` entry, then a fixture at
`fixtures_dir/<stage>/<sha256(user_prompt)[:16]>.json`, then a generic valid response for that
stage. Determinism matters more than realism: the same prompt always yields the same output.

Stage detection is by inspection of the prompt, and the rule must be stated rather than guessed:
the caller sets it. Add an optional `stage: str | None = None` keyword to `complete` that the
factory-built clients ignore and the fake uses; when it is absent the fake infers the stage from
markers in the prompt and falls back to `"generation"`.

A driving knob for tests, since the revision loop is the thing most worth exercising:
`FakeLLMClient(score_sequence=[6.5, 8.6])` makes successive `review` responses score in that
order, so a test can force exactly one revision cycle and then a pass.

Fixtures live at `tests/fixtures/llm/<stage>/*.json` and are the test agent's to write, not yours.

## 4. `resume_pipeline/crypto.py`

```python
def seal(user_id: str, plaintext: str, *, master_key: bytes | None = None) -> bytes: ...
def open_sealed(user_id: str, ciphertext: bytes, *, master_key: bytes | None = None) -> str: ...
```

Envelope encryption, AES-256-GCM. The data key is derived per user from the master key with
HKDF-SHA256 using the user id as `info`, so a ciphertext sealed for user A cannot be opened as
user B. Stored form is `nonce || tag || payload` as `bytea`; the nonce is 12 random bytes per seal,
so sealing the same plaintext twice gives different ciphertexts.

The master key comes from `settings.master_key`, base64, exactly 32 bytes decoded; anything else
raises at load. These are the only two functions the module exposes — no "get the data key"
helper, because every extra surface is another place a key can leak.

`open_sealed` raises `Forbidden` on any authentication failure, with a message that does not say
whether the ciphertext, the user, or the key was wrong.

## 5. `resume_pipeline/llm/credentials.py`

```python
@dataclass(frozen=True)
class RunCredentials:
    keys: Mapping[str, str]              # provider → plaintext, in memory only
    def require(self, provider: str) -> str: ...   # raises MissingApiKey with details.provider

async def resolve_for_run(conn, user_id: str, providers: Iterable[str]) -> RunCredentials: ...
```

Decrypts once per run, in memory, inside the pipeline process. A key is never bound to a log
context, never in an exception message, never written to `resume_runs` jsonb, and `RunCredentials`
must not render its keys in `repr`. Write `__repr__` explicitly; do not rely on the dataclass
default, which prints every field.

## 6. `resume_pipeline/llm/factory.py`

```python
@dataclass(frozen=True)
class RunClients:
    generation: LLMClient
    review: LLMClient
    revision: LLMClient

@dataclass(frozen=True)
class ModelSelection:
    generation_model: str
    review_model: str
    revision_model: str

async def clients_for_run(conn, user_id: str, selection: ModelSelection, *,
                          mode: Literal["fake","live"] | None = None) -> RunClients: ...
```

- `mode` defaults to `settings.llm_mode`. In `fake` mode it returns three `FakeLLMClient`s and
  **touches neither the key table nor the network**.
- In `live` mode it resolves every provider the three models require and raises `MissingApiKey`
  with `details.provider` **before the graph starts**, not on the first call. A run that dies
  halfway because of a missing key has already spent money.
- v1's split is the default: a strong model reviews, a generation model writes, a cheap model
  revises. Preserve it as the default selection.

## 7. `resume_pipeline/repositories/keys.py` additions

```python
async def list_for_user(conn, user_id) -> list[KeyRow]      # never includes ciphertext
async def upsert(conn, user_id, *, provider, label, secret) -> str
async def delete(conn, user_id, key_id) -> None
async def mark_used(conn, user_id, provider) -> None
```
`KeyRow` carries `id, provider, label, last_four, created_at, last_used_at` and **no field capable
of holding the secret**. `upsert` seals before writing and derives `last_four` from the last four
characters of the plaintext.

## Acceptance criteria

1. `seal`/`open_sealed` round-trips; a ciphertext sealed for user A raises `Forbidden` when opened
   for user B; sealing the same plaintext twice gives different bytes.
2. A master key that is not exactly 32 decoded bytes raises at load.
3. `RunCredentials` and `KeyRow` never render a secret in `repr`, `str`, or a serialised form —
   assert by sealing a recognisable sentinel and grepping the rendered output for it.
4. A client that always returns 429 retries three times then raises `UpstreamFailed`.
5. A client that returns 400 is **not** retried — assert with a call counter.
6. An authentication failure raises a named error immediately and is not retried.
7. In `fake` mode, `clients_for_run` makes no database query and no network call even when the
   user has no keys at all.
8. In `live` mode, a missing provider key raises `MissingApiKey` with `details.provider`, and no
   LLM call is attempted.
9. `FakeLLMClient` returns `parse_strict_json_object`-parseable JSON for targeting and review, with
   all eight rubric categories present, and `\documentclass`-bearing LaTeX for the three text
   stages. Same prompt in, same output out.
10. `score_sequence` drives successive review scores in order.
11. Every model in `catalog.py` has a price in `pricing.py`.
12. No test opens a socket; no test needs a real API key.

## Test paths (test agent writes only here)

```
tests/llm/test_base.py
tests/llm/test_parse_strict_json.py
tests/llm/test_retry_policy.py
tests/llm/test_fake_client.py
tests/llm/test_catalog_pricing.py
tests/llm/test_factory.py
tests/llm/test_credentials.py
tests/test_crypto.py
tests/repositories/test_keys.py
tests/fixtures/llm/**            (fixture JSON for the fake client)
```

Drive the real provider clients by injecting a stub SDK object rather than patching the network —
the retry-policy tests must prove the policy, not the transport.

## Source paths (implementing agent writes only here)

```
resume_pipeline/llm/{base,anthropic,openai,catalog,factory,fake,credentials}.py
resume_pipeline/crypto.py
resume_pipeline/repositories/keys.py
```
