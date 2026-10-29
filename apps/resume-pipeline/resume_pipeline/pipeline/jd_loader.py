"""Job description loading and validation.

Ported from v1 `resume_agent/jd_loader.py` with two changes:

- The Playwright fallback is dropped. v2 ships no headless browser, so `fetch_jd_from_url` keeps
  only the httpx path.
- `fetch_jd_from_url` takes a `client` keyword argument so a caller (or a test) can supply a
  pre-built httpx client and drive the URL path without a network.

The `MIN_JD_TEXT_LENGTH` guard is the gate that stops a run before any paid LLM call: short,
blocked or boilerplate-only text is rejected, never passed through with a warning.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from html import unescape
from typing import Any, Literal

import httpx
from bs4 import BeautifulSoup

from resume_pipeline.pipeline.budgets import MIN_JD_TEXT_LENGTH

JDSourceType = Literal["text", "upload", "url"]

_USER_AGENT = "Mozilla/5.0 resume-generator/1.0"


@dataclass(frozen=True)
class JDLoadResult:
    text: str
    error: str | None = None
    source_type: JDSourceType = "text"

    @property
    def ok(self) -> bool:
        return self.error is None and bool(self.text.strip())


def load_jd_from_text(text: str) -> JDLoadResult:
    cleaned = normalize_text(text)
    if len(cleaned) < MIN_JD_TEXT_LENGTH:
        return JDLoadResult("", "JD text is too short. Paste the full job description.", "text")
    return JDLoadResult(cleaned, None, "text")


def load_jd_from_upload(file_name: str, data: bytes) -> JDLoadResult:
    suffix = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
    if suffix not in {"txt", "md"}:
        return JDLoadResult("", "Only .txt and .md uploads are supported in the MVP.", "upload")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return JDLoadResult("", "Could not decode the uploaded file as UTF-8 text.", "upload")
    result = load_jd_from_text(text)
    return JDLoadResult(result.text, result.error, "upload")


def fetch_jd_from_url(
    url: str,
    timeout_seconds: float = 12.0,
    *,
    client: Any | None = None,
) -> JDLoadResult:
    """Fetch a job description over HTTP.

    `client` accepts a pre-built httpx client (or any object with a compatible `get`). When it is
    given it is used as-is and left open; the caller owns its lifetime.
    """
    if not url.strip():
        return JDLoadResult("", "Enter a job URL or paste the JD text.", "url")

    return _fetch_jd_httpx(url, timeout_seconds, client=client)


def _fetch_jd_httpx(url: str, timeout_seconds: float, *, client: Any | None = None) -> JDLoadResult:
    try:
        if client is not None:
            response = client.get(url)
        else:
            with httpx.Client(
                follow_redirects=True,
                timeout=timeout_seconds,
                headers={"User-Agent": _USER_AGENT},
            ) as owned_client:
                response = owned_client.get(url)
    except httpx.TimeoutException:
        return JDLoadResult("", "The URL timed out. Paste the JD text manually.", "url")
    except httpx.HTTPError as exc:
        return JDLoadResult("", f"Could not fetch the URL: {exc}", "url")

    if response.status_code >= 400:
        return JDLoadResult(
            "",
            f"The URL returned HTTP {response.status_code}. Paste the JD text manually.",
            "url",
        )

    content_type = response.headers.get("content-type", "")
    if "text/html" in content_type or "<html" in response.text[:500].lower():
        text = extract_text_from_html(response.text)
    else:
        text = response.text

    cleaned = normalize_text(text)
    blocked_reason = detect_blocked_or_auth_page(cleaned)
    if blocked_reason:
        return JDLoadResult("", blocked_reason, "url")
    if len(cleaned) < MIN_JD_TEXT_LENGTH:
        return JDLoadResult("", "The URL did not contain enough readable JD text. Paste it manually.", "url")
    if not looks_like_job_description(cleaned):
        return JDLoadResult(
            "",
            "The URL fetched successfully but only returned page boilerplate, "
            "not a readable job description.",
            "url",
        )
    return JDLoadResult(cleaned, None, "url")


def extract_text_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    main = soup.find("main") or soup.find("article") or soup.body or soup
    return str(main.get_text(separator="\n"))


def normalize_text(text: str) -> str:
    text = unescape(text or "")
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


_JOB_DESCRIPTION_SIGNALS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\b(software|backend|frontend|full.?stack|data|machine learning|platform)\s+(engineer|developer)\b",
        re.I,
    ),
    re.compile(r"\b(responsibilities|in this role|you will|what you.ll do)\b", re.I),
    re.compile(r"\b(qualifications|requirements|your background|what you.ll need|must have)\b", re.I),
    re.compile(r"\b(experience|familiarity|proficiency)\s+(with|in|building|working)\b", re.I),
    re.compile(
        r"\b(java|python|typescript|javascript|react|spring|kotlin|go|scala|aws|azure|kubernetes)\b",
        re.I,
    ),
)


def looks_like_job_description(text: str) -> bool:
    """Return True when extracted URL text has real JD signals, not only page chrome."""
    normalized = normalize_text(text)
    if len(normalized) < MIN_JD_TEXT_LENGTH:
        return False

    signal_count = sum(1 for pattern in _JOB_DESCRIPTION_SIGNALS if pattern.search(normalized))
    # Require at least two distinct signals so generic careers/navigation pages do
    # not pass merely because they mention "Careers" or a single product name.
    return signal_count >= 2


def detect_blocked_or_auth_page(text: str) -> str | None:
    lowered = text.lower()
    auth_markers = [
        "sign in to apply",
        "log in to continue",
        "login to continue",
        "access denied",
        "enable javascript",
        "verify you are human",
        "captcha",
        "cloudflare",
    ]
    for marker in auth_markers:
        if marker in lowered and len(text) < 1500:
            return "The URL appears blocked or behind authentication. Paste the JD text manually."
    return None
