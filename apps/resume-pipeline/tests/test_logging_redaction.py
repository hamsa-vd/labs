"""`resume_pipeline.logging` (WP3 §2, acceptance criteria 5 and 12).

The contract asks for this to be tested *per key name, not in aggregate*, and for one specific
failure mode to be ruled out: a key named `api_key` whose value has been replaced by `***` is still
a finding, because the log line now advertises that this event carries a key and an attacker
reading logs learns the shape of what to steal. So every assertion below is `key not in output`,
never `output[key] != value`.

The denied substrings are matched against the *lower-cased* key name, and matched as substrings,
which is deliberately over-broad: `latex` contains `tex`, `service_token` contains `token`. That
breadth is the point — a new field called `jd_excerpt` is redacted the day somebody adds it,
without anyone remembering to update a list.
"""

from __future__ import annotations

import importlib
import json
from collections.abc import Callable, Iterator
from typing import Any

import pytest
import structlog

LOGGING_MODULE = "resume_pipeline.logging"

# A value distinctive enough that finding it anywhere in the output is proof of a leak.
SENTINEL = "SENTINEL-4f0c9a2e-value-that-must-never-be-logged"

# The contract's list, spelled out. Each entry is a substring of the lower-cased key name.
DENIED_SUBSTRINGS = (
    "api_key",
    "apikey",
    "authorization",
    "secret",
    "token",
    "ciphertext",
    "password",
    "tex",
    "jd_text",
    "resume_text",
    "jd",
    "body",
)

# Real key names a caller might plausibly pass, one group per denied substring. Case is varied on
# purpose: the rule is defined on the lower-cased name.
DENIED_KEYS = [
    "api_key",
    "API_KEY",
    "anthropic_api_key",
    "apikey",
    "apiKey",
    "x-apikey",
    "authorization",
    "Authorization",
    "authorization_header",
    "secret",
    "SECRET",
    "document_url_secret",
    "token",
    "service_token",
    "input_tokens",
    "ciphertext",
    "key_ciphertext",
    "password",
    "db_password",
    "tex",
    "tex_source",
    "resume_tex",
    "latex",
    "context",
    "jd_text",
    "resume_text",
    "jd",
    "jd_url",
    "jd_source_type",
    "body",
    "request_body",
]

# Keys that carry no denied substring and must survive untouched. Each one is something the
# pipeline genuinely logs, so a regression here is a regression in observability.
KEPT_KEYS = [
    "event",
    "run_id",
    "user_id",
    "application_id",
    "request_id",
    "node",
    "company",
    "status",
    "latency_ms",
    "level",
    "timestamp",
    "score",
]


@pytest.fixture(scope="module")
def logging_mod() -> Any:
    try:
        return importlib.import_module(LOGGING_MODULE)
    except ModuleNotFoundError as exc:  # pragma: no cover - only before WP3 source lands
        pytest.fail(f"WP3 has not provided `{LOGGING_MODULE}` yet ({exc}).", pytrace=False)


@pytest.fixture(scope="module")
def redact(logging_mod: Any) -> Callable[..., dict[str, Any]]:
    return logging_mod.redact  # type: ignore[no-any-return]


@pytest.fixture(autouse=True)
def _restore_structlog() -> Iterator[None]:
    """`configure_logging` mutates global structlog state; hand it back afterwards."""
    yield
    structlog.reset_defaults()
    structlog.contextvars.clear_contextvars()


def _serialise(event_dict: dict[str, Any]) -> str:
    return json.dumps(event_dict, default=str)


def _no_denied_key_anywhere(value: Any) -> bool:
    if isinstance(value, dict):
        for key, inner in value.items():
            lowered = str(key).lower()
            if any(denied in lowered for denied in DENIED_SUBSTRINGS):
                return False
            if not _no_denied_key_anywhere(inner):
                return False
        return True
    if isinstance(value, list):
        return all(_no_denied_key_anywhere(item) for item in value)
    return True


# ─── Criterion 5, one key at a time: flat ─────────────────────────────────────


@pytest.mark.parametrize("key", DENIED_KEYS)
def test_denied_key_is_removed_not_masked(
    redact: Callable[..., dict[str, Any]], key: str
) -> None:
    event_dict = {"event": "llm_call", "node": "generate", key: SENTINEL}

    out = redact(None, "info", dict(event_dict))

    assert key not in out, f"`{key}` is still present; removal means absent, not masked"
    assert SENTINEL not in _serialise(out)
    assert out["event"] == "llm_call"
    assert out["node"] == "generate"


# ─── Criterion 5, one key at a time: nested in a dict ─────────────────────────


@pytest.mark.parametrize("key", DENIED_KEYS)
def test_denied_key_is_removed_inside_a_nested_dict(
    redact: Callable[..., dict[str, Any]], key: str
) -> None:
    event_dict = {
        "event": "provider_call",
        "request": {"model": "some-model", "headers": {key: SENTINEL}},
    }

    out = redact(None, "info", dict(event_dict))

    assert SENTINEL not in _serialise(out)
    assert key not in out["request"]["headers"]
    assert out["request"]["model"] == "some-model"


# ─── Criterion 5, one key at a time: inside a list of dicts ───────────────────


@pytest.mark.parametrize("key", DENIED_KEYS)
def test_denied_key_is_removed_inside_a_list_of_dicts(
    redact: Callable[..., dict[str, Any]], key: str
) -> None:
    event_dict = {
        "event": "batch",
        "calls": [
            {"node": "review", key: SENTINEL},
            {"node": "revise", "latency_ms": 12},
        ],
    }

    out = redact(None, "info", dict(event_dict))

    assert SENTINEL not in _serialise(out)
    assert key not in out["calls"][0]
    assert out["calls"][0]["node"] == "review"
    assert out["calls"][1] == {"node": "revise", "latency_ms": 12}


def test_every_denied_substring_is_covered_by_a_key_in_this_suite() -> None:
    """Guards the suite itself: if the contract grows a key, this test fails until it is tested."""
    for denied in DENIED_SUBSTRINGS:
        assert any(denied in key.lower() for key in DENIED_KEYS), f"no test key covers `{denied}`"


def test_deeply_nested_and_mixed_structures_are_cleaned(
    redact: Callable[..., dict[str, Any]]
) -> None:
    event_dict = {
        "event": "run_finished",
        "run": {
            "documents": [
                {"kind": "resume_tex", "tex": SENTINEL, "byte_size": 10},
                {"kind": "jd", "jd_text": SENTINEL, "byte_size": 20},
            ],
            "provider": {"auth": {"authorization": SENTINEL}},
        },
    }

    out = redact(None, "info", dict(event_dict))

    assert SENTINEL not in _serialise(out)
    assert _no_denied_key_anywhere(out)
    assert out["run"]["documents"][0]["byte_size"] == 10
    assert out["run"]["documents"][1]["byte_size"] == 20


# ─── Keys that must survive ───────────────────────────────────────────────────


@pytest.mark.parametrize("key", KEPT_KEYS)
def test_innocuous_key_survives(redact: Callable[..., dict[str, Any]], key: str) -> None:
    out = redact(None, "info", {"event": "something", key: "kept-value"})
    assert out[key] == "kept-value"


def test_non_string_values_are_left_alone(redact: Callable[..., dict[str, Any]]) -> None:
    event_dict: dict[str, Any] = {
        "event": "run",
        "count": 3,
        "ratio": 0.5,
        "ok": True,
        "missing": None,
        "items": [1, 2, 3],
    }
    out = redact(None, "info", dict(event_dict))
    assert out == event_dict


# ─── Truncation ───────────────────────────────────────────────────────────────


def test_a_long_string_is_truncated_to_500_plus_an_ellipsis(
    redact: Callable[..., dict[str, Any]]
) -> None:
    long_value = "a" * 600
    out = redact(None, "info", {"event": "e", "note": long_value})

    assert out["note"] == "a" * 500 + "…"
    assert len(out["note"]) == 501


def test_a_string_of_exactly_500_is_untouched(redact: Callable[..., dict[str, Any]]) -> None:
    exact = "b" * 500
    out = redact(None, "info", {"event": "e", "note": exact})
    assert out["note"] == exact


def test_a_string_of_501_is_truncated(redact: Callable[..., dict[str, Any]]) -> None:
    out = redact(None, "info", {"event": "e", "note": "c" * 501})
    assert out["note"] == "c" * 500 + "…"


def test_a_short_string_is_untouched(redact: Callable[..., dict[str, Any]]) -> None:
    out = redact(None, "info", {"event": "e", "note": "short"})
    assert out["note"] == "short"


def test_truncation_reaches_nested_dicts_and_lists(
    redact: Callable[..., dict[str, Any]]
) -> None:
    long_value = "d" * 900
    out = redact(
        None,
        "info",
        {
            "event": "e",
            "inner": {"note": long_value},
            "items": [{"note": long_value}],
        },
    )
    assert out["inner"]["note"] == "d" * 500 + "…"
    assert out["items"][0]["note"] == "d" * 500 + "…"


def test_truncation_does_not_resurrect_a_removed_key(
    redact: Callable[..., dict[str, Any]]
) -> None:
    """A 600-character resume body is removed, not truncated to a 500-character resume body."""
    out = redact(None, "info", {"event": "e", "resume_text": "e" * 600})
    assert "resume_text" not in out


# ─── Processor signature and structlog wiring ─────────────────────────────────


def test_redact_accepts_the_structlog_processor_signature(
    redact: Callable[..., dict[str, Any]]
) -> None:
    out = redact(None, "info", {"event": "e"})
    assert isinstance(out, dict)
    assert out["event"] == "e"


def test_configure_logging_emits_json_to_stdout_with_the_secret_gone(
    logging_mod: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    logging_mod.configure_logging("info")
    structlog.get_logger("wp3.test").info("provider_call", api_key=SENTINEL, node="review")

    captured = capsys.readouterr().out.strip()
    assert captured, "configure_logging must send events to stdout"
    line = json.loads(captured.splitlines()[-1])

    assert line["event"] == "provider_call"
    assert line["node"] == "review"
    assert "api_key" not in line
    assert SENTINEL not in captured


def test_configure_logging_is_idempotent(logging_mod: Any) -> None:
    logging_mod.configure_logging("info")
    logging_mod.configure_logging("debug")
    logging_mod.configure_logging()
    assert structlog.is_configured()


# ─── bind_request ─────────────────────────────────────────────────────────────


def test_bind_request_binds_the_request_id(logging_mod: Any) -> None:
    logging_mod.bind_request("req-123")
    assert structlog.contextvars.get_contextvars().get("request_id") == "req-123"


def test_bind_request_binds_user_and_run(logging_mod: Any) -> None:
    logging_mod.bind_request("req-456", user_id="user-1", run_id="run-1")
    bound = structlog.contextvars.get_contextvars()
    assert bound.get("request_id") == "req-456"
    assert bound.get("user_id") == "user-1"
    assert bound.get("run_id") == "run-1"


def test_bind_request_does_not_invent_a_user(logging_mod: Any) -> None:
    logging_mod.bind_request("req-789")
    assert structlog.contextvars.get_contextvars().get("user_id") is None
    assert structlog.contextvars.get_contextvars().get("run_id") is None


def test_bound_context_reaches_the_log_line(
    logging_mod: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    logging_mod.configure_logging("info")
    logging_mod.bind_request("req-abc", user_id="user-9")
    structlog.get_logger("wp3.test").info("handled")

    line = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert line["request_id"] == "req-abc"
    assert line["user_id"] == "user-9"
