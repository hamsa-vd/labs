"""Weighted review scoring (RG-034).

Ported verbatim from v1 `resume_agent/scoring.py`. The rubric weights came from a system that
produces good resumes; they are not adjustable here. Only this docstring differs from v1.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

RESUME_RUBRIC = {
    "jd_skills_keyword_match": 0.20,
    "role_domain_relevance": 0.15,
    "achievement_evidence_strength": 0.15,
    "credibility_source_truth_compliance": 0.15,
    "single_page_compliance": 0.15,
    "targeting_brief_compliance": 0.10,
    "ats_latex_formatting_safety": 0.05,
    "recruiter_impression_seniority_alignment": 0.05,
}

COVER_LETTER_RUBRIC = {
    "jd_company_alignment": 0.30,
    "evidence_relevance": 0.25,
    "motivation_domain_fit": 0.20,
    "clarity_tone": 0.15,
    "credibility_no_fabrication": 0.10,
}


@dataclass(frozen=True)
class ScoreResult:
    score: float
    missing_categories: list[str]


def score_resume_review(review: dict[str, Any]) -> ScoreResult:
    return weighted_score(review.get("category_scores", {}), RESUME_RUBRIC)


def score_cover_letter_review(review: dict[str, Any]) -> ScoreResult:
    return weighted_score(review.get("category_scores", {}), COVER_LETTER_RUBRIC)


def weighted_score(category_scores: dict[str, Any], rubric: dict[str, float]) -> ScoreResult:
    missing: list[str] = []
    total = 0.0
    for key, weight in rubric.items():
        if key not in category_scores:
            missing.append(key)
            value = 0.0
        else:
            value = _clamp_score(category_scores[key])
        total += value * weight
    return ScoreResult(round(total, 2), missing)


def attach_scores(review_payload: dict[str, Any]) -> dict[str, Any]:
    payload = dict(review_payload)
    if "resume" in payload and isinstance(payload["resume"], dict):
        result = score_resume_review(payload["resume"])
        payload["resume"] = dict(payload["resume"])
        payload["resume"]["score"] = result.score
        payload["resume"]["missing_score_categories"] = result.missing_categories
    if "cover_letter" in payload and isinstance(payload["cover_letter"], dict):
        result = score_cover_letter_review(payload["cover_letter"])
        payload["cover_letter"] = dict(payload["cover_letter"])
        payload["cover_letter"]["score"] = result.score
        payload["cover_letter"]["missing_score_categories"] = result.missing_categories
    return payload


def _clamp_score(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(10.0, numeric))
