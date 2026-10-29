"""ATS scoring service.

Wraps the vendored `resume_pipeline.ats` scorer. Ports the contract of v1's
`resume_agent/ats_client.py`: the key names below are what `persist_outputs` writes and what the
result view reads.

`check` never raises. An ATS check is a measurement, not a gate, and a run has to survive a bad
one — every failure path returns the same dict shape with `ats_error` set and no score.
"""

from __future__ import annotations

import logging
from typing import Any

from resume_pipeline.pipeline.latex_text import tex_to_text

logger = logging.getLogger(__name__)


def check(resume_text: str, jd_text: str) -> dict[str, Any]:
    """Score `resume_text` against `jd_text`.

    `resume_text` may be LaTeX or plain text; it is reduced to prose first because the scorer
    expects prose. Given identical inputs the result is identical: no clock, no network, no
    randomness.
    """
    try:
        prose = tex_to_text(resume_text or "")
        if not prose.strip():
            return _failed("The resume is empty, so it could not be scored. Add resume content and retry.")
        if not (jd_text or "").strip():
            return _failed(
                "The job description is empty, so the resume could not be scored. "
                "Add the job description and retry."
            )

        from resume_pipeline.ats.scorer import score

        result = score(prose, jd_text)
        hard_reqs = [
            {
                "kind": r.kind,
                "description": r.description,
                "required_value": r.required_value,
                "met": r.met,
                "confidence": r.confidence,
            }
            for r in result.hard_requirements.requirements
        ]
        return {
            "ats_total_score": max(0.0, min(100.0, float(result.total_score))),
            "ats_grade": result.grade,
            "ats_keyword_score": result.keyword.score,
            "ats_structural_score": result.structural.score,
            "ats_semantic_score": result.semantic.score,
            "ats_matched": list(result.keyword.matched),
            "ats_missing_required": list(result.keyword.missing_required),
            "ats_missing_preferred": list(result.keyword.missing_preferred),
            "ats_missing_nice_to_have": list(result.keyword.missing_nice_to_have),
            "ats_top_actions": list(result.top_actions),
            "ats_hard_requirements": hard_reqs,
            "ats_all_hard_met": bool(result.hard_requirements.all_met),
            "ats_error": None,
        }
    except Exception as exc:  # noqa: BLE001 — a failed ATS check must not end the run.
        # The exception's own message is discarded rather than returned. A scorer
        # failure often quotes the input it choked on, and `ats_error` is persisted
        # on the run and rendered in the result view — so `str(exc)` is a path for a
        # resume body or a job description to reach a stored, displayed field.
        # The type alone is enough to diagnose; the body is not ours to publish.
        logger.warning("ATS check failed: %s", type(exc).__name__)
        return _failed(f"Scoring failed ({type(exc).__name__}). The rest of the run continued.")


def _failed(message: str) -> dict[str, Any]:
    return {
        "ats_total_score": None,
        "ats_grade": None,
        "ats_keyword_score": None,
        "ats_structural_score": None,
        "ats_semantic_score": None,
        "ats_matched": [],
        "ats_missing_required": [],
        "ats_missing_preferred": [],
        "ats_missing_nice_to_have": [],
        "ats_top_actions": [],
        "ats_hard_requirements": [],
        "ats_all_hard_met": False,
        "ats_error": message,
    }
