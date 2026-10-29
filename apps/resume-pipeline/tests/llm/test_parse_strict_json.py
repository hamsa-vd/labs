"""`parse_strict_json_object` (WP4 §1), ported verbatim from v1's `claude_client.py`.

The function is six lines long and every one of them is load-bearing, because a model that was
told "return strict JSON only" returns a fenced block roughly a third of the time. The order is
fixed: `json.loads` first, then the first `{...}` match with `DOTALL`, then `ValueError`.

The regex is `\\{.*\\}` and it is **greedy** — it spans from the first `{` to the last `}` in the
whole string. That is not a detail to tidy: it is why a fenced object with a trailing sentence
still parses, and why two concatenated objects do not. Both are pinned below so nobody "fixes" the
greediness and silently changes which of the model's two objects the review node reads.

One assertion is ours rather than v1's: the raw text must not appear in the error. The raw text of
a failed review contains the resume body, and the house rule is that no resume body reaches an
exception message.
"""

from __future__ import annotations

import json
from types import ModuleType

import pytest

RESUME_BODY = "Architected a Kafka event pipeline that cut settlement latency by 45 percent."


def test_a_plain_json_object_parses(base_mod: ModuleType) -> None:
    assert base_mod.parse_strict_json_object('{"verdict": "pass"}') == {"verdict": "pass"}


def test_an_empty_object_parses(base_mod: ModuleType) -> None:
    assert base_mod.parse_strict_json_object("{}") == {}


def test_surrounding_whitespace_is_tolerated(base_mod: ModuleType) -> None:
    assert base_mod.parse_strict_json_object('\n\n  {"a": 1}  \n') == {"a": 1}


def test_a_nested_object_survives(base_mod: ModuleType) -> None:
    raw = '{"resume": {"category_scores": {"single_page_compliance": 9.0}}}'

    assert base_mod.parse_strict_json_object(raw)["resume"]["category_scores"] == {
        "single_page_compliance": 9.0
    }


def test_a_fenced_json_block_parses_through_the_regex_fallback(base_mod: ModuleType) -> None:
    raw = '```json\n{"verdict": "revise", "score": 6.5}\n```'

    assert base_mod.parse_strict_json_object(raw) == {"verdict": "revise", "score": 6.5}


def test_a_bare_fence_without_a_language_parses(base_mod: ModuleType) -> None:
    raw = '```\n{"verdict": "pass"}\n```'

    assert base_mod.parse_strict_json_object(raw) == {"verdict": "pass"}


def test_prose_before_and_after_the_object_is_discarded(base_mod: ModuleType) -> None:
    raw = 'Here is the review you asked for:\n{"verdict": "pass"}\nLet me know if you want more.'

    assert base_mod.parse_strict_json_object(raw) == {"verdict": "pass"}


def test_a_multi_line_object_is_matched_across_newlines(base_mod: ModuleType) -> None:
    raw = 'Result:\n{\n  "verdict": "pass",\n  "must_fix": [\n    "Tighten the summary."\n  ]\n}\n'

    parsed = base_mod.parse_strict_json_object(raw)

    assert parsed["must_fix"] == ["Tighten the summary."]


def test_a_stray_opening_brace_after_the_object_does_not_break_the_match(
    base_mod: ModuleType,
) -> None:
    """The greedy match ends at the last `}`, which here is still the end of the real object."""
    raw = '{"verdict": "pass"} and then I started to say something {else'

    assert base_mod.parse_strict_json_object(raw) == {"verdict": "pass"}


def test_two_concatenated_objects_raise_rather_than_silently_picking_one(
    base_mod: ModuleType,
) -> None:
    """Greedy matching spans both, which is invalid JSON. Failing loudly is the right answer:
    quietly reading the first object would hide that the model answered twice."""
    raw = '{"verdict": "pass"}\n{"verdict": "revise"}'

    with pytest.raises(ValueError):
        base_mod.parse_strict_json_object(raw)


def test_a_json_array_is_rejected(base_mod: ModuleType) -> None:
    with pytest.raises(ValueError):
        base_mod.parse_strict_json_object('["pass", "revise"]')


def test_a_json_string_is_rejected(base_mod: ModuleType) -> None:
    with pytest.raises(ValueError):
        base_mod.parse_strict_json_object('"just a string"')


def test_a_json_number_is_rejected(base_mod: ModuleType) -> None:
    with pytest.raises(ValueError):
        base_mod.parse_strict_json_object("8.6")


def test_json_null_is_rejected(base_mod: ModuleType) -> None:
    with pytest.raises(ValueError):
        base_mod.parse_strict_json_object("null")


def test_text_with_no_object_at_all_raises(base_mod: ModuleType) -> None:
    with pytest.raises(ValueError):
        base_mod.parse_strict_json_object("I could not complete that review.")


def test_an_empty_string_raises(base_mod: ModuleType) -> None:
    with pytest.raises(ValueError):
        base_mod.parse_strict_json_object("")


def test_a_malformed_object_raises(base_mod: ModuleType) -> None:
    with pytest.raises(ValueError):
        base_mod.parse_strict_json_object('{"verdict": }')


def test_a_json_decode_error_is_a_value_error(base_mod: ModuleType) -> None:
    """Callers catch `ValueError`; `JSONDecodeError` is one, and the fallback path must not leak
    some other exception type past them."""
    with pytest.raises(ValueError):
        base_mod.parse_strict_json_object("{not json at all}")

    assert issubclass(json.JSONDecodeError, ValueError)


def test_unicode_survives_the_round_trip(base_mod: ModuleType) -> None:
    raw = '{"note": "Optimisé — 45 % faster"}'

    assert base_mod.parse_strict_json_object(raw)["note"] == "Optimisé — 45 % faster"


def test_the_raw_response_is_not_echoed_into_the_error(base_mod: ModuleType) -> None:
    """A failed review's raw text contains the resume. No resume body reaches an error message."""
    raw = f"I cannot produce JSON for this resume: {RESUME_BODY}"

    with pytest.raises(ValueError) as caught:
        base_mod.parse_strict_json_object(raw)

    assert RESUME_BODY not in str(caught.value)


def test_the_raw_response_is_not_echoed_when_the_object_is_malformed(
    base_mod: ModuleType,
) -> None:
    raw = '{"resume_excerpt": "' + RESUME_BODY + '", }'

    with pytest.raises(ValueError) as caught:
        base_mod.parse_strict_json_object(raw)

    assert RESUME_BODY not in str(caught.value)


def test_the_result_is_a_plain_dict(base_mod: ModuleType) -> None:
    parsed = base_mod.parse_strict_json_object('{"a": 1}')

    assert isinstance(parsed, dict)
