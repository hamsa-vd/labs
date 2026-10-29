"""ATS service wrapper (WP2 §8).

`check` is the one place a run touches the ATS scorer, and a run must survive a bad ATS check:
it never raises. The fault-injection tests below break the vendored scorer on purpose (never
the module under test) to prove the failure comes back as data.
"""

from __future__ import annotations

import json

import pytest

from resume_pipeline.ats import scorer as vendored_scorer
from resume_pipeline.services.ats_service import check

EXPECTED_KEYS = {
    "ats_total_score",
    "ats_grade",
    "ats_keyword_score",
    "ats_structural_score",
    "ats_semantic_score",
    "ats_matched",
    "ats_missing_required",
    "ats_missing_preferred",
    "ats_missing_nice_to_have",
    "ats_top_actions",
    "ats_hard_requirements",
    "ats_all_hard_met",
    "ats_error",
}

SCORE_KEYS = (
    "ats_total_score",
    "ats_grade",
    "ats_keyword_score",
    "ats_structural_score",
    "ats_semantic_score",
)

LIST_KEYS = (
    "ats_matched",
    "ats_missing_required",
    "ats_missing_preferred",
    "ats_missing_nice_to_have",
    "ats_top_actions",
    "ats_hard_requirements",
)


# ─── Shape ────────────────────────────────────────────────────────────────────


def test_result_has_exactly_the_contract_keys(plain_resume: str, sample_jd: str) -> None:
    assert set(check(plain_resume, sample_jd)) == EXPECTED_KEYS


def test_result_is_json_serialisable(plain_resume: str, sample_jd: str) -> None:
    # persist_outputs writes this dict straight out; it must contain no dataclasses.
    assert json.loads(json.dumps(check(plain_resume, sample_jd)))


def test_a_successful_check_reports_no_error(plain_resume: str, sample_jd: str) -> None:
    assert check(plain_resume, sample_jd)["ats_error"] is None


def test_score_types_and_ranges(plain_resume: str, sample_jd: str) -> None:
    result = check(plain_resume, sample_jd)
    assert isinstance(result["ats_total_score"], float)
    assert 0.0 <= result["ats_total_score"] <= 100.0
    assert 0.0 <= result["ats_keyword_score"] <= 50.0
    assert 0.0 <= result["ats_structural_score"] <= 30.0
    assert 0.0 <= result["ats_semantic_score"] <= 20.0


def test_grade_is_one_of_the_four_bands(plain_resume: str, sample_jd: str) -> None:
    assert check(plain_resume, sample_jd)["ats_grade"] in {"Excellent", "Good", "Fair", "Poor"}


def test_list_keys_hold_lists(plain_resume: str, sample_jd: str) -> None:
    result = check(plain_resume, sample_jd)
    for key in LIST_KEYS:
        assert isinstance(result[key], list)
    for key in ("ats_matched", "ats_missing_required", "ats_top_actions"):
        assert all(isinstance(item, str) for item in result[key])


def test_hard_requirements_entries_have_the_contract_fields(plain_resume: str, sample_jd: str) -> None:
    result = check(plain_resume, sample_jd)
    assert result["ats_hard_requirements"], "this JD states a years and a degree requirement"
    for requirement in result["ats_hard_requirements"]:
        assert set(requirement) == {"kind", "description", "required_value", "met", "confidence"}
        assert isinstance(requirement["kind"], str)
        assert isinstance(requirement["description"], str)
        assert isinstance(requirement["met"], bool)
        assert isinstance(requirement["confidence"], float)


def test_all_hard_met_agrees_with_the_individual_requirements(plain_resume: str, sample_jd: str) -> None:
    result = check(plain_resume, sample_jd)
    assert isinstance(result["ats_all_hard_met"], bool)
    assert result["ats_all_hard_met"] == all(req["met"] for req in result["ats_hard_requirements"])


def test_a_matching_resume_scores_and_matches_jd_keywords(plain_resume: str, sample_jd: str) -> None:
    result = check(plain_resume, sample_jd)
    matched = {term.lower() for term in result["ats_matched"]}
    assert result["ats_total_score"] > 0
    assert any("python" in term for term in matched)
    assert any("kafka" in term for term in matched)


# ─── Determinism ──────────────────────────────────────────────────────────────


def test_identical_input_gives_an_identical_result(plain_resume: str, sample_jd: str) -> None:
    assert check(plain_resume, sample_jd) == check(plain_resume, sample_jd)


def test_identical_input_gives_an_identical_result_for_latex(tex_resume: str, sample_jd: str) -> None:
    assert check(tex_resume, sample_jd) == check(tex_resume, sample_jd)


# ─── Acceptance criterion 5: LaTeX and plain text score alike ─────────────────


def test_a_tex_resume_and_its_plain_text_equivalent_score_within_two_points(
    tex_resume: str, plain_resume: str, sample_jd: str
) -> None:
    from_tex = check(tex_resume, sample_jd)
    from_plain = check(plain_resume, sample_jd)
    assert from_tex["ats_error"] is None
    assert from_plain["ats_error"] is None
    assert abs(from_tex["ats_total_score"] - from_plain["ats_total_score"]) <= 2.0


def test_latex_markup_never_reaches_the_scorer(tex_resume: str, plain_resume: str, sample_jd: str) -> None:
    from_tex = check(tex_resume, sample_jd)
    from_plain = check(plain_resume, sample_jd)
    assert set(from_tex["ats_matched"]) == set(from_plain["ats_matched"])
    assert set(from_tex["ats_missing_required"]) == set(from_plain["ats_missing_required"])


# ─── Empty input is a missing measurement, not a zero score ───────────────────


@pytest.mark.parametrize("resume", ["", "   ", "\n\n\t\n"])
def test_an_empty_resume_returns_an_error_not_a_zero_score(resume: str, sample_jd: str) -> None:
    result = check(resume, sample_jd)
    assert isinstance(result["ats_error"], str)
    assert result["ats_error"]
    assert result["ats_total_score"] is None


@pytest.mark.parametrize("jd", ["", "   ", "Backend Engineer"])
def test_an_empty_or_unusable_jd_returns_an_error_not_a_zero_score(plain_resume: str, jd: str) -> None:
    result = check(plain_resume, jd)
    assert isinstance(result["ats_error"], str)
    assert result["ats_error"]
    assert result["ats_total_score"] is None


# ─── It never raises ──────────────────────────────────────────────────────────


def _error_shape(result: dict[str, object]) -> None:
    assert set(result) == EXPECTED_KEYS
    assert isinstance(result["ats_error"], str)
    assert result["ats_error"]
    for key in SCORE_KEYS:
        assert result[key] is None
    for key in LIST_KEYS:
        assert result[key] == []
    assert result["ats_all_hard_met"] is False


def test_a_scorer_that_raises_comes_back_as_an_error_result(
    monkeypatch: pytest.MonkeyPatch, plain_resume: str, sample_jd: str
) -> None:
    def explode(*args: object, **kwargs: object) -> str:
        raise RuntimeError("scorer blew up")

    monkeypatch.setattr(vendored_scorer, "parse_resume", explode)
    _error_shape(check(plain_resume, sample_jd))


def test_a_scorer_that_raises_a_value_error_comes_back_as_an_error_result(
    monkeypatch: pytest.MonkeyPatch, plain_resume: str, sample_jd: str
) -> None:
    def explode(*args: object, **kwargs: object) -> str:
        raise ValueError("no recognisable keywords could be extracted")

    monkeypatch.setattr(vendored_scorer, "extract_keywords", explode)
    _error_shape(check(plain_resume, sample_jd))


def test_a_type_error_from_the_scorer_is_caught(
    monkeypatch: pytest.MonkeyPatch, plain_resume: str, sample_jd: str
) -> None:
    def explode(*args: object, **kwargs: object) -> str:
        raise TypeError("unexpected argument")

    monkeypatch.setattr(vendored_scorer, "check_hard_requirements", explode)
    result = check(plain_resume, sample_jd)
    assert isinstance(result, dict)
    assert isinstance(result["ats_error"], str)


def test_the_error_message_leaks_no_resume_or_jd_content(
    monkeypatch: pytest.MonkeyPatch, plain_resume: str, sample_jd: str
) -> None:
    def explode(*args: object, **kwargs: object) -> str:
        raise RuntimeError(f"failed while scoring: {plain_resume}")

    monkeypatch.setattr(vendored_scorer, "parse_resume", explode)
    message = check(plain_resume, sample_jd)["ats_error"]
    assert isinstance(message, str)
    assert "Architected a Kafka event pipeline" not in message
    assert "order settlement platform" not in message


def test_the_total_score_is_never_above_one_hundred(
    monkeypatch: pytest.MonkeyPatch, plain_resume: str, sample_jd: str
) -> None:
    def inflated(*args: object, **kwargs: object) -> vendored_scorer.SemanticResult:
        return vendored_scorer.SemanticResult(score=5000.0)

    monkeypatch.setattr(vendored_scorer, "_score_semantic", inflated)
    result = check(plain_resume, sample_jd)
    if result["ats_error"] is None:
        assert result["ats_total_score"] <= 100.0


def test_the_service_makes_no_network_call(plain_resume: str, sample_jd: str) -> None:
    # The suite-wide socket guard in tests/conftest.py fails the test if it tries.
    assert check(plain_resume, sample_jd)["ats_error"] is None
