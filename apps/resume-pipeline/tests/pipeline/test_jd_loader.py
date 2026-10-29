"""Job description loading (WP2 §4).

The four `test_load_jd_from_text_rejects_short_text` / `test_extract_text_from_html_removes_scripts`
/ `test_detect_blocked_or_auth_page` / `test_*_job_description` cases are v1's own tests
(`tests/fixtures/v1/test_jd_loader.py`) with only the import path changed.

Every network path is driven through an httpx MockTransport passed as the `client` keyword
argument. No test here opens a socket; `tests/conftest.py` enforces that for the whole suite.
"""

from __future__ import annotations

import dataclasses

import httpx
import pytest

from resume_pipeline.pipeline.budgets import MIN_JD_TEXT_LENGTH
from resume_pipeline.pipeline.jd_loader import (
    JDLoadResult,
    detect_blocked_or_auth_page,
    extract_text_from_html,
    fetch_jd_from_url,
    load_jd_from_text,
    load_jd_from_upload,
    looks_like_job_description,
    normalize_text,
)

URL = "https://jobs.example.com/senior-backend-engineer"

JD_BODY = """
Senior Backend Engineer

Responsibilities
In this role, you will design and operate Python and Java microservices on AWS, build
event-driven pipelines with Kafka, and own the observability of the platform end to end.

Qualifications
5+ years of experience building backend applications. Experience with Spring Boot,
FastAPI, PostgreSQL, Redis, Kubernetes and Terraform. Familiarity with Prometheus.
"""

BOILERPLATE = (
    """
    Skip to Main Content
    Company
    Customers
    Careers
    Investors
    Products
    Privacy Policy
    Cookies are used on this site to assist in improving the candidate experience.
    """
    * 4
)

BLOCK_PAGE = (
    "Please verify you are human before continuing. "
    "Our security service protects this page from automated traffic. "
    "If you believe this is an error, contact the site owner and try again later. "
    "Reference number 12345678. Additional details are available in our help centre. "
    "Access to this page is restricted while the check completes. Please wait a moment "
    "and reload the page once the verification has finished running in your browser."
)


def _client(handler: object) -> httpx.Client:
    """An httpx client whose transport is a stub. It can never reach the network."""
    return httpx.Client(transport=httpx.MockTransport(handler))  # type: ignore[arg-type]


def _html(body: str) -> str:
    return f"<html><head><title>Job</title></head><body><main>{body}</main></body></html>"


# ─── v1 regression tests, import path changed only ────────────────────────────


def test_load_jd_from_text_rejects_short_text() -> None:
    result = load_jd_from_text("short")
    assert not result.ok
    assert "too short" in (result.error or "")


def test_extract_text_from_html_removes_scripts() -> None:
    html = "<html><body><main><h1>Role</h1><script>bad()</script><p>Build APIs.</p></main></body></html>"
    text = extract_text_from_html(html)
    assert "Role" in text
    assert "Build APIs" in text
    assert "bad()" not in text


def test_detect_blocked_or_auth_page() -> None:
    assert detect_blocked_or_auth_page("Please sign in to apply") is not None


def test_boilerplate_navigation_is_not_job_description() -> None:
    text = """
    Skip to Main Content
    Company
    Customers
    Careers
    Investors
    Products
    Jira Software
    Confluence
    Privacy Policy
    Copyright 2026 Atlassian
    Cookies are used on this site to assist in improving the candidate experience.
    """ * 4

    assert not looks_like_job_description(text)


def test_rendered_job_text_is_job_description() -> None:
    text = """
    We're looking for a Backend Software Engineer to join our Growth team.

    Responsibilities
    In this role, you will drive complex projects from technical design to launch,
    lead code reviews, and partner across engineering teams.

    Qualifications
    4+ years of experience building backend applications. Experience with Java,
    Python, Kotlin, Go, Scala, cloud architecture, and collaboration.
    """

    assert looks_like_job_description(text)


# ─── The suite-wide network guard (RG-008) ────────────────────────────────────


def test_the_network_guard_is_active() -> None:
    import socket

    with pytest.raises(RuntimeError) as excinfo:
        socket.create_connection(("example.com", 80), timeout=0.1)
    assert "network" in str(excinfo.value).lower()

    with pytest.raises(RuntimeError):
        socket.getaddrinfo("example.com", 80)


# ─── JDLoadResult ─────────────────────────────────────────────────────────────


def test_jd_load_result_defaults_and_frozen() -> None:
    result = JDLoadResult("some text")
    assert result.error is None
    assert result.source_type == "text"
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.text = "other"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("text", "error", "expected_ok"),
    [
        ("a real job description", None, True),
        ("", None, False),
        ("   \n\t ", None, False),
        ("a real job description", "something went wrong", False),
        ("", "something went wrong", False),
    ],
)
def test_ok_requires_no_error_and_non_blank_text(text: str, error: str | None, expected_ok: bool) -> None:
    assert JDLoadResult(text, error).ok is expected_ok


# ─── load_jd_from_text ────────────────────────────────────────────────────────


def test_text_at_the_minimum_length_is_accepted() -> None:
    result = load_jd_from_text("a" * MIN_JD_TEXT_LENGTH)
    assert result.ok
    assert result.error is None
    assert result.source_type == "text"
    assert len(result.text) == MIN_JD_TEXT_LENGTH


def test_text_one_character_below_the_minimum_is_rejected() -> None:
    result = load_jd_from_text("a" * (MIN_JD_TEXT_LENGTH - 1))
    assert not result.ok
    assert result.error
    assert result.text == ""
    assert result.source_type == "text"


def test_length_is_measured_after_normalisation() -> None:
    # Whitespace-padded text that only clears 300 characters before normalising is rejected.
    padded = "word " + (" " * 400) + "word"
    assert len(padded) > MIN_JD_TEXT_LENGTH
    assert not load_jd_from_text(padded).ok


def test_accepted_text_is_returned_normalised() -> None:
    raw = "Role\r\n\r\n\r\n\r\nWe   need   engineers. " + ("filler words here. " * 30)
    result = load_jd_from_text(raw)
    assert result.ok
    assert "\r" not in result.text
    assert "\n\n\n" not in result.text
    assert "   " not in result.text
    assert result.text == result.text.strip()


def test_empty_text_is_rejected() -> None:
    result = load_jd_from_text("")
    assert not result.ok
    assert result.text == ""


# ─── normalize_text ───────────────────────────────────────────────────────────


def test_normalize_text_unescapes_html_entities() -> None:
    assert normalize_text("R&amp;D &lt;team&gt;") == "R&D <team>"


def test_normalize_text_converts_carriage_returns() -> None:
    assert "\r" not in normalize_text("one\r\ntwo\rthree")


def test_normalize_text_collapses_spaces_and_tabs() -> None:
    assert normalize_text("a   \t  b") == "a b"


def test_normalize_text_collapses_three_or_more_newlines_to_two() -> None:
    assert normalize_text("a\n\n\n\n\nb") == "a\n\nb"


def test_normalize_text_strips_outer_whitespace() -> None:
    assert normalize_text("\n\n  hello  \n\n") == "hello"


def test_normalize_text_is_idempotent() -> None:
    once = normalize_text("a\r\n\n\n\n  b   c  ")
    assert normalize_text(once) == once


# ─── extract_text_from_html ───────────────────────────────────────────────────


def test_extract_text_drops_style_noscript_and_svg() -> None:
    html = (
        "<html><body><main><p>Keep this.</p>"
        "<style>.a{color:red}</style>"
        "<noscript>Enable JS</noscript>"
        "<svg><title>icon</title></svg>"
        "</main></body></html>"
    )
    text = extract_text_from_html(html)
    assert "Keep this." in text
    assert "color:red" not in text
    assert "Enable JS" not in text
    assert "icon" not in text


def test_extract_text_prefers_main_then_article_then_body() -> None:
    main_html = "<html><body><nav>Nav</nav><main>Main content</main></body></html>"
    assert "Nav" not in extract_text_from_html(main_html)
    assert "Main content" in extract_text_from_html(main_html)

    article_html = "<html><body><nav>Nav</nav><article>Article content</article></body></html>"
    assert "Article content" in extract_text_from_html(article_html)
    assert "Nav" not in extract_text_from_html(article_html)

    body_html = "<html><body><p>Body content</p></body></html>"
    assert "Body content" in extract_text_from_html(body_html)


def test_extract_text_separates_block_elements_with_newlines() -> None:
    text = extract_text_from_html("<html><body><main><p>One</p><p>Two</p></main></body></html>")
    assert "OneTwo" not in text


# ─── looks_like_job_description ───────────────────────────────────────────────


def test_short_text_is_never_a_job_description() -> None:
    assert not looks_like_job_description("Backend engineer. Responsibilities. Requirements.")


def test_a_single_signal_is_not_enough() -> None:
    text = ("We love cats and we have many of them in the office. " * 10) + "Requirements to enter."
    assert len(text) > MIN_JD_TEXT_LENGTH
    assert not looks_like_job_description(text)


# ─── detect_blocked_or_auth_page ──────────────────────────────────────────────


@pytest.mark.parametrize(
    "marker",
    [
        "sign in to apply",
        "log in to continue",
        "login to continue",
        "access denied",
        "enable javascript",
        "verify you are human",
        "captcha",
        "cloudflare",
    ],
)
def test_every_block_marker_is_detected(marker: str) -> None:
    assert detect_blocked_or_auth_page(f"Sorry. {marker.title()} to see this page.") is not None


def test_clean_text_is_not_flagged_as_blocked() -> None:
    assert detect_blocked_or_auth_page(JD_BODY) is None


def test_a_long_page_that_merely_mentions_a_marker_is_not_flagged() -> None:
    long_page = JD_BODY + " We use captcha on our signup form. " + ("More detail about the role. " * 60)
    assert len(long_page) >= 1500
    assert detect_blocked_or_auth_page(long_page) is None


# ─── load_jd_from_upload ──────────────────────────────────────────────────────


@pytest.mark.parametrize("name", ["jd.txt", "jd.md", "JD.TXT", "notes.MD", "some.name.txt"])
def test_upload_accepts_txt_and_md(name: str) -> None:
    result = load_jd_from_upload(name, JD_BODY.encode("utf-8"))
    assert result.ok
    assert result.source_type == "upload"
    assert "Responsibilities" in result.text


@pytest.mark.parametrize("name", ["jd.pdf", "jd.docx", "jd.rtf", "jd", "jd.txt.pdf", "jd.text"])
def test_upload_rejects_every_other_suffix(name: str) -> None:
    result = load_jd_from_upload(name, JD_BODY.encode("utf-8"))
    assert not result.ok
    assert result.error
    assert result.text == ""
    assert result.source_type == "upload"


def test_upload_of_non_utf8_bytes_is_an_error_not_an_exception() -> None:
    result = load_jd_from_upload("jd.txt", b"\xff\xfe\x00\x01 not utf-8 at all \xc3\x28")
    assert not result.ok
    assert result.error
    assert result.text == ""
    assert result.source_type == "upload"


def test_upload_shorter_than_the_minimum_is_rejected_as_upload() -> None:
    result = load_jd_from_upload("jd.txt", b"too short")
    assert not result.ok
    assert result.error
    assert result.source_type == "upload"


def test_upload_decodes_utf8_content() -> None:
    body = "Résumé rôle — naïve café. " + JD_BODY
    result = load_jd_from_upload("jd.md", body.encode("utf-8"))
    assert result.ok
    assert "Résumé rôle — naïve café." in result.text


# ─── fetch_jd_from_url ────────────────────────────────────────────────────────


@pytest.mark.parametrize("url", ["", "   ", "\n\t"])
def test_a_blank_url_errors_without_making_a_request(url: str) -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        return httpx.Response(200, html=_html(f"<p>{JD_BODY}</p>"))

    result = fetch_jd_from_url(url, client=_client(handler))
    assert calls == []
    assert not result.ok
    assert result.error
    assert result.text == ""
    assert result.source_type == "url"


def test_an_html_response_is_reduced_to_text_before_the_length_check() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            html=_html(f"<h1>Senior Backend Engineer</h1><p>{JD_BODY}</p><script>track()</script>"),
        )

    result = fetch_jd_from_url(URL, client=_client(handler))
    assert result.ok
    assert result.error is None
    assert result.source_type == "url"
    assert "Responsibilities" in result.text
    assert "track()" not in result.text
    assert "<h1>" not in result.text


def test_a_non_html_response_is_used_as_is() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=JD_BODY, headers={"content-type": "text/plain"})

    result = fetch_jd_from_url(URL, client=_client(handler))
    assert result.ok
    assert result.text == normalize_text(JD_BODY)


def test_an_html_body_served_as_plain_text_is_still_stripped() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, text=_html(f"<p>{JD_BODY}</p>"), headers={"content-type": "text/plain"}
        )

    result = fetch_jd_from_url(URL, client=_client(handler))
    assert result.ok
    assert "<p>" not in result.text


@pytest.mark.parametrize("status", [400, 401, 403, 404, 429, 500, 502, 503])
def test_an_error_status_returns_an_error_result_and_never_raises(status: int) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, html=_html(f"<p>{JD_BODY}</p>"))

    result = fetch_jd_from_url(URL, client=_client(handler))
    assert not result.ok
    assert result.error
    assert str(status) in result.error
    assert result.text == ""
    assert result.source_type == "url"


def test_a_timeout_returns_an_error_result_and_never_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timed out", request=request)

    result = fetch_jd_from_url(URL, timeout_seconds=0.5, client=_client(handler))
    assert not result.ok
    assert result.error
    assert result.text == ""
    assert result.source_type == "url"


def test_a_transport_error_returns_an_error_result_and_never_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    result = fetch_jd_from_url(URL, client=_client(handler))
    assert not result.ok
    assert result.error
    assert result.text == ""


def test_a_response_shorter_than_the_minimum_is_an_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, html=_html("<p>Backend engineer wanted. Responsibilities.</p>"))

    result = fetch_jd_from_url(URL, client=_client(handler))
    assert not result.ok
    assert result.error
    assert result.text == ""


def test_a_block_page_longer_than_the_minimum_is_still_an_error() -> None:
    assert len(BLOCK_PAGE) > MIN_JD_TEXT_LENGTH

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, html=_html(f"<p>{BLOCK_PAGE}</p>"))

    result = fetch_jd_from_url(URL, client=_client(handler))
    assert not result.ok
    assert result.error
    assert result.text == ""


def test_a_login_wall_is_an_error() -> None:
    wall = "Sign in to apply for this role. " + ("Create an account to continue browsing jobs. " * 6)
    assert len(wall) > MIN_JD_TEXT_LENGTH

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, html=_html(f"<p>{wall}</p>"))

    result = fetch_jd_from_url(URL, client=_client(handler))
    assert not result.ok
    assert result.error


def test_page_boilerplate_longer_than_the_minimum_is_an_error() -> None:
    assert len(BOILERPLATE) > MIN_JD_TEXT_LENGTH
    assert not looks_like_job_description(BOILERPLATE)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, html=_html(f"<p>{BOILERPLATE}</p>"))

    result = fetch_jd_from_url(URL, client=_client(handler))
    assert not result.ok
    assert result.error
    assert result.text == ""


def test_the_requested_url_is_the_one_fetched() -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        return httpx.Response(200, html=_html(f"<p>{JD_BODY}</p>"))

    assert fetch_jd_from_url(URL, client=_client(handler)).ok
    assert seen == [URL]


def test_client_is_keyword_only() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, html=_html(f"<p>{JD_BODY}</p>"))

    with pytest.raises(TypeError):
        fetch_jd_from_url(URL, 12.0, _client(handler))  # type: ignore[misc]


def test_fetching_is_deterministic_for_the_same_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, html=_html(f"<p>{JD_BODY}</p>"))

    first = fetch_jd_from_url(URL, client=_client(handler))
    second = fetch_jd_from_url(URL, client=_client(handler))
    assert first == second
