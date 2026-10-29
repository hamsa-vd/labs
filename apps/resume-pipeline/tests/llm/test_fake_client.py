"""`FakeLLMClient` (WP4 §3) — the client the whole suite runs on.

`LLM_MODE=fake` is the default everywhere except a deliberate live run, so almost every test of
the graph, the API and the revision loop gets its LLM output from here. That makes the fake a
piece of test infrastructure with a contract of its own, and the contract is: **the output must
survive the same parsing the real output does.**

- targeting and review come back as JSON that `parse_strict_json_object` accepts;
- a review response scores all eight rubric categories, asserted against `scoring.RESUME_RUBRIC`
  itself rather than a copied list, so adding a category to the rubric fails here first;
- generation, revision and cover_letter come back as a LaTeX document with a preamble and a body.

The eight weights sum to 1.0, which is what makes `score_sequence` testable: setting every
category to 6.5 makes `attach_scores` return exactly 6.5, and that is how a later package forces
one revision cycle and then a pass.

Determinism is the other half. The same prompt must produce the same bytes, on the same client and
on a fresh one, or a graph test that runs twice is two different experiments.
"""

from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from resume_pipeline.pipeline.scoring import RESUME_RUBRIC, attach_scores
from tests.llm.conftest import prompt_digest

JSON_STAGES = ("targeting", "review")
LATEX_STAGES = ("generation", "revision", "cover_letter")
ALL_STAGES = JSON_STAGES + LATEX_STAGES

SYSTEM = "You are a resume tailoring system for Hamsa Vardhan."
USER = "Company: Liv-ex\nJob title: Senior Backend Engineer\n"

#: Prompts whose fixtures are committed under `tests/fixtures/llm/<stage>/`. The digest is
#: recomputed in `test_every_committed_fixture_is_addressable`, so an edit here that orphans a
#: fixture file fails rather than quietly falling through to the generic response.
FIXTURE_PROMPTS = {
    "targeting": (
        "Fixture prompt for the targeting stage.\n"
        "Company: Liv-ex\nJob title: Senior Backend Engineer\n"
    ),
    "review": (
        "Fixture prompt for the review stage.\n"
        "Company: Liv-ex\nJob title: Senior Backend Engineer\nRevision number: 0\n"
    ),
    "generation": (
        "Fixture prompt for the generation stage.\n"
        "Company: Liv-ex\nJob title: Senior Backend Engineer\n"
    ),
}

FIXTURE_MARKERS = {
    "targeting": "FIXTURE-MARKER-TARGETING-b41c9d",
    "review": "FIXTURE-MARKER-REVIEW-7a2e05",
    "generation": "FIXTURE-MARKER-GENERATION-15d8f3",
}


async def ask(client: Any, stage: str | None = None, user: str = USER, **extra: Any) -> Any:
    kwargs: dict[str, Any] = {"system_prompt": SYSTEM, "user_prompt": user}
    if stage is not None:
        kwargs["stage"] = stage
    kwargs.update(extra)
    return await client.complete(**kwargs)


# ─── Shape ────────────────────────────────────────────────────────────────────


def test_the_fake_defaults_to_the_fake_provider_and_model(fake_mod: ModuleType) -> None:
    client = fake_mod.FakeLLMClient()

    assert client.provider == "fake"
    assert client.model == "fake-model"


def test_the_provider_and_model_can_be_overridden(fake_mod: ModuleType) -> None:
    """A fake run still records a provider and model on every `resume_llm_calls` row, and a test
    of the cost rollup needs those to be whatever it says they are."""
    client = fake_mod.FakeLLMClient(provider="anthropic", model="claude-sonnet-4-5")

    assert client.provider == "anthropic"
    assert client.model == "claude-sonnet-4-5"


def test_the_constructor_takes_the_contract_keywords(fake_mod: ModuleType) -> None:
    params = inspect.signature(fake_mod.FakeLLMClient).parameters

    assert {"stage_responses", "fixtures_dir", "provider", "model"} <= set(params)


def test_complete_accepts_an_explicit_stage(fake_mod: ModuleType) -> None:
    """The caller sets the stage; inference is the fallback, not the rule. The factory-built real
    clients ignore this keyword, so the graph can pass it unconditionally."""
    params = inspect.signature(fake_mod.FakeLLMClient.complete).parameters

    assert "stage" in params
    assert params["stage"].default is None
    assert params["max_tokens"].default == 6000


async def test_complete_returns_a_completion(fake_mod: ModuleType, base_mod: ModuleType) -> None:
    client = fake_mod.FakeLLMClient()

    completion = await ask(client, "generation")

    assert isinstance(completion, base_mod.Completion)
    assert completion.text.strip() != ""


async def test_the_completion_reports_non_negative_token_counts(fake_mod: ModuleType) -> None:
    """Telemetry sums these on every run, fake runs included."""
    client = fake_mod.FakeLLMClient()

    completion = await ask(client, "generation")

    assert isinstance(completion.input_tokens, int)
    assert isinstance(completion.output_tokens, int)
    assert completion.input_tokens >= 0
    assert completion.output_tokens >= 0


# ─── The call log ─────────────────────────────────────────────────────────────


async def test_every_call_is_recorded(fake_mod: ModuleType) -> None:
    client = fake_mod.FakeLLMClient()

    await ask(client, "targeting")
    await ask(client, "generation")

    assert len(client.calls) == 2


async def test_a_call_record_carries_the_stage_the_prompts_and_a_timestamp(
    fake_mod: ModuleType,
) -> None:
    client = fake_mod.FakeLLMClient()

    await ask(client, "review", user="USER-MARKER")

    record = client.calls[0]
    assert {"stage", "system", "user", "at"} <= set(record)
    assert record["stage"] == "review"
    assert record["system"] == SYSTEM
    assert record["user"] == "USER-MARKER"
    assert record["at"] is not None


async def test_each_client_keeps_its_own_call_log(fake_mod: ModuleType) -> None:
    """A mutable default would share one list across every client in the process and make call
    counts depend on test ordering."""
    first = fake_mod.FakeLLMClient()
    second = fake_mod.FakeLLMClient()

    await ask(first, "generation")

    assert len(first.calls) == 1
    assert second.calls == []


# ─── Schema-valid output ──────────────────────────────────────────────────────


@pytest.mark.parametrize("stage", JSON_STAGES)
async def test_json_stages_parse_with_the_strict_parser(
    fake_mod: ModuleType, base_mod: ModuleType, stage: str
) -> None:
    client = fake_mod.FakeLLMClient()

    completion = await ask(client, stage)

    assert isinstance(base_mod.parse_strict_json_object(completion.text), dict)


@pytest.mark.parametrize("stage", LATEX_STAGES)
async def test_latex_stages_return_a_complete_document(fake_mod: ModuleType, stage: str) -> None:
    client = fake_mod.FakeLLMClient()

    text = (await ask(client, stage)).text

    assert "\\documentclass" in text
    assert "\\begin{document}" in text
    assert "\\end{document}" in text


@pytest.mark.parametrize("stage", LATEX_STAGES)
async def test_the_latex_document_is_in_the_right_order(fake_mod: ModuleType, stage: str) -> None:
    """A preamble after `\\begin{document}` does not compile, and the point of the fake is that a
    fake run exercises the real compile path."""
    text = (await ask(fake_mod.FakeLLMClient(), stage)).text

    assert text.index("\\documentclass") < text.index("\\begin{document}")
    assert text.index("\\begin{document}") < text.index("\\end{document}")


@pytest.mark.parametrize("stage", LATEX_STAGES)
async def test_the_latex_is_not_wrapped_in_a_markdown_fence(
    fake_mod: ModuleType, stage: str
) -> None:
    """Every LaTeX prompt says "do not wrap it in Markdown". The fake models a compliant model."""
    text = (await ask(fake_mod.FakeLLMClient(), stage)).text

    assert "```" not in text


async def test_a_review_scores_all_eight_rubric_categories(
    fake_mod: ModuleType, base_mod: ModuleType
) -> None:
    text = (await ask(fake_mod.FakeLLMClient(), "review")).text
    payload = base_mod.parse_strict_json_object(text)

    assert set(RESUME_RUBRIC) <= set(payload["resume"]["category_scores"])


async def test_a_review_carries_must_fix_and_fix_resolution_lists(
    fake_mod: ModuleType, base_mod: ModuleType
) -> None:
    resume = base_mod.parse_strict_json_object(
        (await ask(fake_mod.FakeLLMClient(), "review")).text
    )["resume"]

    assert isinstance(resume["must_fix"], list)
    assert isinstance(resume["fix_resolution"], list)


async def test_attach_scores_turns_a_fake_review_into_a_real_number(
    fake_mod: ModuleType, base_mod: ModuleType
) -> None:
    """The whole point of the schema requirements: `attach_scores` must produce a score, with no
    category missing. A missing category silently scores zero and drags the weighted total down."""
    payload = base_mod.parse_strict_json_object((await ask(fake_mod.FakeLLMClient(), "review")).text)

    scored = attach_scores(payload)

    assert isinstance(scored["resume"]["score"], float)
    assert scored["resume"]["missing_score_categories"] == []
    assert 0.0 <= scored["resume"]["score"] <= 10.0


# ─── Determinism ──────────────────────────────────────────────────────────────


@pytest.mark.parametrize("stage", ALL_STAGES)
async def test_the_same_prompt_gives_the_same_output(fake_mod: ModuleType, stage: str) -> None:
    client = fake_mod.FakeLLMClient()

    first = await ask(client, stage)
    second = await ask(client, stage)

    assert first.text == second.text


@pytest.mark.parametrize("stage", ALL_STAGES)
async def test_a_fresh_client_gives_the_same_output(fake_mod: ModuleType, stage: str) -> None:
    """Determinism has to hold across instances, or a graph test and its rerun disagree."""
    first = await ask(fake_mod.FakeLLMClient(), stage)
    second = await ask(fake_mod.FakeLLMClient(), stage)

    assert first.text == second.text


# ─── Resolution order ─────────────────────────────────────────────────────────


async def test_an_explicit_stage_response_wins(fake_mod: ModuleType) -> None:
    client = fake_mod.FakeLLMClient(stage_responses={"generation": "EXPLICIT RESPONSE"})

    assert (await ask(client, "generation")).text == "EXPLICIT RESPONSE"


async def test_a_stage_response_does_not_leak_into_other_stages(fake_mod: ModuleType) -> None:
    client = fake_mod.FakeLLMClient(stage_responses={"generation": "EXPLICIT RESPONSE"})

    assert (await ask(client, "revision")).text != "EXPLICIT RESPONSE"


async def test_a_fixture_is_used_when_one_matches_the_prompt(
    fake_mod: ModuleType, llm_fixture_dir: Path
) -> None:
    client = fake_mod.FakeLLMClient(fixtures_dir=llm_fixture_dir)

    text = (await ask(client, "review", user=FIXTURE_PROMPTS["review"])).text

    assert FIXTURE_MARKERS["review"] in text


@pytest.mark.parametrize("stage", ["targeting", "review"])
async def test_a_json_fixture_still_parses_strictly(
    fake_mod: ModuleType, base_mod: ModuleType, llm_fixture_dir: Path, stage: str
) -> None:
    client = fake_mod.FakeLLMClient(fixtures_dir=llm_fixture_dir)

    text = (await ask(client, stage, user=FIXTURE_PROMPTS[stage])).text

    assert isinstance(base_mod.parse_strict_json_object(text), dict)
    assert FIXTURE_MARKERS[stage] in text


async def test_a_latex_fixture_is_served_for_a_text_stage(
    fake_mod: ModuleType, llm_fixture_dir: Path
) -> None:
    client = fake_mod.FakeLLMClient(fixtures_dir=llm_fixture_dir)

    text = (await ask(client, "generation", user=FIXTURE_PROMPTS["generation"])).text

    assert FIXTURE_MARKERS["generation"] in text


async def test_an_unmatched_prompt_falls_through_to_the_generic_response(
    fake_mod: ModuleType, llm_fixture_dir: Path
) -> None:
    """A fixtures directory is a set of overrides, not a whitelist: a prompt nobody has recorded
    still has to produce schema-valid output, or adding one assertion to a graph test breaks it."""
    client = fake_mod.FakeLLMClient(fixtures_dir=llm_fixture_dir)

    text = (await ask(client, "generation", user="A prompt with no recorded fixture.")).text

    assert FIXTURE_MARKERS["generation"] not in text
    assert "\\documentclass" in text


async def test_an_explicit_stage_response_outranks_a_fixture(
    fake_mod: ModuleType, llm_fixture_dir: Path
) -> None:
    client = fake_mod.FakeLLMClient(
        stage_responses={"generation": "EXPLICIT RESPONSE"}, fixtures_dir=llm_fixture_dir
    )

    text = (await ask(client, "generation", user=FIXTURE_PROMPTS["generation"])).text

    assert text == "EXPLICIT RESPONSE"


def test_every_committed_fixture_is_addressable(llm_fixture_dir: Path) -> None:
    """The fixture files are named `sha256(user_prompt)[:16]`. This recomputes every name from the
    prompt in this module, so a fixture nobody can reach fails here instead of passing silently."""
    for stage, prompt in FIXTURE_PROMPTS.items():
        expected = llm_fixture_dir / stage / f"{prompt_digest(prompt)}.json"
        assert expected.exists(), f"no fixture at {expected}"
        assert json.loads(expected.read_text(encoding="utf-8"))


def test_the_digest_helper_matches_the_contract(llm_fixture_dir: Path) -> None:
    prompt = FIXTURE_PROMPTS["review"]

    assert prompt_digest(prompt) == hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]
    assert len(prompt_digest(prompt)) == 16


# ─── score_sequence ───────────────────────────────────────────────────────────


async def test_score_sequence_drives_successive_reviews_in_order(
    fake_mod: ModuleType, base_mod: ModuleType
) -> None:
    """One failing review, then a passing one — exactly one revision cycle. The eight weights sum
    to 1.0, so a uniform category score is the weighted score, to the decimal."""
    client = fake_mod.FakeLLMClient(score_sequence=[6.5, 8.6])

    first = attach_scores(base_mod.parse_strict_json_object((await ask(client, "review")).text))
    second = attach_scores(base_mod.parse_strict_json_object((await ask(client, "review")).text))

    assert first["resume"]["score"] == pytest.approx(6.5)
    assert second["resume"]["score"] == pytest.approx(8.6)


async def test_a_score_sequence_review_is_still_schema_valid(
    fake_mod: ModuleType, base_mod: ModuleType
) -> None:
    client = fake_mod.FakeLLMClient(score_sequence=[6.5, 8.6])

    payload = base_mod.parse_strict_json_object((await ask(client, "review")).text)

    assert set(RESUME_RUBRIC) <= set(payload["resume"]["category_scores"])
    assert attach_scores(payload)["resume"]["missing_score_categories"] == []


async def test_a_score_sequence_does_not_disturb_the_other_stages(
    fake_mod: ModuleType,
) -> None:
    client = fake_mod.FakeLLMClient(score_sequence=[6.5, 8.6])

    assert "\\documentclass" in (await ask(client, "generation")).text


async def test_reviews_past_the_end_of_the_sequence_stay_valid(
    fake_mod: ModuleType, base_mod: ModuleType
) -> None:
    """The contract does not say what happens after the sequence runs out, so this asserts only
    what must be true either way: the response is still a review."""
    client = fake_mod.FakeLLMClient(score_sequence=[6.5])

    await ask(client, "review")
    payload = base_mod.parse_strict_json_object((await ask(client, "review")).text)

    assert set(RESUME_RUBRIC) <= set(payload["resume"]["category_scores"])


# ─── Stage detection ──────────────────────────────────────────────────────────


async def test_an_explicit_stage_beats_whatever_the_prompt_looks_like(
    fake_mod: ModuleType, seed_prompt_bodies: dict[str, str]
) -> None:
    """The caller sets the stage. A review-shaped prompt asked for as generation gets LaTeX."""
    client = fake_mod.FakeLLMClient()

    text = (await ask(client, "generation", user=seed_prompt_bodies["review"])).text

    assert "\\documentclass" in text


@pytest.mark.parametrize("stage", JSON_STAGES)
async def test_a_seeded_prompt_infers_a_json_stage(
    fake_mod: ModuleType,
    base_mod: ModuleType,
    seed_prompt_bodies: dict[str, str],
    stage: str,
) -> None:
    """Inference is exercised against the prompts the pipeline actually sends, not invented text:
    these are the bodies seeded into `resume_prompts`."""
    client = fake_mod.FakeLLMClient()

    text = (await ask(client, None, user=seed_prompt_bodies[stage])).text

    assert isinstance(base_mod.parse_strict_json_object(text), dict)


@pytest.mark.parametrize("stage", LATEX_STAGES)
async def test_a_seeded_prompt_infers_a_latex_stage(
    fake_mod: ModuleType, seed_prompt_bodies: dict[str, str], stage: str
) -> None:
    client = fake_mod.FakeLLMClient()

    text = (await ask(client, None, user=seed_prompt_bodies[stage])).text

    assert "\\documentclass" in text


async def test_an_unrecognisable_prompt_falls_back_to_generation(fake_mod: ModuleType) -> None:
    client = fake_mod.FakeLLMClient()

    completion = await ask(client, None, user="Say something.")

    assert "\\documentclass" in completion.text
    assert client.calls[0]["stage"] == "generation"


async def test_the_inferred_stage_is_what_gets_recorded(
    fake_mod: ModuleType, seed_prompt_bodies: dict[str, str]
) -> None:
    """The call log is how a graph test proves which node called out. An inferred stage that is
    never written down makes that log useless."""
    client = fake_mod.FakeLLMClient()

    await ask(client, None, user=seed_prompt_bodies["review"])

    assert client.calls[0]["stage"] == "review"
