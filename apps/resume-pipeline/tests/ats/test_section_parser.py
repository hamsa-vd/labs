"""Tests for section parser."""

from __future__ import annotations

from resume_pipeline.ats.resume_parser import parse
from resume_pipeline.ats.section_parser import parse_sections


_SAMPLE_RESUME = """PROFESSIONAL SUMMARY
Backend engineer with 5 years of experience.

TECHNICAL SKILLS
Python, Java, Spring Boot, AWS, Docker

WORK EXPERIENCE
Software Engineer | Acme Corp
- Built REST APIs.
- Optimised Redis caching.

EDUCATION
B.Tech in Computer Science | MIT | 2020
"""


def test_detects_standard_sections():
    sections = parse_sections(_SAMPLE_RESUME)
    names = [s.name for s in sections]
    assert any("summary" in n for n in names), f"No summary section found. Sections: {names}"
    assert any("skill" in n or "technical" in n for n in names), f"No skills section. Sections: {names}"
    assert any("experience" in n for n in names), f"No experience section. Sections: {names}"
    assert any("education" in n for n in names), f"No education section. Sections: {names}"


def test_skills_section_has_highest_weight():
    sections = parse_sections(_SAMPLE_RESUME)
    skills = next((s for s in sections if "skill" in s.name or "technical" in s.name), None)
    assert skills is not None, "Skills section not found"
    assert skills.weight >= 2.5, f"Skills section should have weight ≥2.5, got {skills.weight}"


def test_experience_section_higher_weight_than_education():
    sections = parse_sections(_SAMPLE_RESUME)
    exp = next((s for s in sections if "experience" in s.name), None)
    edu = next((s for s in sections if "education" in s.name), None)
    assert exp is not None and edu is not None
    assert exp.weight > edu.weight, (
        f"Experience ({exp.weight}) should outweigh Education ({edu.weight})"
    )


def test_fallback_single_section_for_no_headers():
    plain = "John Doe. Python developer. Built APIs. MIT 2020."
    sections = parse_sections(plain)
    assert len(sections) == 1
    assert sections[0].name == "full_resume" or sections[0].text == plain.strip()


def test_latex_resume_header_preserves_education_content():
    latex = r"""\documentclass{article}
\begin{document}
\section*{EDUCATION}
\resumeHeader{B.Tech in Electronics, SRM University}{2020}
\end{document}
"""
    sections = parse_sections(parse(latex))
    education = next((section for section in sections if section.name == "education"), None)
    assert education is not None
    assert "B.Tech in Electronics" in education.text
    assert "2020" in education.text
