from __future__ import annotations

from resume_agent.graph import failing_documents


def test_failing_documents_resume_below_threshold() -> None:
    state = {"resume_score": 7.5, "revision_call_count": 0}
    assert failing_documents(state) == ["resume"]


def test_failing_documents_resume_passes() -> None:
    state = {"resume_score": 8.5, "revision_call_count": 0}
    assert failing_documents(state) == []


def test_failing_documents_no_score() -> None:
    state = {"resume_score": 0.0, "revision_call_count": 0}
    assert failing_documents(state) == ["resume"]
