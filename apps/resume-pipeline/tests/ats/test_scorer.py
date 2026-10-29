"""Tests for the ATS scoring engine."""

from __future__ import annotations

import pytest

from resume_pipeline.ats.scorer import score


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _resume(skills: str = "", experience: str = "", summary: str = "") -> str:
    return f"""PROFESSIONAL SUMMARY
{summary or 'Backend engineer with 5 years of experience.'}

TECHNICAL SKILLS
{skills or 'Python, Java, Spring Boot, AWS, Docker, Kubernetes, PostgreSQL, Redis'}

WORK EXPERIENCE
Software Engineer | Acme Corp | 2020-2025
- {experience or 'Built high-throughput REST APIs using Spring Boot and deployed on AWS EKS.'}
- Optimised Redis caching reducing latency by 40%.
- Implemented Prometheus and Grafana monitoring dashboards.
- Designed and delivered microservices architecture on Kubernetes.
- Reduced infrastructure cost by 30% through EKS autoscaling.

EDUCATION
B.Tech in Computer Science | MIT | 2020
"""


def _jd(text: str = "") -> str:
    return text or """
We are looking for a Software Development Engineer with experience in:
Requirements:
- Java, Spring Boot microservices
- AWS (EKS, DynamoDB, Lambda)
- Redis caching and high-throughput systems
- REST API design
- Kubernetes and Docker
Preferred:
- Scala or Kotlin
- Kafka for event-driven architecture
- Prometheus and Grafana monitoring
Nice to have:
- Couchbase or Memcached
- Agile development experience
"""


# ─── Core score range tests ────────────────────────────────────────────────────

def test_well_matched_resume_scores_high():
    result = score(_resume(), _jd())
    assert result.total_score >= 55, f"Expected ≥55, got {result.total_score}"


def test_empty_resume_scores_low():
    result = score("John Doe", _jd())
    assert result.total_score < 30, f"Expected <30, got {result.total_score}"


def test_unrelated_resume_scores_low():
    unrelated = """
PROFESSIONAL SUMMARY
Professional chef with 10 years of culinary experience.

SKILLS
Knife skills, French cuisine, pastry, baking, menu planning

WORK EXPERIENCE
Head Chef | Le Cordon Bleu | 2015-2025
- Prepared 200+ covers per night.
- Trained junior chefs in classic techniques.

EDUCATION
Culinary Arts Diploma | 2015
"""
    result = score(unrelated, _jd())
    assert result.total_score < 35, f"Expected <35 for unrelated resume, got {result.total_score}"


def test_perfect_keyword_match_scores_keyword_component_high():
    jd = "Requires: Python, Docker, Kubernetes, AWS, PostgreSQL, Redis, REST API, CI/CD, Git"
    resume = _resume(
        skills="Python, Docker, Kubernetes, AWS, PostgreSQL, Redis, REST API, CI/CD, Git",
        experience="Deployed Python microservices on Kubernetes via Docker. Used AWS, PostgreSQL, Redis.",
    )
    result = score(resume, jd)
    assert result.keyword.score >= 30, f"Expected keyword score ≥30, got {result.keyword.score}"


def test_synonym_matching_js_javascript():
    """'JS' in resume should match 'JavaScript' in JD."""
    jd = "Requires: JavaScript, React, Node.js"
    resume = _resume(skills="JS, React, Node")
    result = score(resume, jd)
    assert "javascript" in result.keyword.matched or result.keyword.score > 15, (
        f"JS should match JavaScript. Matched: {result.keyword.matched}"
    )


def test_synonym_matching_k8s_kubernetes():
    jd = "Experience with Kubernetes required."
    resume = _resume(experience="Deployed services on k8s clusters using Helm.")
    result = score(resume, jd)
    assert "kubernetes" in result.keyword.matched, (
        f"k8s should match Kubernetes. Matched: {result.keyword.matched}"
    )


def test_missing_required_keywords_listed():
    jd = "Requires: Scala, Kotlin, Couchbase"
    resume = _resume(skills="Python, Java, Redis")
    result = score(resume, jd)
    missing = set(result.keyword.missing_required)
    assert "scala" in missing or "kotlin" in missing, (
        f"Scala/Kotlin should be missing required. Got: {missing}"
    )


def test_skills_section_weighted_higher_than_body():
    """Same keyword in Skills section should score higher than buried in experience."""
    resume_skills = _resume(skills="Spring Boot, AWS, Redis, Kafka", experience="Worked on backend.")
    resume_buried = "PROFESSIONAL SUMMARY\nEngineer.\n\nWORK EXPERIENCE\nUsed Spring Boot, AWS, Redis, Kafka.\n\nEDUCATION\nB.Tech 2020"
    jd = "Requires: Spring Boot, AWS, Redis, Kafka"
    result_skills = score(resume_skills, jd)
    result_buried = score(resume_buried, jd)
    assert result_skills.keyword.score >= result_buried.keyword.score, (
        "Skills-section keyword score should be ≥ buried-in-experience score"
    )


def test_strong_action_verbs_improve_structural_score():
    strong_bullets = _resume(experience="Architected distributed system reducing latency by 60%.")
    weak_bullets = "PROFESSIONAL SUMMARY\nEngineer.\n\nTECHNICAL SKILLS\nPython.\n\nWORK EXPERIENCE\n- Responsible for backend systems.\n- Helped with API development.\n\nEDUCATION\nB.Tech 2020"
    result_strong = score(strong_bullets, _jd())
    result_weak = score(weak_bullets, _jd())
    assert result_strong.structural.action_verb_score >= result_weak.structural.action_verb_score, (
        "Strong verb bullets should score higher on action_verb_score"
    )


def test_quantified_bullets_improve_quantification_score():
    quantified = _resume(
        experience="Reduced latency by 40%. Grew user base by 3x. Cut infra cost by $50K/yr."
    )
    vague = _resume(experience="Improved latency. Grew user base. Reduced costs.")
    result_q = score(quantified, _jd())
    result_v = score(vague, _jd())
    assert result_q.structural.quantification_score >= result_v.structural.quantification_score, (
        "Quantified bullets should score higher on quantification"
    )


def test_section_completeness_full_resume():
    result = score(_resume(), _jd())
    assert result.structural.section_completeness_score == 10.0, (
        f"Full resume should have section_completeness=10, got {result.structural.section_completeness_score}"
    )


def test_section_completeness_missing_education():
    no_edu = """PROFESSIONAL SUMMARY
Engineer with 5 years experience.

TECHNICAL SKILLS
Python, AWS, Docker

WORK EXPERIENCE
- Built microservices using Python.
- Deployed on AWS EKS.
"""
    result = score(no_edu, _jd())
    assert "education" in result.structural.missing_sections, (
        f"Missing education should be flagged. Got: {result.structural.missing_sections}"
    )


def test_top_actions_non_empty_for_weak_resume():
    result = score("John Doe, software engineer", _jd())
    assert len(result.top_actions) > 0, "Should surface actions for a weak resume"


def test_grade_labels():
    from resume_pipeline.ats.scorer import _grade
    assert _grade(85) == "Excellent"
    assert _grade(70) == "Good"
    assert _grade(50) == "Fair"
    assert _grade(30) == "Poor"


def test_latex_resume_parsed_correctly():
    """LaTeX resume text should be stripped and scored."""
    latex = r"""
\documentclass{article}
\begin{document}
\section*{PROFESSIONAL SUMMARY}
Backend engineer with 5 years of experience in Java and Spring Boot.

\section*{TECHNICAL SKILLS}
Java, Spring Boot, AWS, Docker, Kubernetes, PostgreSQL, Redis Caching

\section*{WORK EXPERIENCE}
\textbf{Software Engineer} | Acme Corp | 2020-2025
\begin{itemize}
\item Built high-throughput REST APIs using Spring Boot deployed on AWS EKS.
\item Optimised Redis caching reducing latency by 40\%.
\end{itemize}

\section*{EDUCATION}
B.Tech in Computer Science | MIT | 2020
\end{document}
"""
    result = score(latex, _jd())
    assert result.total_score >= 35, f"LaTeX resume should parse and score reasonably, got {result.total_score}"
    assert "java" in result.keyword.matched or "spring boot" in result.keyword.matched, (
        f"Java/Spring Boot should be matched from LaTeX. Matched: {result.keyword.matched}"
    )


# ─── Hard requirements tests ───────────────────────────────────────────────────

from resume_pipeline.ats.hard_requirements import check_hard_requirements


def test_years_experience_met():
    """Resume with 8 years should satisfy a 5+ year JD requirement."""
    jd = "Requirements:\n- 5+ years of experience in backend development\n- Python, AWS"
    resume = _resume(summary="Backend engineer with 8 years of experience in Python and AWS.")
    result = check_hard_requirements(jd, resume)
    yr = next((r for r in result.requirements if r.kind == "years_experience"), None)
    assert yr is not None, "Should detect years-of-experience requirement"
    assert yr.met, f"8 years should satisfy 5+ requirement; resume_years inferred as unmet"


def test_years_experience_not_met():
    """Resume with 2 years should NOT satisfy a 5+ year JD requirement."""
    jd = "Requirements:\n- 5+ years of experience in backend development"
    resume = _resume(summary="Junior engineer with 2 years of experience.")
    result = check_hard_requirements(jd, resume)
    yr = next((r for r in result.requirements if r.kind == "years_experience"), None)
    assert yr is not None
    assert not yr.met, "2 years should NOT satisfy a 5+ year requirement"
    assert not result.all_met


def test_degree_requirement_detected_and_met():
    """Bachelor's degree requirement met by B.Tech in resume."""
    jd = "Requires a Bachelor's degree in Computer Science or related field."
    resume = "EDUCATION\nB.Tech in Computer Science | MIT | 2020"
    result = check_hard_requirements(jd, resume)
    deg = next((r for r in result.requirements if r.kind == "degree"), None)
    assert deg is not None, "Should detect degree requirement"
    assert deg.met, "B.Tech counts as Bachelor's level — should be met"


def test_degree_not_met_when_masters_required():
    """Master's requirement should NOT be met by just a Bachelor's."""
    jd = "Requires a Master's degree or PhD in Computer Science."
    resume = "EDUCATION\nB.S. in Computer Science | State University | 2022"
    result = check_hard_requirements(jd, resume)
    deg = next((r for r in result.requirements if r.kind == "degree"), None)
    assert deg is not None, "Should detect Master's degree requirement"
    assert not deg.met, "B.S. should not satisfy a Master's requirement"


def test_certification_detected_and_met():
    """AWS cert in JD should be flagged; if resume has it, mark met."""
    jd = "Preferred: AWS Certified Solutions Architect certification is a plus."
    resume = "CERTIFICATIONS\nAWS Certified Solutions Architect – Associate (2023)"
    result = check_hard_requirements(jd, resume)
    cert = next((r for r in result.requirements if r.kind == "certification"), None)
    assert cert is not None, "Should detect AWS cert requirement"
    assert cert.met, "Resume lists AWS Certified Solutions Architect — should be met"


def test_certification_not_met():
    """PMP in JD, resume doesn't mention it — should be unmet."""
    jd = "Requires PMP certification."
    resume = _resume(summary="Project lead with 5 years of experience managing teams.")
    result = check_hard_requirements(jd, resume)
    cert = next((r for r in result.requirements if r.kind == "certification"), None)
    assert cert is not None, "Should detect PMP requirement"
    assert not cert.met, "Resume without PMP should be unmet"
    assert cert in result.unmet


def test_no_hard_requirements_in_minimal_jd():
    """A simple skills-only JD should return no hard requirements."""
    jd = "Requirements:\n- Python, Django, PostgreSQL, Redis"
    resume = _resume()
    result = check_hard_requirements(jd, resume)
    assert result.requirements == [], f"No hard requirements expected; got {result.requirements}"
    assert result.all_met


def test_hard_requirements_attached_to_ats_result():
    """score() should include hard_requirements in ATSResult."""
    jd = "Requirements:\n- 3+ years of experience\n- Python, AWS, Docker"
    resume = _resume(summary="Engineer with 5 years of experience in Python and cloud.")
    result = score(resume, jd)
    assert hasattr(result, "hard_requirements"), "ATSResult should have hard_requirements field"
    assert isinstance(result.hard_requirements.requirements, list)
