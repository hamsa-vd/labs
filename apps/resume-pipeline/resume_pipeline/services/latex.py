"""Client for the containerised Tectonic compiler (RG-035).

v1 shelled out to a local `latexmk`. v2 must not: the `.tex` is user input and TeX has file and
shell primitives in it, so compilation happens in a sandboxed container and this module only
talks to it over HTTP.

Two behaviours here are contractual rather than incidental.

**A PDF failure never loses the `.tex`.** `compile_tex` returns a `CompileResult` with
`ok=False` for every failure that is the document's fault — a TeX error, a timeout, an oversized
source. It raises only when the service itself cannot be reached. That is what lets `compile_pdfs`
populate `compile_errors` and still finish the run as `complete_with_compile_errors`, which is v1
behaviour worth keeping.

**A denylisted macro never reaches Tectonic.** `assert_valid_tex` runs first, on this side of the
wire, so `\\write18` is rejected without a request being made at all. The container's `--untrusted`
flag and its sandbox are the second and third layers, not the first.

The cache is deliberately behind a tiny interface. The durable implementation — the
`resume_documents` table keyed on `content_hash` plus the blob store — belongs to another work
package and is not written yet, so the default here is an in-memory LRU. Swapping it in later is
`set_document_cache(PostgresDocumentCache(...))` and changes no signature.
"""

from __future__ import annotations

import hashlib
import os
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from resume_pipeline.errors import UpstreamFailed
from resume_pipeline.latex.validate import assert_valid_tex

DEFAULT_LATEX_SERVICE_URL = "http://127.0.0.1:58080"

# The service caps itself at 20 seconds of wall clock. Allow for the round trip on top of that.
REQUEST_TIMEOUT_SECONDS = 35.0

DEFAULT_PASSES = 2

_UNREACHABLE = (
    "The LaTeX compiler is not responding, so the PDF was not produced. "
    "The .tex is saved; try compiling again in a moment."
)


@dataclass(frozen=True)
class CompileResult:
    ok: bool
    pdf: bytes | None
    pages: int | None
    error: str | None
    error_line: int | None
    log: str | None
    cached: bool


@dataclass(frozen=True)
class CachedDocument:
    """What the cache stores for one `content_hash`: the rendered PDF and its page count."""

    pdf: bytes
    pages: int | None


class DocumentCache(Protocol):
    """Content-addressed store for compiled PDFs, keyed on `sha256` of the source.

    The durable implementation reads and writes the `resume_documents` row for `content_hash` and
    fetches the bytes from the blob store, so a hit survives a restart. Both methods are async so
    that implementation needs no wrapper.
    """

    async def get(self, key: str) -> CachedDocument | None: ...

    async def put(self, key: str, document: CachedDocument) -> None: ...


class InMemoryDocumentCache:
    """Bounded LRU cache. The default until the durable store lands.

    It is process-local, so it is a latency saving and not a durability guarantee.
    """

    def __init__(self, max_entries: int = 32) -> None:
        self._max_entries = max_entries
        self._entries: OrderedDict[str, CachedDocument] = OrderedDict()

    async def get(self, key: str) -> CachedDocument | None:
        document = self._entries.get(key)
        if document is None:
            return None
        self._entries.move_to_end(key)
        return document

    async def put(self, key: str, document: CachedDocument) -> None:
        self._entries[key] = document
        self._entries.move_to_end(key)
        while len(self._entries) > self._max_entries:
            self._entries.popitem(last=False)

    def clear(self) -> None:
        self._entries.clear()


_cache: DocumentCache = InMemoryDocumentCache()


def get_document_cache() -> DocumentCache:
    return _cache


def set_document_cache(cache: DocumentCache) -> None:
    """Install the cache `compile_tex` uses when it is not given one explicitly."""
    global _cache
    _cache = cache


def reset_document_cache() -> None:
    """Restore a fresh in-memory cache. Isolates one caller's compiles from another's."""
    global _cache
    _cache = InMemoryDocumentCache()


def cache_key(tex: str) -> str:
    """The `content_hash` for a source: sha256 of its UTF-8 bytes, lowercase hex."""
    return hashlib.sha256(tex.encode("utf-8")).hexdigest()


def _service_url() -> str:
    """Base URL of the compile service.

    `settings.latex_service_url` is the eventual home of this value, but the settings module is
    another work package's and may not exist yet, so it is read defensively and falls back to the
    environment and then to the port `docker-compose.dev.yml` binds.
    """
    for module_name in ("resume_pipeline.config", "resume_pipeline.settings"):
        try:
            module = __import__(module_name, fromlist=["settings"])
        except ImportError:
            continue
        settings = getattr(module, "settings", None)
        url = getattr(settings, "latex_service_url", None)
        if url:
            return str(url).rstrip("/")
    return os.environ.get("RESUME_LATEX_SERVICE_URL", DEFAULT_LATEX_SERVICE_URL).rstrip("/")


def _error_body(response: httpx.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError:
        return {}
    if not isinstance(payload, dict):
        return {}
    error = payload.get("error")
    return error if isinstance(error, dict) else {}


def _failure_from(response: httpx.Response) -> CompileResult:
    error = _error_body(response)
    details = error.get("details")
    details = details if isinstance(details, dict) else {}
    line = details.get("line")
    message = error.get("message")
    return CompileResult(
        ok=False,
        pdf=None,
        pages=None,
        error=str(message)
        if message
        else "The document could not be compiled. Check the template and try again.",
        error_line=int(line) if isinstance(line, int) else None,
        log=str(details["log"]) if isinstance(details.get("log"), str) else None,
        cached=False,
    )


def _page_count_header(response: httpx.Response) -> int | None:
    raw = response.headers.get("x-page-count")
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


async def compile_tex(
    tex: str,
    *,
    client: httpx.AsyncClient | None = None,
    cache: DocumentCache | None = None,
    passes: int = DEFAULT_PASSES,
) -> CompileResult:
    """Compile `tex` to a PDF through the compile service.

    Raises `ValidationFailed` when the source trips the denylist — that check runs before any
    request is made, so a denied macro never reaches Tectonic. Raises `UpstreamFailed` when the
    service is unreachable or returns a 5xx. Every other failure, including a TeX error and a
    compile timeout, comes back as `ok=False` so the caller can record it and keep the `.tex`.

    `client` is injectable so tests can drive it through an `httpx.MockTransport` with no
    container running.
    """
    assert_valid_tex(tex)

    store = cache if cache is not None else _cache
    key = cache_key(tex)
    hit = await store.get(key)
    if hit is not None:
        return CompileResult(
            ok=True,
            pdf=hit.pdf,
            pages=hit.pages,
            error=None,
            error_line=None,
            log=None,
            cached=True,
        )

    url = f"{_service_url()}/compile"
    owned = client is None
    http = client or httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS)
    try:
        try:
            response = await http.post(url, json={"tex": tex, "passes": passes})
        except httpx.HTTPError as exc:
            # Never put the source or the exception chain in the message: this text reaches a user.
            raise UpstreamFailed(_UNREACHABLE) from exc
    finally:
        if owned:
            await http.aclose()

    if response.status_code >= 500:
        raise UpstreamFailed(_UNREACHABLE)

    if response.status_code != 200:
        return _failure_from(response)

    pdf = response.content
    pages = _page_count_header(response)
    await store.put(key, CachedDocument(pdf=pdf, pages=pages))
    return CompileResult(
        ok=True,
        pdf=pdf,
        pages=pages,
        error=None,
        error_line=None,
        log=None,
        cached=False,
    )
