"""Budget constants and server-side clamping (WP2 §2).

The constants replace v1's `resume_agent/config.py`; the numbers must not drift. The package
purity check for acceptance criterion 6 lives here too, because budgets.py is the module that
replaced the one file in v1 that did touch the filesystem.
"""

from __future__ import annotations

import dataclasses
import json
import subprocess
import sys
from typing import Any

import pytest

from resume_pipeline.pipeline.budgets import (
    ATS_PASS_THRESHOLD,
    COVER_LETTER_PASS_SCORE,
    MAX_CLAUDE_CALLS,
    MAX_OPENAI_CALLS,
    MAX_REVISION_CALLS,
    MAX_REVISIONS,
    MAX_TOTAL_LLM_CALLS,
    MIN_JD_TEXT_LENGTH,
    RECURSION_LIMIT,
    RESUME_PASS_SCORE,
    SERVER_CEILINGS,
    RunBudget,
    clamp_budget,
)

# ─── Constants ────────────────────────────────────────────────────────────────


def test_constants_match_the_contract() -> None:
    assert MIN_JD_TEXT_LENGTH == 300
    assert ATS_PASS_THRESHOLD == 80
    assert RESUME_PASS_SCORE == 8.0
    assert COVER_LETTER_PASS_SCORE == 8.0
    assert MAX_REVISIONS == 1
    assert MAX_TOTAL_LLM_CALLS == 16
    assert MAX_OPENAI_CALLS == 4
    assert MAX_CLAUDE_CALLS == 8
    assert MAX_REVISION_CALLS == 5
    assert RECURSION_LIMIT == 25


def test_pass_scores_are_floats_and_counts_are_ints() -> None:
    assert isinstance(RESUME_PASS_SCORE, float)
    assert isinstance(COVER_LETTER_PASS_SCORE, float)
    for value in (MIN_JD_TEXT_LENGTH, ATS_PASS_THRESHOLD, MAX_REVISIONS, MAX_TOTAL_LLM_CALLS):
        assert isinstance(value, int)


def test_cover_letter_pass_score_exists_so_the_warning_branch_cannot_raise() -> None:
    # RG-030: v1's build_persist_warnings referenced this name without defining it.
    assert COVER_LETTER_PASS_SCORE == RESUME_PASS_SCORE


def test_server_ceilings_match_rg031() -> None:
    assert SERVER_CEILINGS["max_revisions"] == 5
    assert SERVER_CEILINGS["max_total_llm_calls"] == 30
    assert SERVER_CEILINGS["max_openai_calls"] == 10
    assert SERVER_CEILINGS["max_claude_calls"] == 16
    assert SERVER_CEILINGS["max_revision_calls"] == 10
    assert SERVER_CEILINGS["resume_pass_score"] == 9.5
    assert SERVER_CEILINGS["ats_pass_threshold"] == 95


def test_every_default_is_at_or_below_its_ceiling() -> None:
    budget = RunBudget()
    for field, ceiling in SERVER_CEILINGS.items():
        assert getattr(budget, field) <= ceiling


# ─── RunBudget ────────────────────────────────────────────────────────────────


def test_run_budget_defaults_come_from_the_module_constants() -> None:
    budget = RunBudget()
    assert budget.max_revisions == MAX_REVISIONS
    assert budget.resume_pass_score == RESUME_PASS_SCORE
    assert budget.ats_pass_threshold == ATS_PASS_THRESHOLD
    assert budget.max_total_llm_calls == MAX_TOTAL_LLM_CALLS
    assert budget.max_openai_calls == MAX_OPENAI_CALLS
    assert budget.max_claude_calls == MAX_CLAUDE_CALLS
    assert budget.max_revision_calls == MAX_REVISION_CALLS


def test_run_budget_is_frozen() -> None:
    budget = RunBudget()
    assert dataclasses.is_dataclass(budget)
    with pytest.raises(dataclasses.FrozenInstanceError):
        budget.max_revisions = 99  # type: ignore[misc]


def test_run_budget_fields_are_exactly_the_seven_contract_fields() -> None:
    assert [f.name for f in dataclasses.fields(RunBudget)] == [
        "max_revisions",
        "resume_pass_score",
        "ats_pass_threshold",
        "max_total_llm_calls",
        "max_openai_calls",
        "max_claude_calls",
        "max_revision_calls",
    ]


# ─── clamp_budget ─────────────────────────────────────────────────────────────


def test_empty_mapping_returns_the_defaults() -> None:
    assert clamp_budget({}) == RunBudget()


def test_absent_keys_take_the_default() -> None:
    budget = clamp_budget({"max_revisions": 3})
    assert budget.max_revisions == 3
    assert budget.resume_pass_score == RESUME_PASS_SCORE
    assert budget.max_total_llm_calls == MAX_TOTAL_LLM_CALLS


def test_values_within_range_are_honoured() -> None:
    budget = clamp_budget(
        {
            "max_revisions": 4,
            "resume_pass_score": 9.0,
            "ats_pass_threshold": 90,
            "max_total_llm_calls": 20,
            "max_openai_calls": 6,
            "max_claude_calls": 12,
            "max_revision_calls": 8,
        }
    )
    assert budget == RunBudget(
        max_revisions=4,
        resume_pass_score=9.0,
        ats_pass_threshold=90,
        max_total_llm_calls=20,
        max_openai_calls=6,
        max_claude_calls=12,
        max_revision_calls=8,
    )


@pytest.mark.parametrize(
    ("field", "requested"),
    [
        ("max_revisions", 99),
        ("max_total_llm_calls", 1000),
        ("max_openai_calls", 50),
        ("max_claude_calls", 64),
        ("max_revision_calls", 40),
        ("resume_pass_score", 10.0),
        ("ats_pass_threshold", 100),
    ],
)
def test_a_value_above_the_ceiling_is_clamped_to_the_ceiling(field: str, requested: float) -> None:
    budget = clamp_budget({field: requested})
    assert getattr(budget, field) == SERVER_CEILINGS[field]


def test_a_user_can_never_buy_more_budget_than_the_ceiling_allows() -> None:
    budget = clamp_budget(dict.fromkeys(SERVER_CEILINGS, 10_000))
    for field, ceiling in SERVER_CEILINGS.items():
        assert getattr(budget, field) == ceiling


@pytest.mark.parametrize(
    ("field", "requested", "expected"),
    [
        ("max_revisions", 0, 1),
        ("max_revisions", -5, 1),
        ("max_total_llm_calls", 0, 1),
        ("max_openai_calls", -1, 1),
        ("max_claude_calls", 0, 1),
        ("max_revision_calls", -20, 1),
        ("ats_pass_threshold", 0, 1),
    ],
)
def test_a_count_below_one_is_clamped_up_to_one(field: str, requested: int, expected: int) -> None:
    assert getattr(clamp_budget({field: requested}), field) == expected


@pytest.mark.parametrize("requested", [-0.5, -100.0])
def test_a_score_below_zero_is_clamped_up_to_zero(requested: float) -> None:
    assert clamp_budget({"resume_pass_score": requested}).resume_pass_score == 0.0


def test_zero_is_a_legal_pass_score() -> None:
    assert clamp_budget({"resume_pass_score": 0.0}).resume_pass_score == 0.0


@pytest.mark.parametrize("bad", ["lots", None, [], {}, "", "8.0.1"])
def test_an_unparseable_value_falls_back_to_the_default(bad: object) -> None:
    budget = clamp_budget({"max_revisions": bad, "resume_pass_score": bad})
    assert budget.max_revisions == MAX_REVISIONS
    assert budget.resume_pass_score == RESUME_PASS_SCORE


def test_an_unparseable_value_does_not_poison_the_other_fields() -> None:
    budget = clamp_budget({"max_revisions": "nope", "max_openai_calls": 7})
    assert budget.max_revisions == MAX_REVISIONS
    assert budget.max_openai_calls == 7


def test_a_numeric_string_is_parsed() -> None:
    budget = clamp_budget({"max_revisions": "3", "resume_pass_score": "9.0"})
    assert budget.max_revisions == 3
    assert budget.resume_pass_score == 9.0


def test_unknown_keys_are_ignored() -> None:
    assert clamp_budget({"max_revisions": 2, "delete_everything": True}) == RunBudget(max_revisions=2)


def test_clamp_budget_does_not_mutate_the_mapping_it_is_given() -> None:
    requested: dict[str, Any] = {"max_revisions": 99, "resume_pass_score": 12.0}
    before = dict(requested)
    clamp_budget(requested)
    assert requested == before


def test_clamp_budget_returns_a_run_budget() -> None:
    assert isinstance(clamp_budget({"max_revisions": 2}), RunBudget)


def test_clamp_budget_is_deterministic() -> None:
    requested = {"max_revisions": 99, "resume_pass_score": 3.25, "max_openai_calls": "4"}
    assert clamp_budget(requested) == clamp_budget(requested)


# ─── Acceptance criterion 6: no socket, no environment variable, no database ──

_PURITY_SCRIPT = """
import json, os, socket, sys

# Third-party imports happen first so their own import-time environment reads are not
# attributed to the pipeline modules under test.
import httpx, bs4  # noqa: F401
import resume_pipeline.ats.scorer  # noqa: F401

read_keys = []


class RecordingEnviron(dict):
    def __getitem__(self, key):
        read_keys.append(key)
        return super().__getitem__(key)

    def get(self, key, default=None):
        read_keys.append(key)
        return super().get(key, default)


os.environ = RecordingEnviron(os.environ)


def _blocked(*a, **k):
    raise AssertionError("opened a socket")


socket.socket.connect = _blocked
socket.create_connection = _blocked
socket.getaddrinfo = _blocked

from resume_pipeline.pipeline import (
    budgets, jd_loader, latex_text, prompts, scoring, sot_render, template_select,
)
from resume_pipeline.services import ats_service

budgets.clamp_budget({"max_revisions": 2})
scoring.attach_scores({"resume": {"category_scores": {}}})
template_select.recommend_template("Python and Java engineer.", "Backend Engineer")
jd_loader.load_jd_from_text("short")
prompts.governance_prompt()
latex_text.tex_to_text("\\\\textbf{hi}")
sot_render.render_source_of_truth(sot_render.SourceOfTruth())
ats_service.check("", "")

_db = {"asyncpg", "psycopg", "sqlite3", "sqlalchemy"}
db_modules = sorted(m for m in sys.modules if m.split(".")[0] in _db)
print(json.dumps({"env": sorted(set(read_keys)), "db": db_modules}))
"""


def test_package_reads_no_environment_variable_and_imports_no_database_driver() -> None:
    proc = subprocess.run(
        [sys.executable, "-c", _PURITY_SCRIPT],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stderr
    report = json.loads(proc.stdout.strip().splitlines()[-1])
    assert report["env"] == []
    assert report["db"] == []
