"""`resume_pipeline.main` — the error envelope and request id (WP3 §7, criteria 2, 3 and 4).

One handler renders every `AppError` through `.envelope()` at its own status, and a bare
`Exception` becomes `internal_error` at 500 carrying a generic sentence. The second half of that is
the security-relevant half: a stack trace or an exception message in a response body is how a
connection string, a file path, or a fragment of somebody's resume ends up in a browser. So the
test raises an exception whose message is a distinctive sentinel and then greps the entire
response — body, headers and reason — for it.

The probe routes below are added to the app by this suite rather than assumed to exist, because
WP3 ships only `/v1/health`, and an envelope test that depends on a later work package's routes
would be testing the wrong thing.
"""

from __future__ import annotations

import importlib
import os
import sys
import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from resume_pipeline.errors import (
    AppError,
    BudgetExceeded,
    Conflict,
    Forbidden,
    MissingApiKey,
    NotFound,
    UpstreamFailed,
    ValidationFailed,
)

MAIN_MODULE = "resume_pipeline.main"

SERVICE_TOKEN = "service-token-for-tests"

# Distinctive enough that finding it anywhere in a response is proof of a leak.
SENTINEL = "pineapple-4f0c9a2e-internal-detail-that-must-not-escape"

MESSAGE = "That application was not found. Check the link and try again."

# Every error type the shared module defines, with the status and code it must render at.
ERROR_CASES = [
    ("not_found", NotFound, "not_found", 404),
    ("forbidden", Forbidden, "forbidden", 403),
    ("conflict", Conflict, "conflict", 409),
    ("validation_failed", ValidationFailed, "validation_failed", 422),
    ("budget_exceeded", BudgetExceeded, "run_budget_exceeded", 409),
    ("upstream_failed", UpstreamFailed, "upstream_failed", 502),
    ("missing_api_key", MissingApiKey, "missing_api_key", 400),
]
ERROR_TYPES = {name: error for name, error, _, _ in ERROR_CASES}


def _purge_resume_pipeline_modules() -> None:
    for name in list(sys.modules):
        if name.startswith("resume_pipeline.") and name != "resume_pipeline.errors":
            sys.modules.pop(name, None)


@pytest.fixture(scope="module")
def app(tmp_path_factory: pytest.TempPathFactory) -> Iterator[FastAPI]:
    """A real `create_app()`, with probe routes bolted on for the handler tests."""
    documents = tmp_path_factory.mktemp("documents")
    env = {
        "RESUME_DATABASE_URL": "postgres://user:pass@127.0.0.1:5432/nowhere",
        "RESUME_SERVICE_TOKEN": SERVICE_TOKEN,
        "RESUME_DOCUMENTS_DIR": str(documents),
        "RESUME_DOCUMENT_URL_SECRET": "url-signing-secret",
        "RESUME_MASTER_KEY": "EREREREREREREREREREREREREREREREREREREREREQ=",
        "RESUME_ENVIRONMENT": "production",
    }
    previous = {key: os.environ.get(key) for key in env}
    os.environ.update(env)
    _purge_resume_pipeline_modules()

    try:
        main: Any = importlib.import_module(MAIN_MODULE)
    except ModuleNotFoundError as exc:  # pragma: no cover - only before WP3 source lands
        pytest.fail(f"WP3 has not provided `{MAIN_MODULE}` yet ({exc}).", pytrace=False)

    instance = main.create_app()

    probe = APIRouter()

    @probe.get("/_wp3/app-error/{kind}")
    async def _raise_app_error(kind: str) -> dict[str, str]:
        raise ERROR_TYPES[kind](MESSAGE)

    @probe.get("/_wp3/app-error-with-details")
    async def _raise_with_details() -> dict[str, str]:
        raise ValidationFailed(MESSAGE, details={"field": "company"})

    @probe.get("/_wp3/boom")
    async def _raise_unhandled() -> dict[str, str]:
        raise RuntimeError(SENTINEL)

    @probe.get("/_wp3/ok")
    async def _ok() -> dict[str, str]:
        return {"status": "ok"}

    instance.include_router(probe, prefix="/v1")

    yield instance

    for key, value in previous.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    _purge_resume_pipeline_modules()


@pytest.fixture(scope="module")
def client(app: FastAPI) -> Iterator[TestClient]:
    # No lifespan: this suite may not open a socket, and a startup hook would want the database.
    yield TestClient(app, raise_server_exceptions=False)


# ─── Criterion 2: a raised AppError renders as its envelope ───────────────────


def test_not_found_renders_exactly_the_contract_envelope(client: TestClient) -> None:
    response = client.get("/v1/_wp3/app-error/not_found")

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "not_found", "message": MESSAGE, "details": {}}
    }


@pytest.mark.parametrize(
    ("kind", "code", "status"),
    [(name, code, status) for name, _, code, status in ERROR_CASES],
)
def test_every_app_error_renders_at_its_own_status(
    client: TestClient, kind: str, code: str, status: int
) -> None:
    response = client.get(f"/v1/_wp3/app-error/{kind}")

    assert response.status_code == status
    assert response.json() == {"error": {"code": code, "message": MESSAGE, "details": {}}}


def test_details_are_carried_through(client: TestClient) -> None:
    response = client.get("/v1/_wp3/app-error-with-details")

    assert response.status_code == 422
    assert response.json()["error"]["details"] == {"field": "company"}


def test_the_envelope_has_no_other_top_level_keys(client: TestClient) -> None:
    body = client.get("/v1/_wp3/app-error/conflict").json()
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message", "details"}


def test_the_error_envelope_is_json(client: TestClient) -> None:
    response = client.get("/v1/_wp3/app-error/forbidden")
    assert response.headers["content-type"].startswith("application/json")


# ─── Criterion 3: an unhandled exception says nothing about itself ────────────


def test_an_unhandled_exception_is_internal_error_at_500(client: TestClient) -> None:
    response = client.get("/v1/_wp3/boom")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"


def test_the_exception_message_appears_nowhere_in_the_response(client: TestClient) -> None:
    response = client.get("/v1/_wp3/boom")

    haystack = response.text + "\n" + "\n".join(f"{k}: {v}" for k, v in response.headers.items())
    assert SENTINEL not in haystack
    assert "RuntimeError" not in haystack
    assert "Traceback" not in haystack
    assert "resume_pipeline" not in response.text


def test_the_internal_error_message_is_a_sentence_not_a_shrug(client: TestClient) -> None:
    message = client.get("/v1/_wp3/boom").json()["error"]["message"]
    assert message.strip()
    assert "!" not in message, "arey copy carries no exclamation marks"
    assert message[0] == message[0].upper()


def test_the_unhandled_envelope_has_the_same_shape(client: TestClient) -> None:
    body = client.get("/v1/_wp3/boom").json()
    assert set(body) == {"error"}
    assert set(body["error"]) == {"code", "message", "details"}


# ─── Criterion 4: X-Request-Id ────────────────────────────────────────────────


def test_a_supplied_request_id_is_echoed(client: TestClient) -> None:
    request_id = "req-" + uuid.uuid4().hex
    response = client.get("/v1/_wp3/ok", headers={"X-Request-Id": request_id})
    assert response.headers["X-Request-Id"] == request_id


def test_a_request_id_is_minted_when_absent(client: TestClient) -> None:
    response = client.get("/v1/_wp3/ok")
    minted = response.headers.get("X-Request-Id")
    assert minted, "a request without an id must still get one back"


def test_minted_request_ids_differ_between_requests(client: TestClient) -> None:
    first = client.get("/v1/_wp3/ok").headers["X-Request-Id"]
    second = client.get("/v1/_wp3/ok").headers["X-Request-Id"]
    assert first != second


def test_the_request_id_is_echoed_on_an_app_error(client: TestClient) -> None:
    request_id = "req-" + uuid.uuid4().hex
    response = client.get("/v1/_wp3/app-error/not_found", headers={"X-Request-Id": request_id})
    assert response.status_code == 404
    assert response.headers["X-Request-Id"] == request_id


def test_the_request_id_is_echoed_on_an_unhandled_exception(client: TestClient) -> None:
    request_id = "req-" + uuid.uuid4().hex
    response = client.get("/v1/_wp3/boom", headers={"X-Request-Id": request_id})
    assert response.status_code == 500
    assert response.headers["X-Request-Id"] == request_id


# ─── The envelope contract itself ─────────────────────────────────────────────


def test_app_error_envelope_is_the_shape_the_handler_must_render() -> None:
    """Pins the shared module the handler renders through, so a drift shows up here first."""
    error = AppError("Something went wrong. Try again.", code="internal_error", status=500)
    assert error.envelope() == {
        "error": {
            "code": "internal_error",
            "message": "Something went wrong. Try again.",
            "details": {},
        }
    }


def test_the_app_is_a_fastapi_instance_with_routes_under_v1(app: FastAPI) -> None:
    paths = {getattr(route, "path", "") for route in app.routes}
    assert any(path.startswith("/v1/") for path in paths)


def test_module_level_app_exists(app: FastAPI) -> None:
    main = importlib.import_module(MAIN_MODULE)
    assert isinstance(main.app, FastAPI)


def test_documents_dir_is_not_served_as_static_files(app: FastAPI) -> None:
    """Documents are handed out through signed URLs, never by mounting the blob root."""
    assert not any(
        str(getattr(route, "path", "")).startswith("/documents") for route in app.routes
    )


def test_no_document_root_leaks_in_an_error_body(client: TestClient) -> None:
    body = client.get("/v1/_wp3/boom").text
    assert str(Path.home()) not in body
