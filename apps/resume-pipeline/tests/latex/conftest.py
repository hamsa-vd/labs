"""Local fixtures for the WP7 LaTeX tests.

Three things live here, none of which belong in the shared `tests/conftest.py`:

1. `apps/resume-latex/` on `sys.path`, so `parse_log` can be imported. That directory is a
   container payload, not an installed package, so it is not importable by default.
2. Lazy module fixtures. WP7's source is written by a different agent, so these tests must
   *collect* cleanly before it exists. Importing inside a fixture turns "the module is not
   written yet" into a test failure rather than a collection error, which is what the blind
   protocol needs.
3. A hole in the suite-wide socket guard, opened only for tests marked `network`. The guard in
   `tests/conftest.py` is autouse and correct — no unit test may touch a socket. The container
   integration tests talk to a real Tectonic container on localhost and are the one exception.
"""

from __future__ import annotations

import base64
import importlib
import os
import socket
import sys
import tempfile
from pathlib import Path
from types import ModuleType

import pytest

TESTS_LATEX_DIR = Path(__file__).resolve().parent
APP_DIR = TESTS_LATEX_DIR.parents[1]
LATEX_SERVICE_DIR = APP_DIR.parent / "resume-latex"
SEED_TEMPLATE_DIR = APP_DIR / "seed" / "templates"

# `parse_log.py` ships inside the container image and has no package around it.
if str(LATEX_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(LATEX_SERVICE_DIR))


# `resume_pipeline.settings` resolves at import and refuses to load without these, so any test
# that touches the compile client needs them present before the first import. They belong in the
# shared `tests/conftest.py` — every package that imports the settings module has the same need —
# but that file is WP2's and not ours to edit, so they are provisioned here with `setdefault`:
# a real value in the environment always wins.
#
# None of these reach anything. No connection is opened (the socket guard forbids it), and the
# LaTeX URL points at a host that does not resolve, so a request that escaped the stub transport
# would fail loudly rather than quietly hitting the developer's own container.
FALLBACK_SETTINGS_ENV = {
    "RESUME_DATABASE_URL": "postgresql://ascend:ascend@127.0.0.1:55432/ascend_tests",
    "RESUME_SERVICE_TOKEN": "tests-service-token",
    "RESUME_DOCUMENTS_DIR": str(Path(tempfile.gettempdir()) / "ascend-tests-documents"),
    "RESUME_DOCUMENT_URL_SECRET": "tests-document-url-secret",
    "RESUME_MASTER_KEY": base64.urlsafe_b64encode(b"ascend-tests-master-key-032bytes").decode(),
    "RESUME_LATEX_SERVICE_URL": "http://latex.invalid",
    "RESUME_LLM_MODE": "fake",
}


def ensure_settings_env() -> None:
    for name, value in FALLBACK_SETTINGS_ENV.items():
        os.environ.setdefault(name, value)


def pytest_configure(config: pytest.Config) -> None:
    ensure_settings_env()
    config.addinivalue_line(
        "markers",
        "network: test may open a real socket; lifts the suite-wide network guard.",
    )


# ─── Network guard escape hatch ───────────────────────────────────────────────

# Captured at import time, before `tests/conftest.py::_no_network` monkeypatches them.
_REAL_SOCKET_API = {
    "socket.connect": socket.socket.connect,
    "socket.connect_ex": socket.socket.connect_ex,
    "socket.sendto": socket.socket.sendto,
    "create_connection": socket.create_connection,
    "getaddrinfo": socket.getaddrinfo,
}


@pytest.fixture(autouse=True)
def _allow_network_when_marked(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Restore the real socket API for tests marked `network`, and only for those."""
    if "network" not in request.keywords:
        return
    monkeypatch.setattr(socket.socket, "connect", _REAL_SOCKET_API["socket.connect"])
    monkeypatch.setattr(socket.socket, "connect_ex", _REAL_SOCKET_API["socket.connect_ex"])
    monkeypatch.setattr(socket.socket, "sendto", _REAL_SOCKET_API["socket.sendto"])
    monkeypatch.setattr(socket, "create_connection", _REAL_SOCKET_API["create_connection"])
    monkeypatch.setattr(socket, "getaddrinfo", _REAL_SOCKET_API["getaddrinfo"])


# ─── Lazy module fixtures ─────────────────────────────────────────────────────


def _import(name: str) -> ModuleType:
    ensure_settings_env()
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError as exc:  # pragma: no cover - only before WP7 source lands
        pytest.fail(f"WP7 has not provided `{name}` yet ({exc}).", pytrace=False)


@pytest.fixture(scope="session")
def validate_mod() -> ModuleType:
    """`resume_pipeline.latex.validate` — the denylist and structural validator."""
    return _import("resume_pipeline.latex.validate")


@pytest.fixture(scope="session")
def parse_log_mod() -> ModuleType:
    """`parse_log` from `apps/resume-latex/`."""
    return _import("parse_log")


@pytest.fixture(scope="session")
def latex_service_mod() -> ModuleType:
    """`resume_pipeline.services.latex` — the compile client."""
    return _import("resume_pipeline.services.latex")


# ─── Seeded templates ─────────────────────────────────────────────────────────


def seed_template_paths() -> list[Path]:
    """Every seeded template, sorted. Used at collection time to parametrise."""
    return sorted(SEED_TEMPLATE_DIR.glob("*.tex"))


@pytest.fixture(scope="session")
def seed_template_dir() -> Path:
    return SEED_TEMPLATE_DIR


# ─── Container integration ────────────────────────────────────────────────────

LATEX_URL_ENV = "RESUME_LATEX_URL"
LATEX_CONTAINER_ENV = "RESUME_LATEX_CONTAINER"
DEFAULT_CONTAINER = "ascend-rg-latex"


@pytest.fixture(scope="session")
def latex_service_url() -> str:
    """Base URL of a running compiler container, or skip."""
    url = os.environ.get(LATEX_URL_ENV, "").strip()
    if not url:
        pytest.skip(f"{LATEX_URL_ENV} is not set; the LaTeX container is not running.")
    return url.rstrip("/")


@pytest.fixture(scope="session")
def latex_container_name() -> str:
    return os.environ.get(LATEX_CONTAINER_ENV, "").strip() or DEFAULT_CONTAINER
