"""Run budgets and thresholds (RG-030, RG-031).

Replaces v1's `resume_agent/config.py` constants. The filesystem paths v1 kept here are gone —
v2 reads nothing from disk.

`COVER_LETTER_PASS_SCORE` is new. v1's `build_persist_warnings` referenced the name without ever
defining or importing it, so the cover-letter warning branch raised `NameError` the moment it was
reached. RG-030 fixes it by defining the constant here, mirroring the resume threshold.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

MIN_JD_TEXT_LENGTH: int = 300
ATS_PASS_THRESHOLD: int = 80
RESUME_PASS_SCORE: float = 8.0
COVER_LETTER_PASS_SCORE: float = 8.0
MAX_REVISIONS: int = 1
MAX_TOTAL_LLM_CALLS: int = 16
MAX_OPENAI_CALLS: int = 4
MAX_CLAUDE_CALLS: int = 8
MAX_REVISION_CALLS: int = 5
RECURSION_LIMIT: int = 25


@dataclass(frozen=True)
class RunBudget:
    max_revisions: int = MAX_REVISIONS
    resume_pass_score: float = RESUME_PASS_SCORE
    ats_pass_threshold: int = ATS_PASS_THRESHOLD
    max_total_llm_calls: int = MAX_TOTAL_LLM_CALLS
    max_openai_calls: int = MAX_OPENAI_CALLS
    max_claude_calls: int = MAX_CLAUDE_CALLS
    max_revision_calls: int = MAX_REVISION_CALLS


#: Hard server-side ceilings from RG-031. A user setting above a ceiling is clamped down to it;
#: it is never honoured.
SERVER_CEILINGS: dict[str, int | float] = {
    "max_revisions": 5,
    "max_total_llm_calls": 30,
    "max_openai_calls": 10,
    "max_claude_calls": 16,
    "max_revision_calls": 10,
    "resume_pass_score": 9.5,
    "ats_pass_threshold": 95,
}

#: Field defaults, keyed the same way as `SERVER_CEILINGS`.
_DEFAULTS: dict[str, int | float] = {
    "max_revisions": MAX_REVISIONS,
    "max_total_llm_calls": MAX_TOTAL_LLM_CALLS,
    "max_openai_calls": MAX_OPENAI_CALLS,
    "max_claude_calls": MAX_CLAUDE_CALLS,
    "max_revision_calls": MAX_REVISION_CALLS,
    "resume_pass_score": RESUME_PASS_SCORE,
    "ats_pass_threshold": ATS_PASS_THRESHOLD,
}

#: Score-valued fields floor at 0.0; count-valued fields floor at 1.
_FLOAT_FIELDS: frozenset[str] = frozenset({"resume_pass_score"})


def clamp_budget(requested: Mapping[str, Any]) -> RunBudget:
    """Turn a partial mapping of user settings into a `RunBudget` that respects the ceilings.

    An absent key takes the default. A present key is clamped into the allowed range. A value
    that cannot be read as a number falls back to the default rather than raising.
    """
    values: dict[str, Any] = {}
    for field_name, default in _DEFAULTS.items():
        values[field_name] = _clamp_field(field_name, requested.get(field_name, None), default)
    return RunBudget(
        max_revisions=int(values["max_revisions"]),
        resume_pass_score=float(values["resume_pass_score"]),
        ats_pass_threshold=int(values["ats_pass_threshold"]),
        max_total_llm_calls=int(values["max_total_llm_calls"]),
        max_openai_calls=int(values["max_openai_calls"]),
        max_claude_calls=int(values["max_claude_calls"]),
        max_revision_calls=int(values["max_revision_calls"]),
    )


def _clamp_field(field_name: str, value: Any, default: int | float) -> int | float:
    if value is None:
        return default
    is_float = field_name in _FLOAT_FIELDS
    numeric = _coerce_float(value)
    if numeric is None:
        return default
    minimum: float = 0.0 if is_float else 1.0
    ceiling = float(SERVER_CEILINGS[field_name])
    bounded = max(minimum, min(ceiling, numeric))
    return bounded if is_float else int(bounded)


def _coerce_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if numeric != numeric:  # NaN has no place in an ordering, so treat it as unparseable.
        return None
    return numeric
