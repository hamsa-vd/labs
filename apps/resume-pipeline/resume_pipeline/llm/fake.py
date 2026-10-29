"""The offline fake client (RG-008).

`LLM_MODE=fake` is the default everywhere except a deliberate live run, so this class is what
makes the whole pipeline testable: a full generation with its revision loop runs in under two
seconds, offline, for nothing. A test that reaches a provider is a bug.

The fake is only useful if the graph can parse what it returns, so every stage produces
schema-valid output:

* `targeting` and `review` return strict JSON that `parse_strict_json_object` accepts. The review
  payload carries all eight `RESUME_RUBRIC` categories, because `attach_scores` silently weights a
  missing category as zero — a fake that returned six categories would make every run look bad.
* `generation`, `revision` and `cover_letter` return a complete LaTeX document with
  `\\documentclass`, `\\begin{document}` and `\\end{document}`.

Determinism beats realism: the same prompt always yields the same output, so a test can assert on
it. Response resolution goes `stage_responses` → fixture file → generic stage response.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from resume_pipeline.llm.base import Completion
from resume_pipeline.pipeline.scoring import RESUME_RUBRIC

#: A pass on the first review, so a default fake run finishes without a revision cycle.
#: `RESUME_PASS_SCORE` is 8.0; this sits above it.
DEFAULT_REVIEW_SCORE: float = 8.6

#: Every stage the fake knows how to answer. Anything else falls back to `generation`.
KNOWN_STAGES: tuple[str, ...] = (
    "targeting",
    "generation",
    "review",
    "revision",
    "cover_letter",
    "ats",
)

#: Ordered marker sets for inferring a stage when the caller did not say. Every marker is static
#: prose from the seed prompt bodies, never a `{{PLACEHOLDER}}` name — by the time a prompt reaches
#: a client the placeholders are gone and their rendered values are in their place.
#:
#: The order is the whole trick, because a rendered prompt carries other stages' vocabulary inside
#: its substituted values: a review prompt embeds the targeting brief, and a revision prompt embeds
#: the review's category scores. Each stage is therefore tested before any stage whose text it
#: might contain.
_STAGE_MARKERS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "revision",
        (
            "surgical, measurable fixes",
            "complete revised resume latex",
            "score context",
        ),
    ),
    (
        "review",
        (
            "review the resume against the jd",
            "brutal_recruiter_opinion",
            "must-fix generation is mandatory",
            "category_scores",
        ),
    ),
    (
        "cover_letter",
        ("latex cover letter",),
    ),
    (
        "generation",
        (
            "pre-approved resume strategy",
            "selected base resume latex",
        ),
    ),
    (
        "targeting",
        (
            "senior technical recruiter and resume strategist",
            "targeting brief that will guide",
            "role_level_rationale",
            "learning_signal_keywords",
        ),
    ),
    (
        "ats",
        (
            "ats_findings",
            "ats findings",
        ),
    ),
)


def infer_stage(system_prompt: str, user_prompt: str) -> str:
    """Guess the stage from prompt markers, falling back to `generation`.

    Inference exists for callers that have not been updated; the rule the contract sets is that
    the caller passes `stage` explicitly and this is the safety net.
    """
    haystack = f"{system_prompt}\n{user_prompt}".lower()
    for stage, markers in _STAGE_MARKERS:
        if any(marker in haystack for marker in markers):
            return stage
    return "generation"


class FakeLLMClient:
    """An `LLMClient` that never opens a socket and never reads a key."""

    def __init__(
        self,
        *,
        stage_responses: Mapping[str, str] | None = None,
        fixtures_dir: Path | None = None,
        provider: str = "fake",
        model: str = "fake-model",
        score_sequence: Sequence[float] | None = None,
    ) -> None:
        self.provider = provider
        self.model = model
        self.stage_responses: dict[str, str] = dict(stage_responses or {})
        self.fixtures_dir = fixtures_dir
        self.score_sequence: list[float] = [float(s) for s in (score_sequence or [])]
        self.calls: list[dict[str, Any]] = []
        self._review_calls = 0

    async def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 6000,
        stage: str | None = None,
    ) -> Completion:
        resolved = stage if stage else infer_stage(system_prompt, user_prompt)
        self.calls.append(
            {
                "stage": resolved,
                "system": system_prompt,
                "user": user_prompt,
                "at": datetime.now(tz=UTC),
            }
        )
        text = self._response_for(resolved, user_prompt)
        return Completion(
            text=text,
            input_tokens=_token_estimate(system_prompt) + _token_estimate(user_prompt),
            output_tokens=_token_estimate(text),
            model=self.model,
        )

    # ─── Response resolution ──────────────────────────────────────────────────

    def _response_for(self, stage: str, user_prompt: str) -> str:
        explicit = self.stage_responses.get(stage)
        if explicit is not None:
            return explicit
        fixture = self._fixture_for(stage, user_prompt)
        if fixture is not None:
            return fixture
        return self._generic_for(stage)

    def _fixture_for(self, stage: str, user_prompt: str) -> str | None:
        if self.fixtures_dir is None:
            return None
        path = Path(self.fixtures_dir) / stage / f"{fixture_key(user_prompt)}.json"
        if not path.is_file():
            return None
        raw = path.read_text(encoding="utf-8")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return raw
        if isinstance(parsed, str):
            return parsed
        if isinstance(parsed, dict) and isinstance(parsed.get("text"), str):
            # A fixture for a LaTeX stage cannot be a bare JSON object, so `{"text": "..."}` is the
            # way to write one.
            return str(parsed["text"])
        return json.dumps(parsed, indent=2, sort_keys=True)

    def _generic_for(self, stage: str) -> str:
        if stage == "targeting":
            return json.dumps(targeting_payload(), indent=2, sort_keys=True)
        if stage == "review":
            score = self._next_review_score()
            return json.dumps(review_payload(score), indent=2, sort_keys=True)
        if stage == "ats":
            return json.dumps(ats_payload(), indent=2, sort_keys=True)
        if stage == "cover_letter":
            return COVER_LETTER_TEX
        if stage == "revision":
            return REVISION_TEX
        return GENERATION_TEX

    def _next_review_score(self) -> float:
        """Walk `score_sequence`, holding on its last value once it runs out.

        Holding rather than wrapping is what lets `[6.5, 8.6]` mean "fail once, then pass and stay
        passed" — a wrapping sequence would drive the loop until the revision budget stopped it.
        """
        index = self._review_calls
        self._review_calls += 1
        if not self.score_sequence:
            return DEFAULT_REVIEW_SCORE
        return self.score_sequence[min(index, len(self.score_sequence) - 1)]


def fixture_key(user_prompt: str) -> str:
    """The fixture filename stem for a prompt: the first 16 hex characters of its SHA-256."""
    return hashlib.sha256(user_prompt.encode("utf-8")).hexdigest()[:16]


def _token_estimate(text: str) -> int:
    """A stable stand-in for a tokeniser, so telemetry has something non-zero to record."""
    return max(1, len(text) // 4)


# ─── Generic payloads ─────────────────────────────────────────────────────────


def targeting_payload() -> dict[str, Any]:
    """A complete targeting brief, matching the seed prompt's schema."""
    return {
        "role_level": "senior",
        "role_level_rationale": "The job description asks for ownership of a platform and mentoring.",
        "tone": "ownership-heavy",
        "positioning_statement": (
            "Position the candidate as a backend engineer who owns event-driven platforms end to end."
        ),
        "grounded_keywords": ["Python", "PostgreSQL", "Kafka", "AWS"],
        "learning_signal_keywords": ["Terraform"],
        "forbidden_claims": ["Team leadership of more than ten engineers"],
        "seniority_verbs_to_avoid": ["Founded"],
        "seniority_verbs_to_use": ["Owned", "Designed", "Led"],
        "evidence_map": [
            {
                "jd_requirement": "Build event-driven pipelines",
                "candidate_evidence": "Architected a Kafka event pipeline across twelve services.",
                "strategy": "Lead the most recent role with the pipeline bullet.",
            }
        ],
        "keyword_strategy": [
            {"keyword": "Kafka", "has_evidence": True, "approach": "use confidently"},
            {"keyword": "Terraform", "has_evidence": True, "approach": "use adjacent evidence"},
        ],
        "ats_strategy": "Lead with the platform keywords the job description repeats.",
        "cover_letter_angle": (
            "Connect the settlement platform work to the role's ownership of order settlement."
        ),
    }


def review_payload(score: float) -> dict[str, Any]:
    """A review payload scoring every rubric category at `score`.

    Every category carries the same value on purpose: `RESUME_RUBRIC`'s weights sum to 1.0, so the
    weighted score `attach_scores` produces is exactly `score`. That is what makes
    `score_sequence=[6.5, 8.6]` mean what a test expects it to mean.
    """
    bounded = max(0.0, min(10.0, float(score)))
    passed = bounded >= 8.0
    must_fix = (
        []
        if passed
        else [
            "jd_skills_keyword_match: add Terraform to the skills line, it is grounded in the "
            "source of truth and absent from the resume."
        ]
    )
    return {
        "resume": {
            "category_scores": dict.fromkeys(RESUME_RUBRIC, bounded),
            "verdict": "pass" if passed else "fail",
            "brutal_recruiter_opinion": (
                "The resume reads as a credible platform engineer for this job description."
                if passed
                else "The resume is close but under-uses the job description's platform keywords."
            ),
            "must_fix": must_fix,
            "nice_to_have": ["Tighten the summary to two lines."],
            "ats_risks": [],
            "missing_keywords": [] if passed else ["Terraform"],
            "credibility_risks": [],
            "fix_resolution": [
                {
                    "must_fix_item": "jd_skills_keyword_match: add Terraform to the skills line.",
                    "status": "fixed" if passed else "not_fixed",
                    "evidence": (
                        "Terraform now appears in the skills line."
                        if passed
                        else "Terraform is still absent from the skills line."
                    ),
                }
            ],
        }
    }


def ats_payload() -> dict[str, Any]:
    """A minimal ATS commentary payload. The ATS score itself is computed, never modelled."""
    return {
        "summary": "The resume covers the job description's core platform keywords.",
        "top_actions": ["Add Terraform to the skills line."],
        "unmet_hard_requirements": [],
    }


# ─── Generic LaTeX ────────────────────────────────────────────────────────────


def _document(title: str, body: str) -> str:
    return (
        "\\documentclass[letterpaper,11pt]{article}\n"
        "\\usepackage[margin=0.5in]{geometry}\n"
        "\\pagestyle{empty}\n"
        "\\begin{document}\n"
        f"\\textbf{{{title}}}\n"
        "\n"
        f"{body}\n"
        "\\end{document}\n"
    )


GENERATION_TEX: str = _document(
    "Hamsa Vardhan",
    "Senior backend engineer with six years of experience building Python and Java services\n"
    "on AWS, with deep ownership of authentication, search, and observability.\n"
    "\n"
    "\\textbf{EXPERIENCE}\n"
    "\n"
    "\\begin{itemize}\n"
    "  \\item Architected a Kafka event pipeline that cut settlement latency by 45 percent.\n"
    "  \\item Migrated search to AWS OpenSearch, reducing p95 latency from 2.5s to 250ms.\n"
    "\\end{itemize}\n",
)

REVISION_TEX: str = _document(
    "Hamsa Vardhan",
    "Senior backend engineer with six years of experience building Python and Java services\n"
    "on AWS, with deep ownership of authentication, search, observability, and Terraform.\n"
    "\n"
    "\\textbf{EXPERIENCE}\n"
    "\n"
    "\\begin{itemize}\n"
    "  \\item Architected a Kafka event pipeline that cut settlement latency by 45 percent.\n"
    "  \\item Migrated search to AWS OpenSearch, reducing p95 latency from 2.5s to 250ms.\n"
    "  \\item Automated infrastructure with Terraform and Docker across twelve services.\n"
    "\\end{itemize}\n",
)

COVER_LETTER_TEX: str = _document(
    "Hamsa Vardhan",
    "Dear hiring team,\n"
    "\n"
    "Your order settlement platform is the problem I have spent the last three years on.\n"
    "At Liv-ex I architected the Kafka pipeline that cut settlement latency by 45 percent\n"
    "across twelve services, and I would like to do that work for you.\n"
    "\n"
    "Yours sincerely,\n"
    "\n"
    "Hamsa Vardhan\n",
)
