from __future__ import annotations

import json
from pathlib import Path

import resume_agent.graph as graph_module
from resume_agent.graph import invoke_graph
from resume_agent.storage import OutputPaths


class FakeOpenAI:
    """Fake generation client (expensive model: resume + cover letter)."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def complete(self, *, system_prompt: str, user_prompt: str, max_tokens: int = 12000) -> str:
        self.calls.append(user_prompt)
        if "pre-approved resume strategy" in user_prompt or "Generate a tailored LaTeX resume" in user_prompt:
            return "\\documentclass{article}\\begin{document}RESUME V1\\end{document}"
        # Cover letter (called once initially, once after revision)
        return "\\documentclass{letter}\\begin{document}CL V1\\end{document}"


class FakeRevisionClient:
    """Fake cheap revision client — returns a slightly revised resume."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def complete(self, *, system_prompt: str, user_prompt: str, max_tokens: int = 12000) -> str:
        self.calls.append(user_prompt)
        return "\\documentclass{article}\\begin{document}RESUME V2 REVISED\\end{document}"


class FakeClaude:
    """Fake Claude client — targeting brief, then failing review, then passing review."""

    def __init__(self) -> None:
        self.calls = 0

    def complete(self, *, system_prompt: str, user_prompt: str, max_tokens: int = 6000) -> str:
        self.calls += 1
        # Call 1: targeting brief
        if self.calls == 1:
            return json.dumps({
                "role_level": "mid",
                "tone": "collaborative",
                "grounded_keywords": ["Java", "APIs"],
                "forbidden_claims": [],
                "seniority_verbs_to_avoid": ["led"],
                "seniority_verbs_to_use": ["contributed"],
                "evidence_map": {},
                "keyword_strategy": {},
                "ats_strategy": "",
                "cover_letter_angle": "Test angle.",
            })
        # Call 2: first resume review — fails so revision is triggered
        if self.calls == 2:
            return json.dumps({
                "resume": {
                    "category_scores": {
                        "jd_skills_keyword_match": 7,
                        "role_domain_relevance": 7,
                        "achievement_evidence_strength": 7,
                        "credibility_source_truth_compliance": 7,
                        "ats_latex_formatting_safety": 7,
                        "recruiter_impression_seniority_alignment": 7,
                        "targeting_brief_compliance": 7,
                        "single_page_compliance": 7,
                    },
                    "verdict": "fail",
                    "must_fix": ["Improve keyword alignment."],
                    "fix_resolution": [],
                    "issues": [{"severity": "must_fix", "description": "Improve keyword alignment."}],
                }
            })
        # Call 3+: second review after revision — resume now passes
        return json.dumps({
            "resume": {
                "category_scores": {
                    "jd_skills_keyword_match": 9,
                    "role_domain_relevance": 9,
                    "achievement_evidence_strength": 9,
                    "credibility_source_truth_compliance": 9,
                    "ats_latex_formatting_safety": 9,
                    "recruiter_impression_seniority_alignment": 9,
                    "targeting_brief_compliance": 9,
                    "single_page_compliance": 9,
                },
                "verdict": "pass",
                "must_fix": [],
                "fix_resolution": [{"item": "Improve keyword alignment.", "status": "fixed", "evidence": "keywords added"}],
                "issues": [],
            }
        })


def test_graph_revises_failing_resume(monkeypatch, tmp_path) -> None:
    """Graph should revise resume when score is below threshold, then re-generate cover letter."""
    paths = OutputPaths(
        output_dir=tmp_path,
        pdf_dir=tmp_path / "PDF",
        jd_path=tmp_path / "JD.txt",
        resume_tex_path=tmp_path / "hamsa_resume.tex",
        cover_letter_tex_path=tmp_path / "cover_letter.tex",
        review_json_path=tmp_path / "review.json",
        resume_pdf_path=tmp_path / "PDF" / "hamsa_resume.pdf",
        cover_letter_pdf_path=tmp_path / "PDF" / "cover_letter.pdf",
    )
    monkeypatch.setattr(graph_module, "prepare_output_paths", lambda *_args, **_kwargs: paths)

    from langgraph.checkpoint.memory import MemorySaver

    long_jd = "Java React APIs cloud healthcare " * 80
    fake_openai = FakeOpenAI()
    fake_revision = FakeRevisionClient()
    fake_claude = FakeClaude()

    result = invoke_graph(
        {
            "company_name": "Test Company",
            "job_title": "Fullstack Engineer",
            "jd_source_type": "text",
            "jd_text": long_jd,
            "selected_template": "fullstack",
            "compile_pdf_requested": False,
        },
        openai_client=fake_openai,
        revision_client=fake_revision,
        claude_client=fake_claude,
        checkpointer=MemorySaver(),
    )

    # Resume should be the revised version
    assert "RESUME V2 REVISED" in result["final_resume_tex"]
    # Cover letter should be present (generated once at end, after all revisions)
    assert result["final_cover_letter_tex"]
    # Resume score should pass after revision
    assert result["resume_score"] >= 8.0
    # Exactly one revision was made
    assert result["revision_call_count"] == 1
    # Total LLM calls: brief(1) + resume(2) + review-fail(3) + revise(4) + review-pass(5) + cover(6)
    # Cover letter is now generated once at end, not after each revision
    assert result["total_llm_call_count"] == 6
    assert Path(result["resume_tex_path"]).exists()
