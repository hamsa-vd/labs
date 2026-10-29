# WP3 — API foundation: settings, errors, logging, storage, repositories

Discharges RG-004, RG-007, and the storage half of RG-006, as adapted by ADR-100.

Root: `apps/resume-pipeline/`. Run with `make check` (ruff, mypy strict, pytest).

The service binds to `127.0.0.1` and is never internet-reachable. Ascend is its only client and
holds the Cloudflare Access identity; it passes the resolved user on every call. This service
therefore trusts the caller's identity assertion but must still scope every query by `user_id` —
a bug in ascend must not become a cross-tenant read.

`resume_pipeline/errors.py` already exists and is shared. Do not rewrite it. It provides
`AppError`, `NotFound`, `Forbidden`, `Conflict`, `ValidationFailed`, `BudgetExceeded`,
`UpstreamFailed`, `MissingApiKey`, each with `code`, `status`, `details` and `.envelope()`.

---

## 1. `resume_pipeline/settings.py`

`pydantic-settings`. Fails at import when a required variable is absent — not at first request,
because a misconfigured service that starts and then 500s is worse than one that refuses to start.

```python
class Settings(BaseSettings):
    database_url: str                       # required
    service_token: str                      # required; shared secret ascend presents
    documents_dir: Path                     # required; blob root
    document_url_secret: str                # required; HMAC key for signed document URLs
    master_key: str                         # required; base64, 32 bytes, for BYOK envelope encryption
    latex_service_url: str = "http://127.0.0.1:58080"
    llm_mode: Literal["fake", "live"] = "fake"
    log_level: str = "info"
    environment: Literal["development", "production"] = "development"
    model_config = SettingsConfigDict(env_prefix="RESUME_", env_file=".env", extra="ignore")

def get_settings() -> Settings: ...   # lru_cache'd
```

`llm_mode` defaults to `"fake"`. Live mode is opt-in, never the default: a test or a stray dev
process must not be able to spend the user's money by omission.

Add `apps/resume-pipeline/.env.example` with every variable, one comment line each, no TODOs.

## 2. `resume_pipeline/logging.py`

```python
def configure_logging(level: str = "info") -> None: ...
def redact(logger, method_name, event_dict) -> dict: ...   # structlog processor
def bind_request(request_id: str, user_id: str | None = None, run_id: str | None = None) -> None: ...
```

structlog, JSON to stdout. The `redact` processor:
- removes any key whose lower-cased name contains `api_key`, `apikey`, `authorization`, `secret`,
  `token`, `ciphertext`, `password`, `tex`, `jd_text`, `resume_text`, `jd`, `body`;
- truncates any remaining string longer than 500 characters to 500 plus `"…"`;
- recurses into nested dicts and into lists of dicts.

Removal means the key is absent from the output, not present with a placeholder — a key named
`api_key` in a log line is a finding even when its value is masked.

Test it per key name, not in aggregate.

## 3. `resume_pipeline/telemetry.py`

```python
@dataclass(frozen=True)
class LlmUsage:
    input_tokens: int = 0
    output_tokens: int = 0

async def record_llm_call(
    conn, *, run_id: str, user_id: str, node: str, provider: str, model: str,
    usage: LlmUsage, latency_ms: int | None = None,
) -> Decimal: ...
```

Inserts one `resume_llm_calls` row, computes its cost from `llm/pricing.py`, and increments
`resume_runs.cost_usd` and the `token_usage` rollup on the run in the same transaction. Returns
the cost of this call.

`token_usage` accumulates as `{"<node>": {"input_tokens": n, "output_tokens": n, "calls": n,
"cost_usd": "0.0123"}}`, plus a `"prompts"` key the run service writes separately. Money is
`Decimal`, never `float`, and serialises as a string.

A model absent from the pricing table is a hard failure — raise `UpstreamFailed` naming the model
rather than silently recording zero. A silent zero is how a cost bug survives to production.

`resume_pipeline/llm/pricing.py`:
```python
@dataclass(frozen=True)
class ModelPrice:
    input_per_mtok: Decimal
    output_per_mtok: Decimal
    as_of: str          # ISO date
PRICES: dict[str, ModelPrice]
def price_for(model: str) -> ModelPrice: ...      # raises UpstreamFailed when unknown
def cost_of(model: str, usage: LlmUsage) -> Decimal: ...
```
Populate `PRICES` with the current Anthropic and OpenAI text models, each with an `as_of` date.
Include at minimum the three roles v1 used plus cheap revision models. Getting a price slightly
stale is acceptable; a missing entry is not.

## 4. `resume_pipeline/db.py`

```python
async def pool() -> asyncpg.Pool: ...          # lazily created, reused
async def close_pool() -> None: ...
@asynccontextmanager
async def connection() -> AsyncIterator[asyncpg.Connection]: ...
@asynccontextmanager
async def transaction() -> AsyncIterator[asyncpg.Connection]: ...
```

Nothing outside `repositories/` executes SQL.

## 5. `resume_pipeline/storage/`

`base.py` — the protocol D1 mandated, so the backend stays swappable:
```python
class BlobStore(Protocol):
    async def put(self, path: str, data: bytes, content_type: str) -> str: ...
    async def get(self, path: str) -> bytes: ...
    async def signed_url(self, path: str, ttl_seconds: int = 60) -> str: ...
    async def delete(self, path: str) -> None: ...
    async def exists(self, path: str) -> bool: ...
```

`paths.py` — the only place a storage path is constructed:
```python
DocumentKind = Literal["resume_tex","resume_pdf","cover_letter_tex","cover_letter_pdf",
                       "jd","imported_resume","template_preview"]
EXTENSIONS: dict[DocumentKind, str]          # tex→.tex, pdf→.pdf, jd→.txt, preview→.png
CONTENT_TYPES: dict[DocumentKind, str]
def document_path(user_id: str, application_id: str, run_id: str | None, kind: DocumentKind) -> str: ...
```
Shape: `{user_id}/{application_id}/{run_id or "_"}/{kind}{ext}`. Every segment must be validated
as a UUID (or the literal `_`) before it is joined, so a crafted id cannot escape the root with
`..` or an absolute path. Reject with `ValidationFailed`.

`local.py` — `LocalBlobStore(root: Path)` implementing the protocol against the filesystem:
- `put` creates parent directories, writes atomically (temp file then rename), returns the path;
- every method resolves the final path and asserts it is inside `root`, raising `ValidationFailed`
  otherwise — defence in depth behind `paths.py`, because this is the class that touches the disk;
- `get` on a missing path raises `NotFound`;
- `delete` on a missing path is a no-op, not an error.

`signed.py` — the ascend-side redemption contract:
```python
def sign_document_url(path: str, ttl_seconds: int, secret: str, *, now: int | None = None) -> str: ...
def verify_document_token(token: str, secret: str, *, now: int | None = None) -> str: ...
```
The token carries the path and an absolute expiry, authenticated with HMAC-SHA256 over both, and
is URL-safe base64. `verify_document_token` returns the path or raises `Forbidden` — on a bad
signature, on expiry, and on a malformed token alike, with the same message for each so the token
cannot be probed. Comparison is constant-time. `now` is injectable so expiry is testable without
sleeping.

## 6. `resume_pipeline/repositories/`

Every function takes `user_id` as its first argument after the connection and includes
`user_id = $n` in its `where` clause. A read that finds nothing raises `NotFound`; it never
returns another user's row and never distinguishes "does not exist" from "not yours" — do not
leak existence.

`applications.py`
```python
async def get(conn, user_id, application_id) -> ApplicationRow
async def create(conn, user_id, *, company, role, jd_text, jd_source_type, jd_url, origin, status="draft") -> str
async def list_for_user(conn, user_id, *, status=None, query=None, limit=50, cursor=None) -> tuple[list[ApplicationRow], str | None]
async def update_tracking(conn, user_id, application_id, **fields) -> ApplicationRow
async def find_by_migration_key(conn, user_id, migrated_from) -> ApplicationRow | None
```
`create` computes `company_slug`/`role_slug` with `util/slug.py::slugify`, ported verbatim from
v1's `storage.slugify`. Cursor pagination on `(updated_at desc, id desc)`, never offset.

`documents.py`
```python
async def insert(conn, user_id, *, application_id, run_id, kind, storage_path, byte_size, content_hash, content_type) -> str
async def get(conn, user_id, document_id) -> DocumentRow
async def list_for_run(conn, user_id, run_id) -> list[DocumentRow]
async def find_by_hash(conn, user_id, kind, content_hash) -> DocumentRow | None
```
Every `put` to the blob store is paired with an `insert` here. The row is the index; nothing lists
the directory to find a file.

`runs.py`, `sot.py`, `templates.py`, `prompts.py` — CRUD over their tables, same rules.
`keys.py` is **not** yours: WP4 owns it, because it owns the encryption that seals what goes in.
Keep them thin: no business logic, no LLM, no HTTP. Signatures follow the same shape as above;
derive the exact set from the columns in `apps/ascend/supabase/migrations/0006_resume_generator.sql`
(already written — read it, it is the schema of record).

`util/slug.py` — `slugify(value: str, fallback: str = "untitled") -> str`, ported verbatim from
`Resume/resume_generator/resume_agent/storage.py`. NFKD-normalise, drop non-ASCII, lower-case,
non-alphanumeric runs to a single `-`, strip leading and trailing `-`, fall back when empty.

## 7. `resume_pipeline/main.py` and `deps.py`

```python
def create_app() -> FastAPI: ...
app = create_app()
```
- Routers mount under `/v1`.
- One exception handler renders every `AppError` through `.envelope()` at its `status`.
  A bare `Exception` handler logs with the request id and returns `internal_error` with a generic
  sentence — never a stack trace, never the exception's own message.
- Request-id middleware accepts or mints `X-Request-Id`, binds it to the log context, echoes it in
  the response header.
- `deps.py` provides `current_user_id` (reads `X-Ascend-User` after validating the service token in
  `Authorization: Bearer <service_token>`), `db_connection`, and `blob_store`. A wrong or absent
  service token is `403 forbidden`; an absent or non-UUID `X-Ascend-User` is `403` too, with the
  same message, so the endpoint cannot be used to probe which half was wrong.
- `GET /v1/health` returns `{"status": "ok"|"degraded", "version": str, "db": "ok"|"degraded"}` and
  is the one route that does not require the service token.

## Acceptance criteria

1. A missing required setting raises at import time, naming the variable.
2. A raised `NotFound` renders exactly `{"error":{"code":"not_found","message":…,"details":{}}}` at 404.
3. An unhandled exception returns `internal_error` at 500 and its message appears nowhere in the body.
4. `X-Request-Id` is echoed; when absent one is minted and still echoed.
5. Every redaction key is removed, verified one key at a time, including nested and in-list cases.
6. A signed document URL verifies before its TTL and raises `Forbidden` after it; a token with one
   byte flipped raises `Forbidden`; the two failures are indistinguishable from the message.
7. `document_path` rejects a non-UUID segment and any `..`; `LocalBlobStore` refuses to read or
   write outside its root even when handed a crafted path directly.
8. A blob round-trips: put, get, exists, delete, and `get` after delete raises `NotFound`.
9. `record_llm_call` accumulates cost and token counts correctly across three calls spanning two
   providers, and an unpriced model raises rather than recording zero.
10. Every repository read for user B on user A's row raises `NotFound`.
11. `GET /v1/health` answers without a service token; every other route refuses without one.
12. No test opens a network socket. No log line in any test contains a secret or a document body.

## Test paths (test agent writes only here)

```
tests/test_settings.py
tests/test_logging_redaction.py
tests/test_telemetry.py
tests/test_pricing.py
tests/storage/test_paths.py
tests/storage/test_local_blob_store.py
tests/storage/test_signed_urls.py
tests/repositories/test_applications.py
tests/repositories/test_documents.py
tests/repositories/test_ownership.py
tests/test_app_errors.py
tests/test_deps_auth.py
tests/test_slug.py
```

Repository tests need Postgres. Follow the opt-in pattern: read `RESUME_DATABASE_URL` (or
`TEST_DATABASE_URL`) and skip cleanly when absent, so the default suite stays offline. A dev
database is running at `postgres://ascend:ascend@127.0.0.1:55432/ascend` with every migration
applied. The socket guard added in WP2's `tests/conftest.py` must keep working — allow localhost
Postgres connections through it, block everything else.

## Source paths (implementing agent writes only here)

```
resume_pipeline/settings.py
resume_pipeline/logging.py
resume_pipeline/telemetry.py
resume_pipeline/db.py
resume_pipeline/main.py
resume_pipeline/deps.py
resume_pipeline/llm/pricing.py
resume_pipeline/storage/{base,paths,local,signed}.py
resume_pipeline/repositories/{applications,documents,runs,sot,templates,prompts}.py
resume_pipeline/routers/health.py
resume_pipeline/schemas/common.py
resume_pipeline/util/slug.py
apps/resume-pipeline/.env.example
```
