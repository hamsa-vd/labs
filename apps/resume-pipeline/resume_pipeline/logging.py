"""Structured logging and the redaction processor (RG-007).

structlog, JSON, stdout. One process, one log stream, one shape.

The redaction processor **removes** a matching key rather than masking it. A line containing
`"api_key": "***"` is still a line that says an API key was in scope at that point, and the next
person to add a field named `api_key_prefix` gets it printed in full. Removal has no such edge:
the key is simply not in the output.

The key list is matched as a lower-cased substring, which is deliberately over-broad. `tex`
matches `resume_tex` and also `context`; `token` matches `service_token` and also
`input_tokens`. Losing a token count from a log line costs nothing. Losing a resume body to a log
file cannot be undone.
"""

from __future__ import annotations

import logging
import sys
from collections.abc import MutableMapping
from typing import Any

import structlog

#: Substrings that condemn a key. Matched against the lower-cased key name.
REDACT_KEYS: tuple[str, ...] = (
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

#: Strings longer than this are truncated. A log line is a breadcrumb, not a copy of the payload.
MAX_STRING_LENGTH = 500

TRUNCATION_SUFFIX = "…"

_LEVELS: dict[str, int] = {
    "critical": logging.CRITICAL,
    "error": logging.ERROR,
    "warning": logging.WARNING,
    "warn": logging.WARNING,
    "info": logging.INFO,
    "debug": logging.DEBUG,
    "notset": logging.NOTSET,
}


def should_redact(key: str) -> bool:
    lowered = key.lower()
    return any(marker in lowered for marker in REDACT_KEYS)


def _truncate(value: str) -> str:
    if len(value) <= MAX_STRING_LENGTH:
        return value
    return value[:MAX_STRING_LENGTH] + TRUNCATION_SUFFIX


def _scrub(value: Any) -> Any:
    if isinstance(value, dict):
        return _scrub_mapping(value)
    if isinstance(value, list):
        return [_scrub(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_scrub(item) for item in value)
    if isinstance(value, str):
        return _truncate(value)
    return value


def _scrub_mapping(mapping: dict[Any, Any]) -> dict[Any, Any]:
    cleaned: dict[Any, Any] = {}
    for key, value in mapping.items():
        if isinstance(key, str) and should_redact(key):
            continue
        cleaned[key] = _scrub(value)
    return cleaned


def redact(
    logger: Any, method_name: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    """structlog processor: drop secret-bearing keys, truncate what is left.

    Recurses into nested dicts and into lists (including lists of dicts), because a payload
    nested two levels down leaks exactly as well as one at the top.
    """
    return _scrub_mapping(dict(event_dict))


def configure_logging(level: str = "info") -> None:
    numeric = _LEVELS.get(level.lower(), logging.INFO)
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=numeric, force=True)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            redact,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(numeric),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=False,
    )


def bind_request(request_id: str, user_id: str | None = None, run_id: str | None = None) -> None:
    """Bind per-request identity to the log context for the rest of this task.

    `user_id` and `run_id` are bound only when present, so a line never carries a null that
    reads as "no user" when it really means "not known yet".
    """
    structlog.contextvars.bind_contextvars(request_id=request_id)
    if user_id is not None:
        structlog.contextvars.bind_contextvars(user_id=user_id)
    if run_id is not None:
        structlog.contextvars.bind_contextvars(run_id=run_id)


def clear_request() -> None:
    structlog.contextvars.clear_contextvars()
