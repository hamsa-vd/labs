"""Template recommendation (WP2 §3).

The three `test_recommends_*` cases are v1's own tests (`tests/fixtures/v1/test_resume_selection.py`)
with only the import path changed. The rest pin the scoring behaviour the contract lists, using
exact totals — this is a verbatim port, so a changed weight should fail loudly rather than drift.
"""

from __future__ import annotations

import dataclasses

import pytest

from resume_pipeline.pipeline.template_select import (
    EXPLICIT_TITLE_BOOSTS,
    KEYWORD_RULES,
    TEMPLATE_KEYS,
    TIE_BREAK_ORDER,
    TemplateRecommendation,
    recommend_template,
)

# ─── v1 regression tests, import path changed only ────────────────────────────


def test_recommends_frontend_for_react_typescript_jd() -> None:
    recommendation = recommend_template(
        "Build React TypeScript SPA interfaces with Redux and Vite.", "Frontend Engineer"
    )
    assert recommendation.template_key == "frontend"


def test_recommends_backend_java_for_spring_jd() -> None:
    jd = "Design Java 17 Spring Boot microservices, REST APIs, MongoDB, and Spring Security."
    recommendation = recommend_template(jd, "Backend Java Developer")
    assert recommendation.template_key == "backend-java"


def test_recommends_fullstack_for_mixed_frontend_backend_jd() -> None:
    jd = "Full Stack Engineer using React, TypeScript, backend APIs, Node.js, and cloud services."
    recommendation = recommend_template(jd, "Fullstack Software Engineer")
    assert recommendation.template_key == "fullstack"


# ─── Shape ────────────────────────────────────────────────────────────────────


def test_template_keys_are_the_five_contract_keys() -> None:
    assert TEMPLATE_KEYS == ["frontend", "backend-java", "backend-python", "fullstack", "senior-engineer"]


def test_tie_break_order_covers_every_template_key() -> None:
    assert TIE_BREAK_ORDER == ["frontend", "backend-java", "backend-python", "fullstack", "senior-engineer"]
    assert sorted(TIE_BREAK_ORDER) == sorted(TEMPLATE_KEYS)


def test_keyword_rules_cover_every_template_key() -> None:
    assert sorted(KEYWORD_RULES) == sorted(TEMPLATE_KEYS)
    for terms in KEYWORD_RULES.values():
        assert terms and all(term == term.lower() for term in terms)


def test_explicit_title_boosts_match_v1() -> None:
    assert EXPLICIT_TITLE_BOOSTS == [
        (r"\b(frontend|front-end|front end)\b", "frontend", 80),
        (r"\b(fullstack|full-stack|full stack)\b", "fullstack", 80),
        (r"\b(java|spring)\b", "backend-java", 60),
        (r"\b(python|django|fastapi|flask)\b", "backend-python", 60),
        (r"\b(senior|staff|lead)\b", "senior-engineer", 50),
    ]


def test_recommendation_is_a_frozen_dataclass_scored_over_every_key() -> None:
    recommendation = recommend_template("Python and Django services.", "Backend Engineer")
    assert isinstance(recommendation, TemplateRecommendation)
    assert sorted(recommendation.scores) == sorted(TEMPLATE_KEYS)
    assert sorted(recommendation.matched_terms) == sorted(TEMPLATE_KEYS)
    assert all(isinstance(value, int) for value in recommendation.scores.values())
    assert recommendation.template_key in TEMPLATE_KEYS
    with pytest.raises(dataclasses.FrozenInstanceError):
        recommendation.template_key = "frontend"  # type: ignore[misc]


def test_recommendation_is_deterministic() -> None:
    jd = "Java, Spring Boot, React, and Kubernetes."
    first = recommend_template(jd, "Software Engineer")
    second = recommend_template(jd, "Software Engineer")
    assert first == second


def test_job_title_defaults_to_empty_string() -> None:
    assert recommend_template("Python and FastAPI services.").template_key == "backend-python"


# ─── Word boundaries ──────────────────────────────────────────────────────────


def test_java_matches_on_a_word_boundary_but_not_inside_javascript() -> None:
    inside = recommend_template("javascript everywhere")
    assert "java" not in inside.matched_terms["backend-java"]
    assert inside.scores["backend-java"] == 0
    assert "javascript" in inside.matched_terms["frontend"]

    boundary = recommend_template("Java 17 rules")
    assert boundary.matched_terms["backend-java"] == ["java"]
    assert boundary.scores["backend-java"] == 2


def test_matching_is_case_insensitive() -> None:
    assert recommend_template("KOTLIN").scores["backend-java"] == 2


def test_a_term_is_counted_once_per_occurrence() -> None:
    assert recommend_template("Kotlin.").scores["backend-java"] == 2
    assert recommend_template("Kotlin, Kotlin, Kotlin.").scores["backend-java"] == 6


# ─── Term weights ─────────────────────────────────────────────────────────────


def test_a_single_word_term_weighs_two() -> None:
    assert recommend_template("Kotlin.").scores["backend-java"] == 2


def test_a_term_containing_a_space_weighs_three() -> None:
    assert recommend_template("rest api").scores["backend-java"] == 3


def test_a_term_containing_a_dot_weighs_three() -> None:
    assert recommend_template("Next.js").scores["frontend"] == 3


def test_a_term_containing_a_hyphen_weighs_three() -> None:
    # "front-end" is the only hyphenated frontend term; "frontend" must not also match it.
    assert recommend_template("front-end work").scores["frontend"] == 3


# ─── Title boosts ─────────────────────────────────────────────────────────────


def test_a_senior_title_adds_its_boost() -> None:
    recommendation = recommend_template("", "Senior Engineer")
    # 50 from the title boost plus 2 for the "senior" keyword in the combined text
    assert recommendation.scores["senior-engineer"] == 52
    assert recommendation.template_key == "senior-engineer"


def test_a_frontend_title_adds_eighty() -> None:
    recommendation = recommend_template("", "Frontend Engineer")
    assert recommendation.scores["frontend"] == 82
    assert recommendation.template_key == "frontend"


def test_the_boost_applies_to_the_title_only_not_the_body() -> None:
    from_body = recommend_template("We need a senior mindset.", "")
    assert from_body.scores["senior-engineer"] == 2


# ─── Mixed fullstack bonus ────────────────────────────────────────────────────


def test_frontend_and_backend_signals_together_give_fullstack_twenty_five() -> None:
    recommendation = recommend_template("React and Java.")
    assert recommendation.scores == {
        "frontend": 2,
        "backend-java": 2,
        "backend-python": 0,
        "fullstack": 27,
        "senior-engineer": 0,
    }
    assert recommendation.template_key == "fullstack"


def test_a_frontend_signal_alone_earns_no_fullstack_bonus() -> None:
    recommendation = recommend_template("We build React interfaces.")
    assert recommendation.scores["fullstack"] == 2
    assert recommendation.template_key == "frontend"


def test_a_backend_signal_alone_earns_no_fullstack_bonus() -> None:
    recommendation = recommend_template("We build Spring Boot microservices.")
    assert recommendation.scores["fullstack"] == 0


# ─── Tie breaking ─────────────────────────────────────────────────────────────


def test_a_tie_resolves_to_the_earliest_key_in_tie_break_order() -> None:
    recommendation = recommend_template("Kotlin and Django.")
    assert recommendation.scores["backend-java"] == recommendation.scores["backend-python"] == 2
    assert recommendation.template_key == "backend-java"


def test_an_all_zero_score_selects_the_first_key_in_tie_break_order() -> None:
    recommendation = recommend_template("We run a community garden and cook meals for neighbours.")
    assert set(recommendation.scores.values()) == {0}
    assert recommendation.template_key == TIE_BREAK_ORDER[0]


# ─── Reason ───────────────────────────────────────────────────────────────────


def test_reason_names_the_selected_key_and_its_matched_terms() -> None:
    recommendation = recommend_template("Design Java 17 Spring Boot microservices and REST APIs.")
    assert recommendation.template_key == "backend-java"
    assert "backend-java" in recommendation.reason
    assert "java" in recommendation.reason


def test_reason_lists_at_most_eight_matched_terms() -> None:
    jd = (
        "Build React TypeScript SPA interfaces with Redux and Vite, Next.js, Angular, "
        "Storybook, webpack, and frontend UI work."
    )
    recommendation = recommend_template(jd)
    matched = recommendation.matched_terms["frontend"]
    assert len(matched) > 8
    listed = [term for term in matched if term in recommendation.reason]
    assert len(listed) <= 8
    assert all(term in recommendation.reason for term in matched[:8])


def test_reason_says_no_stronger_signal_was_found_when_nothing_matched() -> None:
    recommendation = recommend_template("We run a community garden and cook meals for neighbours.")
    assert recommendation.matched_terms[recommendation.template_key] == []
    assert recommendation.template_key in recommendation.reason
    assert "no stronger role signal was found" in recommendation.reason


# ─── No filesystem template registry ──────────────────────────────────────────


def test_selection_needs_no_template_registry_on_disk() -> None:
    # v1 called storage.template_options(); v2 has no filesystem registry, so the keys are local.
    import resume_pipeline.pipeline.template_select as module

    assert not hasattr(module, "template_options")
