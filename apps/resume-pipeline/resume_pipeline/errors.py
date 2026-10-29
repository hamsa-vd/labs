"""Application error hierarchy (RG-004).

Every failure the API returns renders through one handler into a single envelope:

    {"error": {"code": "run_budget_exceeded", "message": "Human sentence.", "details": {}}}

`code` is a stable snake_case string the UI switches on; `message` follows the arey voice —
what happened, then what to do, no exclamation marks. Never put a secret, a resume body, or a
job description in `message` or `details`.
"""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    code = "internal_error"
    status = 500

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        status: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        if status is not None:
            self.status = status
        self.details: dict[str, Any] = details or {}

    def envelope(self) -> dict[str, Any]:
        return {"error": {"code": self.code, "message": self.message, "details": self.details}}


class NotFound(AppError):
    code = "not_found"
    status = 404


class Forbidden(AppError):
    code = "forbidden"
    status = 403


class Conflict(AppError):
    code = "conflict"
    status = 409


class ValidationFailed(AppError):
    code = "validation_failed"
    status = 422


class BudgetExceeded(AppError):
    code = "run_budget_exceeded"
    status = 409


class UpstreamFailed(AppError):
    code = "upstream_failed"
    status = 502


class MissingApiKey(AppError):
    code = "missing_api_key"
    status = 400
