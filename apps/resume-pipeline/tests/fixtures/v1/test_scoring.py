from __future__ import annotations

from resume_agent.scoring import score_cover_letter_review, score_resume_review


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
