"""Process configuration (RG-004).

Configuration is validated at **import**, not at first request. A service that starts with a
missing `RESUME_DATABASE_URL` and then returns 500 to a user is worse than one that refuses to
start: the first failure is discovered in production by a person, the second by the operator
during deploy.

`llm_mode` defaults to `"fake"`. Live mode is opt-in and never the default, because a test run or
a stray dev process that picked up a user's key must not be able to spend their money simply by
omitting a variable.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PREFIX = "RESUME_"


class MissingSettings(ValueError, RuntimeError):
    """Raised at import when a required setting is absent.

    It derives from both `ValueError` and `RuntimeError` on purpose. Pydantic's own
    `ValidationError` is a `ValueError`, so callers that were written against pydantic keep
    working; callers that reasonably expect a configuration failure to be a `RuntimeError` do
    too. The originating `ValidationError` is preserved as `__cause__`.
    """


class Settings(BaseSettings):
    database_url: str
    service_token: str
    documents_dir: Path
    document_url_secret: str
    master_key: str
    latex_service_url: str = "http://127.0.0.1:58080"
    llm_mode: Literal["fake", "live"] = "fake"
    log_level: str = "info"
    environment: Literal["development", "production"] = "development"

    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX, env_file=".env", extra="ignore")


def _describe(exc: ValidationError) -> str:
    """Name the missing variables the way the operator set them, not the way pydantic sees them.

    An operator reading the crash needs `RESUME_DATABASE_URL`; a developer reading it needs
    `database_url`. Both spellings appear so neither has to translate.
    """
    missing = [
        str(error["loc"][0])
        for error in exc.errors()
        if error["type"] == "missing" and error["loc"]
    ]
    if not missing:
        return f"The resume pipeline configuration is not valid: {exc}. Fix the environment and restart."
    named = ", ".join(f"{ENV_PREFIX}{field.upper()} ({field})" for field in sorted(missing))
    plural = "variables are" if len(missing) > 1 else "variable is"
    return (
        f"The resume pipeline did not start because a required {plural} not set: {named}. "
        "Set it in the environment or in .env, then start the service again."
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    try:
        # Every field is populated from the environment; mypy cannot see that and asks for
        # the required ones as arguments.
        return Settings()  # type: ignore[call-arg]
    except ValidationError as exc:
        raise MissingSettings(_describe(exc)) from exc


#: Resolved once, here, so an incomplete environment is a failed import rather than a failed
#: request. Everything else in the service reaches configuration through `get_settings()`.
settings: Settings = get_settings()
