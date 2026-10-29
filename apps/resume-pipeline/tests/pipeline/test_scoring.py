"""Rubric scoring (WP2 §1).

The two `test_*_rubric_weights_sum_to_expected_score` cases are v1's own tests
(`tests/fixtures/v1/test_scoring.py`), ported with only the import path changed. They are the
regression net for the weights, which must not move.
"""

from __future__ import annotations

import dataclasses

import pytest

from resume_pipeline.pipeline.scoring import (
    COVER_LETTER_RUBRIC,
    RESUME_RUBRIC,
    ScoreResult,
    attach_scores,
    score_cover_letter_review,
    score_resume_review,
    weighted_score,
)

# ─── v1 regression tests, import path changed only ────────────────────────────


def test_resume_rubric_weights_sum_to_expected_score() -> None:
    review = {
        "category_scores": {
            "jd_skills_keyword_match": 10,
            "role_domain_relevance": 8,
            "achievement_evidence_strength": 8,
            "credibility_source_truth_compliance": 10,
            "single_page_compliance": 10,
            "targeting_brief_compliance": 9,
            "ats_latex_formatting_safety": 9,
            "recruiter_impression_seniority_alignment": 8,
        }
    }
    result = score_resume_review(review)
    # 10*0.20 + 8*0.15 + 8*0.15 + 10*0.15 + 10*0.15 + 9*0.10 + 9*0.05 + 8*0.05
    # = 2.0 + 1.2 + 1.2 + 1.5 + 1.5 + 0.9 + 0.45 + 0.40 = 9.15
    assert result.score == 9.15
    assert result.missing_categories == []


def test_cover_letter_rubric_weights_sum_to_expected_score() -> None:
    review = {
        "category_scores": {
            "jd_company_alignment": 8,
            "evidence_relevance": 8,
            "motivation_domain_fit": 7,
            "clarity_tone": 9,
            "credibility_no_fabrication": 10,
        }
    }
    result = score_cover_letter_review(review)
    assert result.score == 8.15
    assert result.missing_categories == []


# ─── Rubric shape ─────────────────────────────────────────────────────────────


def test_resume_rubric_has_the_eight_contract_weights() -> None:
    assert RESUME_RUBRIC == {
        "jd_skills_keyword_match": 0.20,
        "role_domain_relevance": 0.15,
        "achievement_evidence_strength": 0.15,
        "credibility_source_truth_compliance": 0.15,
        "single_page_compliance": 0.15,
        "targeting_brief_compliance": 0.10,
        "ats_latex_formatting_safety": 0.05,
        "recruiter_impression_seniority_alignment": 0.05,
    }


def test_cover_letter_rubric_has_the_five_contract_weights() -> None:
    assert COVER_LETTER_RUBRIC == {
        "jd_company_alignment": 0.30,
        "evidence_relevance": 0.25,
        "motivation_domain_fit": 0.20,
        "clarity_tone": 0.15,
        "credibility_no_fabrication": 0.10,
    }


@pytest.mark.parametrize("rubric", [RESUME_RUBRIC, COVER_LETTER_RUBRIC])
def test_rubric_weights_sum_to_one(rubric: dict[str, float]) -> None:
    assert round(sum(rubric.values()), 10) == 1.0


def test_perfect_scores_reach_ten() -> None:
    perfect = dict.fromkeys(RESUME_RUBRIC, 10)
    assert weighted_score(perfect, RESUME_RUBRIC).score == 10.0


# ─── Clamping and unparseable values ──────────────────────────────────────────


def test_value_above_ten_clamps_to_ten() -> None:
    scores = dict.fromkeys(RESUME_RUBRIC, 0)
    scores["jd_skills_keyword_match"] = 99
    # clamped to 10 * 0.20
    assert weighted_score(scores, RESUME_RUBRIC).score == 2.0


def test_negative_value_clamps_to_zero() -> None:
    scores = dict.fromkeys(RESUME_RUBRIC, 0)
    scores["jd_skills_keyword_match"] = -50
    assert weighted_score(scores, RESUME_RUBRIC).score == 0.0


@pytest.mark.parametrize("bad", ["not a number", None, [], {}, "", "ten"])
def test_unparseable_value_clamps_to_zero_without_raising(bad: object) -> None:
    scores: dict[str, object] = dict.fromkeys(RESUME_RUBRIC, 10)
    scores["jd_skills_keyword_match"] = bad
    result = weighted_score(scores, RESUME_RUBRIC)
    # every other category is a perfect 10; the bad one contributes nothing
    assert result.score == 8.0
    assert result.missing_categories == []


def test_numeric_string_is_parsed_not_zeroed() -> None:
    scores: dict[str, object] = dict.fromkeys(RESUME_RUBRIC, 0)
    scores["jd_skills_keyword_match"] = "7.5"
    assert weighted_score(scores, RESUME_RUBRIC).score == 1.5


def test_boundary_values_are_kept() -> None:
    assert weighted_score(dict.fromkeys(RESUME_RUBRIC, 10.0), RESUME_RUBRIC).score == 10.0
    assert weighted_score(dict.fromkeys(RESUME_RUBRIC, 0.0), RESUME_RUBRIC).score == 0.0


# ─── Missing categories ───────────────────────────────────────────────────────


def test_missing_category_contributes_zero_and_is_reported() -> None:
    scores = dict.fromkeys(RESUME_RUBRIC, 10)
    del scores["single_page_compliance"]  # weight 0.15
    result = weighted_score(scores, RESUME_RUBRIC)
    assert result.missing_categories == ["single_page_compliance"]
    assert result.score == 8.5


def test_all_categories_missing_reports_every_rubric_key_in_rubric_order() -> None:
    result = weighted_score({}, RESUME_RUBRIC)
    assert result.score == 0.0
    assert result.missing_categories == list(RESUME_RUBRIC)


def test_extra_categories_are_ignored() -> None:
    scores: dict[str, object] = dict.fromkeys(RESUME_RUBRIC, 10)
    scores["some_category_the_model_invented"] = 10
    result = weighted_score(scores, RESUME_RUBRIC)
    assert result.score == 10.0
    assert result.missing_categories == []


def test_review_without_category_scores_key_scores_zero() -> None:
    result = score_resume_review({})
    assert result.score == 0.0
    assert result.missing_categories == list(RESUME_RUBRIC)

    cover = score_cover_letter_review({})
    assert cover.score == 0.0
    assert cover.missing_categories == list(COVER_LETTER_RUBRIC)


# ─── Rounding and result type ─────────────────────────────────────────────────


def test_score_is_rounded_to_two_decimal_places() -> None:
    scores = dict.fromkeys(RESUME_RUBRIC, 0)
    scores["jd_skills_keyword_match"] = 3.333  # 3.333 * 0.20 = 0.6666
    result = weighted_score(scores, RESUME_RUBRIC)
    assert result.score == 0.67
    assert str(result.score) == "0.67"


def test_score_result_is_a_frozen_dataclass() -> None:
    result = weighted_score({}, RESUME_RUBRIC)
    assert isinstance(result, ScoreResult)
    assert isinstance(result.score, float)
    assert isinstance(result.missing_categories, list)
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.score = 1.0  # type: ignore[misc]


def test_scoring_is_deterministic() -> None:
    review = {"category_scores": {"jd_skills_keyword_match": 7, "clarity_tone": 4}}
    assert score_resume_review(review) == score_resume_review(review)


# ─── attach_scores ────────────────────────────────────────────────────────────


def _payload() -> dict[str, object]:
    return {
        "resume": {"category_scores": dict.fromkeys(RESUME_RUBRIC, 10), "must_fix": ["a"]},
        "cover_letter": {"category_scores": dict.fromkeys(COVER_LETTER_RUBRIC, 8)},
        "notes": "unchanged",
    }


def test_attach_scores_adds_score_and_missing_categories_to_both_blocks() -> None:
    result = attach_scores(_payload())
    assert result["resume"]["score"] == 10.0
    assert result["resume"]["missing_score_categories"] == []
    assert result["cover_letter"]["score"] == 8.0
    assert result["cover_letter"]["missing_score_categories"] == []
    assert result["resume"]["must_fix"] == ["a"]
    assert result["notes"] == "unchanged"


def test_attach_scores_does_not_mutate_its_argument() -> None:
    payload = _payload()
    before = _payload()
    attach_scores(payload)
    assert payload == before
    assert "score" not in payload["resume"]
    assert "missing_score_categories" not in payload["cover_letter"]


def test_attach_scores_returns_a_new_dict() -> None:
    payload = _payload()
    result = attach_scores(payload)
    assert result is not payload
    assert result["resume"] is not payload["resume"]


def test_attach_scores_leaves_absent_keys_alone() -> None:
    result = attach_scores({"resume": {"category_scores": {}}})
    assert "cover_letter" not in result
    assert result["resume"]["score"] == 0.0
    assert result["resume"]["missing_score_categories"] == list(RESUME_RUBRIC)


@pytest.mark.parametrize("value", ["a string", None, 7, ["list"]])
def test_attach_scores_leaves_non_dict_values_alone(value: object) -> None:
    result = attach_scores({"resume": value, "cover_letter": value})
    assert result["resume"] == value
    assert result["cover_letter"] == value


def test_attach_scores_reports_missing_categories_on_a_partial_review() -> None:
    payload = {"resume": {"category_scores": {"jd_skills_keyword_match": 10}}}
    result = attach_scores(payload)
    assert result["resume"]["score"] == 2.0
    assert "single_page_compliance" in result["resume"]["missing_score_categories"]
    assert "jd_skills_keyword_match" not in result["resume"]["missing_score_categories"]


def test_attach_scores_on_empty_payload_returns_empty_dict() -> None:
    assert attach_scores({}) == {}
