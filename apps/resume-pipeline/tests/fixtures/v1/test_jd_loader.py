from __future__ import annotations

from resume_agent.jd_loader import (
    detect_blocked_or_auth_page,
    extract_text_from_html,
    load_jd_from_text,
    looks_like_job_description,
)


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
