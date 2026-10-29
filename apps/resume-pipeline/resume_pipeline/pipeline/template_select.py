"""Deterministic template recommendation (RG-021).

Ported from v1 `resume_agent/resume_selection.py`. The single change: v2 has no filesystem
template registry, so the five keys are defined locally as `TEMPLATE_KEYS` instead of being read
from `storage.template_options()`. Keyword rules, weights, boosts, the fullstack bonus and the
tie-break order are unchanged.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

TEMPLATE_KEYS = ["frontend", "backend-java", "backend-python", "fullstack", "senior-engineer"]


@dataclass(frozen=True)
class TemplateRecommendation:
    template_key: str
    scores: dict[str, int]
    matched_terms: dict[str, list[str]]
    reason: str


KEYWORD_RULES: dict[str, list[str]] = {
    "frontend": [
        "react",
        "typescript",
        "javascript",
        "frontend",
        "front-end",
        "spa",
        "single page application",
        "next.js",
        "nextjs",
        "angular",
        "redux",
        "vite",
        "webpack",
        "storybook",
        "ui",
    ],
    "backend-java": [
        "java",
        "spring",
        "spring boot",
        "spring security",
        "jvm",
        "kotlin",
        "scala",
        "microservices",
        "rest api",
        "restful",
        "mongodb",
        "dynamodb",
    ],
    "backend-python": [
        "python",
        "django",
        "fastapi",
        "flask",
        "ml",
        "machine learning",
        "ai",
        "llm",
        "rag",
        "langchain",
        "automation",
        "data pipeline",
    ],
    "fullstack": [
        "full stack",
        "fullstack",
        "front end and back end",
        "frontend and backend",
        "react",
        "typescript",
        "api",
        "backend",
        "node",
        "node.js",
        "cloud",
    ],
    "senior-engineer": [
        "senior",
        "staff",
        "lead",
        "mentor",
        "mentoring",
        "architecture",
        "technical design",
        "system design",
        "operational excellence",
    ],
}


EXPLICIT_TITLE_BOOSTS: list[tuple[str, str, int]] = [
    (r"\b(frontend|front-end|front end)\b", "frontend", 80),
    (r"\b(fullstack|full-stack|full stack)\b", "fullstack", 80),
    (r"\b(java|spring)\b", "backend-java", 60),
    (r"\b(python|django|fastapi|flask)\b", "backend-python", 60),
    (r"\b(senior|staff|lead)\b", "senior-engineer", 50),
]


TIE_BREAK_ORDER = ["frontend", "backend-java", "backend-python", "fullstack", "senior-engineer"]


def recommend_template(jd_text: str, job_title: str = "") -> TemplateRecommendation:
    text = f"{job_title}\n{jd_text}".lower()
    title = job_title.lower()
    scores = {key: 0 for key in TEMPLATE_KEYS}
    matched_terms: dict[str, list[str]] = {key: [] for key in TEMPLATE_KEYS}

    for template_key, terms in KEYWORD_RULES.items():
        for term in terms:
            count = _count_term(text, term)
            if count:
                scores[template_key] += count * _term_weight(term)
                matched_terms[template_key].append(term)

    for pattern, template_key, boost in EXPLICIT_TITLE_BOOSTS:
        if re.search(pattern, title):
            scores[template_key] += boost

    _apply_mixed_fullstack_bonus(scores, matched_terms)

    selected = max(TIE_BREAK_ORDER, key=lambda key: (scores[key], -TIE_BREAK_ORDER.index(key)))
    reason = _build_reason(selected, scores, matched_terms)
    return TemplateRecommendation(selected, scores, matched_terms, reason)


def _count_term(text: str, term: str) -> int:
    escaped = re.escape(term.lower())
    if re.search(r"[a-z0-9]", term):
        pattern = rf"(?<![a-z0-9]){escaped}(?![a-z0-9])"
    else:
        pattern = escaped
    return len(re.findall(pattern, text))


def _term_weight(term: str) -> int:
    if " " in term or "." in term or "-" in term:
        return 3
    return 2


def _apply_mixed_fullstack_bonus(scores: dict[str, int], matched_terms: dict[str, list[str]]) -> None:
    frontend_has_signal = bool(
        set(matched_terms["frontend"]) & {"react", "typescript", "frontend", "angular"}
    )
    backend_has_signal = bool(
        set(matched_terms["backend-java"] + matched_terms["backend-python"])
        & {"java", "spring", "python", "django", "fastapi", "microservices", "rest api"}
    )
    if frontend_has_signal and backend_has_signal:
        scores["fullstack"] += 25


def _build_reason(template_key: str, scores: dict[str, int], matched_terms: dict[str, list[str]]) -> str:
    terms = ", ".join(matched_terms.get(template_key, [])[:8])
    if terms:
        return f"Recommended {template_key} based on: {terms}."
    return f"Recommended {template_key} by default because no stronger role signal was found."
