"""`resume_pipeline.settings` (WP3 §1, acceptance criterion 1).

The load-bearing claim is *when* a misconfiguration is discovered. A service that starts with no
`RESUME_MASTER_KEY` and then 500s on the first request that needs it has turned a deploy-time
mistake into a user-facing one, so the contract puts the failure at import time and requires the
message to name the missing variable.

Every test here reloads the module inside an empty `RESUME_*` environment and an empty working
directory, so neither a developer's shell nor a stray `.env` next to the repo can make a required
variable look present.
"""

from __future__ import annotations

import base64
import importlib
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

SETTINGS_MODULE = "resume_pipeline.settings"
APP_DIR = Path(__file__).resolve().parents[1]

REQUIRED = ("database_url", "service_token", "documents_dir", "document_url_secret", "master_key")
OPTIONAL = ("latex_service_url", "llm_mode", "log_level", "environment")

MASTER_KEY = base64.b64encode(b"\x11" * 32).decode()


def _valid_env(documents_dir: Path) -> dict[str, str]:
    return {
        "RESUME_DATABASE_URL": "postgres://user:pass@127.0.0.1:5432/db",
        "RESUME_SERVICE_TOKEN": "service-token-value",
        "RESUME_DOCUMENTS_DIR": str(documents_dir),
        "RESUME_DOCUMENT_URL_SECRET": "url-signing-secret",
        "RESUME_MASTER_KEY": MASTER_KEY,
    }


@pytest.fixture
def isolated_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """An empty `RESUME_*` environment, in a directory with no `.env` in it."""
    for name in list(os.environ):
        if name.startswith("RESUME_"):
            monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _import_settings() -> ModuleType:
    """Import the settings module fresh, so import-time validation actually runs."""
    sys.modules.pop(SETTINGS_MODULE, None)
    return importlib.import_module(SETTINGS_MODULE)


def _load(env: dict[str, str], monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    module = _import_settings()
    cache_clear = getattr(module.get_settings, "cache_clear", None)
    if cache_clear is not None:
        cache_clear()
    return module


@pytest.fixture(autouse=True)
def _unload_after(isolated_env: Path) -> Any:
    yield
    # A settings module left in sys.modules with a test's environment baked into its lru_cache
    # would poison whatever runs next.
    sys.modules.pop(SETTINGS_MODULE, None)


# ─── The whole environment present ────────────────────────────────────────────


def test_a_complete_environment_imports_and_loads(
    isolated_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    documents = isolated_env / "documents"
    module = _load(_valid_env(documents), monkeypatch)
    settings = module.get_settings()

    assert settings.database_url == "postgres://user:pass@127.0.0.1:5432/db"
    assert settings.service_token == "service-token-value"
    assert Path(settings.documents_dir) == documents
    assert settings.document_url_secret == "url-signing-secret"
    assert settings.master_key == MASTER_KEY


def test_documents_dir_is_a_path(isolated_env: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load(_valid_env(isolated_env / "documents"), monkeypatch)
    assert isinstance(module.get_settings().documents_dir, Path)


def test_get_settings_is_cached(isolated_env: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load(_valid_env(isolated_env / "documents"), monkeypatch)
    assert module.get_settings() is module.get_settings()


# ─── Criterion 1: a missing required setting raises at import, naming the variable ───


@pytest.mark.parametrize("missing", REQUIRED)
def test_missing_required_setting_raises_at_import(
    isolated_env: Path, monkeypatch: pytest.MonkeyPatch, missing: str
) -> None:
    env = _valid_env(isolated_env / "documents")
    env.pop(f"RESUME_{missing.upper()}")
    for key, value in env.items():
        monkeypatch.setenv(key, value)

    with pytest.raises(Exception) as excinfo:  # noqa: B017 - pydantic's error type is not ours to fix
        _import_settings()

    # Criterion 1 is not "it fails", it is "it fails naming the variable". A ValidationError that
    # says only `1 validation error for Settings` leaves an operator guessing.
    text = str(excinfo.value).lower()
    assert missing in text, f"the failure does not name `{missing}`: {excinfo.value}"


def test_the_env_prefix_is_required(isolated_env: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An unprefixed `DATABASE_URL` is somebody else's variable and must not satisfy ours."""
    env = _valid_env(isolated_env / "documents")
    env.pop("RESUME_DATABASE_URL")
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("DATABASE_URL", "postgres://someone:else@127.0.0.1:5432/other")

    with pytest.raises(Exception) as excinfo:  # noqa: B017
        _import_settings()
    assert "database_url" in str(excinfo.value).lower()


def test_unknown_prefixed_variables_are_ignored(
    isolated_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = _valid_env(isolated_env / "documents")
    env["RESUME_SOMETHING_NOBODY_DECLARED"] = "1"
    module = _load(env, monkeypatch)
    assert module.get_settings().database_url.startswith("postgres://")


# ─── Defaults ─────────────────────────────────────────────────────────────────


def test_llm_mode_defaults_to_fake(isolated_env: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Live mode is opt-in. A stray dev process must not be able to spend money by omission."""
    module = _load(_valid_env(isolated_env / "documents"), monkeypatch)
    assert module.get_settings().llm_mode == "fake"


def test_other_defaults(isolated_env: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load(_valid_env(isolated_env / "documents"), monkeypatch)
    settings = module.get_settings()
    assert settings.latex_service_url == "http://127.0.0.1:58080"
    assert settings.log_level == "info"
    assert settings.environment == "development"


@pytest.mark.parametrize("mode", ["fake", "live"])
def test_llm_mode_accepts_both_modes(
    isolated_env: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    env = _valid_env(isolated_env / "documents")
    env["RESUME_LLM_MODE"] = mode
    module = _load(env, monkeypatch)
    assert module.get_settings().llm_mode == mode


def test_llm_mode_rejects_anything_else(
    isolated_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = _valid_env(isolated_env / "documents")
    env["RESUME_LLM_MODE"] = "real"
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    with pytest.raises(Exception) as excinfo:  # noqa: B017
        _import_settings()
    assert "llm_mode" in str(excinfo.value).lower()


@pytest.mark.parametrize("environment", ["development", "production"])
def test_environment_accepts_both_values(
    isolated_env: Path, monkeypatch: pytest.MonkeyPatch, environment: str
) -> None:
    env = _valid_env(isolated_env / "documents")
    env["RESUME_ENVIRONMENT"] = environment
    module = _load(env, monkeypatch)
    assert module.get_settings().environment == environment


def test_environment_rejects_anything_else(
    isolated_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = _valid_env(isolated_env / "documents")
    env["RESUME_ENVIRONMENT"] = "staging"
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    with pytest.raises(Exception) as excinfo:  # noqa: B017
        _import_settings()
    assert "environment" in str(excinfo.value).lower()


# ─── .env.example ─────────────────────────────────────────────────────────────


def test_env_example_documents_every_variable() -> None:
    example = APP_DIR / ".env.example"
    assert example.exists(), "WP3 §1 requires apps/resume-pipeline/.env.example"
    text = example.read_text(encoding="utf-8")

    for name in REQUIRED + OPTIONAL:
        assert f"RESUME_{name.upper()}" in text, f"`.env.example` does not mention {name}"

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    comments = [line for line in lines if line.startswith("#")]
    assert len(comments) >= len(REQUIRED + OPTIONAL), "one comment line per variable"


def test_env_example_holds_no_todos_and_no_real_secret() -> None:
    text = (APP_DIR / ".env.example").read_text(encoding="utf-8")
    assert "TODO" not in text.upper()
    # An example file that ships a usable key is a leak, not an example.
    assert "sk-ant-" not in text
    assert "sk-proj-" not in text
