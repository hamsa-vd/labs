"""The compile client (WP7 §4 and §5).

Two behaviours carry the weight here.

**A PDF failure never loses the `.tex`.** That is v1 behaviour the port must keep: a compile error
populates `compile_errors` and the run still finishes, distinguished as
`complete_with_compile_errors`. So a TeX error comes back as `CompileResult(ok=False, ...)`, never
as an exception. Only an unreachable service raises.

**A denylisted macro never reaches Tectonic.** The validator runs on this side too, which is only
meaningful if it runs *before* the request. Every test that asserts it does so by counting
requests through the stub transport, because "it was rejected" and "it was rejected before it left
the process" are different claims and only the second one is security.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from types import ModuleType

import httpx
import pytest

from resume_pipeline.errors import UpstreamFailed, ValidationFailed
from tests.latex.test_validate import DENIED_IDS, DENIED_PAYLOADS

STUB_BASE_URL = "http://latex.invalid"

PDF_BYTES = b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n%%EOF\n"

TEX_LOG = (
    "This is Tectonic 0.17.0\n"
    "Running TeX ...\n"
    "! Undefined control sequence.\n"
    "l.42 \\resumeHeading\n"
    "                   {Liv-ex}{London, UK}\n"
    "No pages of output.\n"
)


def unique_tex(marker: str = "") -> str:
    """A valid document that no earlier test can have cached.

    The hash cache is keyed on the source, so a shared fixture would make request counts depend
    on test ordering. A nonce in a comment keeps each test independent.
    """
    nonce = marker or uuid.uuid4().hex
    return (
        "\\documentclass[11pt]{article}\n"
        f"% run {nonce}\n"
        "\\begin{document}\n"
        "Senior backend engineer, six years, Python and Java on AWS.\n"
        "\\end{document}\n"
    )


def tex_with(payload: str) -> str:
    return (
        "\\documentclass[11pt]{article}\n"
        f"% run {uuid.uuid4().hex}\n"
        "\\begin{document}\n"
        "Resume body.\n"
        f"{payload}\n"
        "\\end{document}\n"
    )


class Recorder:
    """A MockTransport handler that counts what actually left the process."""

    def __init__(self, handler: Callable[[httpx.Request], httpx.Response]) -> None:
        self._handler = handler
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        request.read()
        self.requests.append(request)
        return self._handler(request)

    @property
    def calls(self) -> int:
        return len(self.requests)


@asynccontextmanager
async def stub_service(
    handler: Callable[[httpx.Request], httpx.Response],
) -> AsyncIterator[tuple[httpx.AsyncClient, Recorder]]:
    recorder = Recorder(handler)
    transport = httpx.MockTransport(recorder)
    async with httpx.AsyncClient(transport=transport, base_url=STUB_BASE_URL) as client:
        yield client, recorder


def pdf_response(pages: int = 2, compile_ms: int = 812) -> Callable[[httpx.Request], httpx.Response]:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=PDF_BYTES,
            headers={
                "content-type": "application/pdf",
                "X-Page-Count": str(pages),
                "X-Compile-Ms": str(compile_ms),
            },
        )

    return handler


DEFAULT_FAILURE_MESSAGE = "Line 42 uses a command Tectonic does not know."


def compile_failed_response(
    line: int | None = 42,
    code: str = "compile_failed",
    message: str = DEFAULT_FAILURE_MESSAGE,
) -> Callable[[httpx.Request], httpx.Response]:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            422,
            json={
                "error": {
                    "code": code,
                    "message": message,
                    "details": {"line": line, "log": TEX_LOG},
                }
            },
        )

    return handler


def status_response(status: int) -> Callable[[httpx.Request], httpx.Response]:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(status, text="upstream is unwell")

    return handler


# ─── cache_key ────────────────────────────────────────────────────────────────


def test_cache_key_is_the_sha256_of_the_source(latex_service_mod: ModuleType) -> None:
    tex = unique_tex("stable")
    expected = hashlib.sha256(tex.encode("utf-8")).hexdigest()

    assert latex_service_mod.cache_key(tex) == expected


def test_cache_key_is_stable_and_sixty_four_hex_characters(latex_service_mod: ModuleType) -> None:
    tex = unique_tex("stable")

    key = latex_service_mod.cache_key(tex)
    assert key == latex_service_mod.cache_key(tex)
    assert len(key) == 64
    assert all(character in "0123456789abcdef" for character in key)


def test_cache_key_differs_for_a_one_character_change(latex_service_mod: ModuleType) -> None:
    first = latex_service_mod.cache_key(unique_tex("stable"))
    second = latex_service_mod.cache_key(unique_tex("stable") + " ")

    assert first != second


# ─── Success ──────────────────────────────────────────────────────────────────


async def test_a_successful_compile_returns_the_pdf_and_the_page_count(
    latex_service_mod: ModuleType,
) -> None:
    tex = unique_tex()

    async with stub_service(pdf_response(pages=2)) as (client, recorder):
        result = await latex_service_mod.compile_tex(tex, client=client)

    assert recorder.calls == 1
    assert result.ok is True
    assert result.pdf == PDF_BYTES
    assert result.pages == 2
    assert result.error is None
    assert result.error_line is None
    assert result.cached is False


async def test_the_request_posts_the_source_to_the_compile_route(
    latex_service_mod: ModuleType,
) -> None:
    tex = unique_tex()

    async with stub_service(pdf_response()) as (client, recorder):
        await latex_service_mod.compile_tex(tex, client=client)

    assert recorder.calls == 1
    request = recorder.requests[0]
    assert request.method == "POST"
    assert request.url.path.endswith("/compile"), f"Unexpected route: {request.url}"

    body = json.loads(request.content)
    assert body["tex"] == tex, "The source must be sent verbatim; Tectonic compiles what it is given."


# ─── A TeX error is a result, not an exception ────────────────────────────────


async def test_a_tex_error_returns_ok_false_rather_than_raising(
    latex_service_mod: ModuleType,
) -> None:
    """v1 behaviour the port must keep: a PDF failure never loses the .tex."""
    tex = unique_tex()

    async with stub_service(compile_failed_response(line=42)) as (client, _):
        result = await latex_service_mod.compile_tex(tex, client=client)

    assert result.ok is False
    assert result.pdf is None
    assert result.pages is None
    assert result.error_line == 42
    assert result.error, "A failure with no message leaves the user nothing to act on."
    assert result.cached is False


async def test_a_tex_error_keeps_the_log_out_of_the_user_facing_message(
    latex_service_mod: ModuleType,
) -> None:
    tex = unique_tex()

    async with stub_service(compile_failed_response(line=42)) as (client, _):
        result = await latex_service_mod.compile_tex(tex, client=client)

    assert result.log is not None, "Operators need the full log even though the user does not."
    assert "Undefined control sequence" in result.log
    assert result.error is not None
    assert "\n" not in result.error.strip(), "The user-facing error is one sentence."
    assert result.error != result.log
    assert "This is Tectonic" not in result.error


async def test_a_tex_error_without_a_line_number_reports_no_line(
    latex_service_mod: ModuleType,
) -> None:
    async with stub_service(compile_failed_response(line=None)) as (client, _):
        result = await latex_service_mod.compile_tex(unique_tex(), client=client)

    assert result.ok is False
    assert result.error_line is None


async def test_a_compile_timeout_is_a_result_not_an_exception(
    latex_service_mod: ModuleType,
) -> None:
    """A document that loops forever is still the document's fault, so the run must survive it."""
    handler = compile_failed_response(
        line=None,
        code="compile_timeout",
        message="The document took too long to compile. Simplify it and try again.",
    )

    async with stub_service(handler) as (client, _):
        result = await latex_service_mod.compile_tex(unique_tex(), client=client)

    assert result.ok is False
    assert result.pdf is None
    assert result.error


# ─── An unreachable service raises ────────────────────────────────────────────


@pytest.mark.parametrize("status", [500, 502, 503, 504])
async def test_a_server_error_raises_upstream_failed(
    latex_service_mod: ModuleType, status: int
) -> None:
    async with stub_service(status_response(status)) as (client, _):
        with pytest.raises(UpstreamFailed):
            await latex_service_mod.compile_tex(unique_tex(), client=client)


async def test_a_transport_failure_raises_upstream_failed(latex_service_mod: ModuleType) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    async with stub_service(handler) as (client, _):
        with pytest.raises(UpstreamFailed):
            await latex_service_mod.compile_tex(unique_tex(), client=client)


async def test_a_read_timeout_raises_upstream_failed(latex_service_mod: ModuleType) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    async with stub_service(handler) as (client, _):
        with pytest.raises(UpstreamFailed):
            await latex_service_mod.compile_tex(unique_tex(), client=client)


async def test_upstream_failed_says_it_is_retryable_and_leaks_nothing(
    latex_service_mod: ModuleType,
) -> None:
    secret = "Architected a Kafka pipeline for Liv-ex settlement"
    tex = (
        "\\documentclass[11pt]{article}\n"
        f"% run {uuid.uuid4().hex}\n"
        "\\begin{document}\n"
        f"{secret}\n"
        "\\end{document}\n"
    )

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    async with stub_service(handler) as (client, _):
        with pytest.raises(UpstreamFailed) as caught:
            await latex_service_mod.compile_tex(tex, client=client)

    error = caught.value
    assert error.code == "upstream_failed"
    assert "!" not in error.message
    assert "Traceback" not in error.message, "A stack trace is not a user-facing message."
    assert secret not in str(error), "Secrets rule: never put a resume body in an exception."
    assert any(
        phrase in error.message.lower() for phrase in ("try again", "retry", "again in a moment")
    ), f"The message must tell the user it is worth retrying, got {error.message!r}."


# ─── Nothing denylisted ever leaves the process ───────────────────────────────


async def attempt(latex_service_mod: ModuleType, tex: str, client: httpx.AsyncClient) -> bool:
    """Compile `tex` and report whether it was rejected, by either shape the contract allows.

    §4 says `compile_tex` runs `assert_valid_tex` first, which raises. §5 says a failure that is
    the document's fault returns `ok=False` rather than raising. A denylist hit is both, so these
    tests accept either — what they do not accept is the request being made.
    """
    try:
        result = await latex_service_mod.compile_tex(tex, client=client)
    except ValidationFailed:
        return True
    return bool(result.ok is False)


async def test_a_write18_payload_never_reaches_the_service(
    latex_service_mod: ModuleType,
) -> None:
    """Acceptance criterion 6. The whole point of validating on this side is that the request is
    never made, so the assertion is on the request count, not only on the rejection."""
    tex = tex_with(r"\write18{echo owned}")

    async with stub_service(pdf_response()) as (client, recorder):
        rejected = await attempt(latex_service_mod, tex, client)

    assert recorder.calls == 0, (
        f"A \\write18 payload reached the compiler service ({recorder.calls} request(s)). "
        "The denylist must run before the request is built."
    )
    assert rejected, "A \\write18 payload must never compile."


@pytest.mark.parametrize("payload", DENIED_PAYLOADS, ids=DENIED_IDS)
async def test_no_denied_construct_ever_reaches_the_service(
    latex_service_mod: ModuleType, payload: str
) -> None:
    async with stub_service(pdf_response()) as (client, recorder):
        rejected = await attempt(latex_service_mod, tex_with(payload), client)

    assert recorder.calls == 0, f"{payload!r} reached the compiler service."
    assert rejected, f"{payload!r} must never compile."


async def test_an_oversized_source_never_reaches_the_service(
    latex_service_mod: ModuleType,
) -> None:
    tex = tex_with("% " + ("a" * (200 * 1024)))

    async with stub_service(pdf_response()) as (client, recorder):
        rejected = await attempt(latex_service_mod, tex, client)

    assert recorder.calls == 0, "A source over the size limit must be rejected before the request."
    assert rejected


async def test_a_structurally_invalid_source_never_reaches_the_service(
    latex_service_mod: ModuleType,
) -> None:
    async with stub_service(pdf_response()) as (client, recorder):
        rejected = await attempt(latex_service_mod, "Just some prose.\n", client)

    assert recorder.calls == 0
    assert rejected


# ─── The hash cache ───────────────────────────────────────────────────────────


async def test_an_identical_source_is_served_from_the_cache(
    latex_service_mod: ModuleType,
) -> None:
    """Acceptance criterion 8: the second identical request does not invoke Tectonic."""
    tex = unique_tex()

    async with stub_service(pdf_response(pages=2)) as (client, recorder):
        first = await latex_service_mod.compile_tex(tex, client=client)
        second = await latex_service_mod.compile_tex(tex, client=client)

    assert first.ok is True
    assert first.cached is False
    assert second.ok is True
    assert second.cached is True, "A cache hit must say so; WP5 reports it to the user."
    assert second.pdf == first.pdf
    assert second.pages == first.pages
    assert recorder.calls == 1, (
        f"The compiler service was invoked {recorder.calls} times for one source. "
        "An identical source must come back from the cache."
    )


async def test_a_different_source_is_not_served_from_the_cache(
    latex_service_mod: ModuleType,
) -> None:
    async with stub_service(pdf_response()) as (client, recorder):
        await latex_service_mod.compile_tex(unique_tex(), client=client)
        second = await latex_service_mod.compile_tex(unique_tex(), client=client)

    assert second.cached is False
    assert recorder.calls == 2


async def test_a_failed_compile_is_not_cached_as_a_success(
    latex_service_mod: ModuleType,
) -> None:
    """Caching a failure would pin a broken document until the source changes."""
    tex = unique_tex()

    async with stub_service(compile_failed_response()) as (client, _):
        first = await latex_service_mod.compile_tex(tex, client=client)

    assert first.ok is False

    async with stub_service(pdf_response()) as (client, recorder):
        second = await latex_service_mod.compile_tex(tex, client=client)

    assert second.ok is True
    assert recorder.calls == 1, "A previous failure must not be replayed as a cached success."


# ─── Shape ────────────────────────────────────────────────────────────────────


async def test_compile_result_is_frozen(latex_service_mod: ModuleType) -> None:
    async with stub_service(pdf_response()) as (client, _):
        result = await latex_service_mod.compile_tex(unique_tex(), client=client)

    with pytest.raises(Exception):  # noqa: B017 - FrozenInstanceError is a dataclass detail
        result.ok = False
