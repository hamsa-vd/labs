"""`resume_pipeline.deps` and `/v1/health` (WP3 §7, acceptance criterion 11).

This service binds to loopback and trusts ascend's identity assertion, which makes the service
token the whole perimeter. Two properties follow.

**Nothing but `/v1/health` is reachable without it.** The sweep below walks the app's own route
table rather than a hand-written list, so a router added in a later work package is covered the day
it is mounted and a forgotten dependency shows up as a failure here.

**A refusal says nothing about which half failed.** A wrong token, an absent token, a missing
`X-Ascend-User` and a malformed one all render the identical envelope. Otherwise the endpoint is an
oracle: an attacker with a guessed token learns it was the *user* header that was wrong, which is
the same as learning the token was right.

This module does not use `from __future__ import annotations`: FastAPI resolves `Annotated[...,
Depends(...)]` on the probe routes below at registration time, and those annotations reference the
lazily imported `deps` module through a closure that a deferred annotation cannot see.
"""

import importlib
import os
import sys
import uuid
from collections.abc import Iterator
from typing import Annotated, Any

import pytest
from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient

MAIN_MODULE = "resume_pipeline.main"
DEPS_MODULE = "resume_pipeline.deps"

SERVICE_TOKEN = "service-token-for-tests-4f0c9a2e"
WRONG_TOKEN = "service-token-for-tests-4f0c9a2f"
USER_ID = "11111111-1111-4111-8111-111111111111"

BLOB_STORE_METHODS = ("put", "get", "signed_url", "delete", "exists")

# Paths this suite mounts itself; they are not part of the service's surface.
PROBE_PREFIX = "/v1/_wp3"

OPEN_PATHS = {"/v1/health"}


def _purge_resume_pipeline_modules() -> None:
    for name in list(sys.modules):
        if name.startswith("resume_pipeline.") and name != "resume_pipeline.errors":
            sys.modules.pop(name, None)


@pytest.fixture(scope="module")
def modules(tmp_path_factory: pytest.TempPathFactory) -> Iterator[tuple[Any, Any]]:
    documents = tmp_path_factory.mktemp("documents")
    env = {
        "RESUME_DATABASE_URL": "postgres://user:pass@127.0.0.1:5432/nowhere",
        "RESUME_SERVICE_TOKEN": SERVICE_TOKEN,
        "RESUME_DOCUMENTS_DIR": str(documents),
        "RESUME_DOCUMENT_URL_SECRET": "url-signing-secret",
        "RESUME_MASTER_KEY": "EREREREREREREREREREREREREREREREREREREREREQ=",
    }
    previous = {key: os.environ.get(key) for key in env}
    os.environ.update(env)
    _purge_resume_pipeline_modules()

    try:
        main = importlib.import_module(MAIN_MODULE)
        deps = importlib.import_module(DEPS_MODULE)
    except ModuleNotFoundError as exc:  # pragma: no cover - only before WP3 source lands
        pytest.fail(f"WP3 has not provided that module yet ({exc}).", pytrace=False)

    yield main, deps

    for key, value in previous.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    _purge_resume_pipeline_modules()


@pytest.fixture(scope="module")
def deps(modules: tuple[Any, Any]) -> Any:
    return modules[1]


@pytest.fixture(scope="module")
def app(modules: tuple[Any, Any]) -> FastAPI:
    main, deps_module = modules
    instance: FastAPI = main.create_app()

    probe = APIRouter()

    @probe.get("/_wp3/whoami")
    async def _whoami(
        user_id: Annotated[str, Depends(deps_module.current_user_id)],
    ) -> dict[str, str]:
        return {"user_id": user_id}

    @probe.get("/_wp3/blob-store")
    async def _blob_store(
        store: Annotated[Any, Depends(deps_module.blob_store)],
    ) -> dict[str, bool]:
        return {method: callable(getattr(store, method, None)) for method in BLOB_STORE_METHODS}

    instance.include_router(probe, prefix="/v1")
    return instance


@pytest.fixture(scope="module")
def client(app: FastAPI) -> TestClient:
    # No lifespan: this suite may not open a socket.
    return TestClient(app, raise_server_exceptions=False)


def _auth(token: str = SERVICE_TOKEN) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _full_headers() -> dict[str, str]:
    return {**_auth(), "X-Ascend-User": USER_ID}


# ─── The dependency accepts a good caller ─────────────────────────────────────


def test_a_valid_token_and_user_resolves_the_user_id(client: TestClient) -> None:
    response = client.get(f"{PROBE_PREFIX}/whoami", headers=_full_headers())

    assert response.status_code == 200
    assert response.json() == {"user_id": USER_ID}


def test_any_valid_uuid_user_is_accepted(client: TestClient) -> None:
    other = str(uuid.uuid4())
    response = client.get(
        f"{PROBE_PREFIX}/whoami", headers={**_auth(), "X-Ascend-User": other}
    )
    assert response.status_code == 200
    assert response.json()["user_id"] == other


# ─── Every way of getting it wrong, and they all look the same ────────────────

REFUSAL_CASES: list[tuple[str, dict[str, str]]] = [
    ("no headers at all", {}),
    ("no authorization header", {"X-Ascend-User": USER_ID}),
    ("wrong token", {**_auth(WRONG_TOKEN), "X-Ascend-User": USER_ID}),
    ("empty token", {**_auth(""), "X-Ascend-User": USER_ID}),
    ("token without the bearer scheme", {"Authorization": SERVICE_TOKEN,
                                         "X-Ascend-User": USER_ID}),
    ("basic auth instead", {"Authorization": "Basic c2VydmljZTp0b2tlbg==",
                            "X-Ascend-User": USER_ID}),
    ("valid token, no user header", _auth()),
    ("valid token, empty user header", {**_auth(), "X-Ascend-User": ""}),
    ("valid token, non-uuid user", {**_auth(), "X-Ascend-User": "not-a-uuid"}),
    ("valid token, sql-ish user", {**_auth(), "X-Ascend-User": "1 or 1=1"}),
    ("valid token, truncated uuid", {**_auth(), "X-Ascend-User": USER_ID[:-1]}),
]


@pytest.mark.parametrize(
    ("label", "headers"), REFUSAL_CASES, ids=[label for label, _ in REFUSAL_CASES]
)
def test_a_bad_caller_is_forbidden(
    client: TestClient, label: str, headers: dict[str, str]
) -> None:
    response = client.get(f"{PROBE_PREFIX}/whoami", headers=headers)

    assert response.status_code == 403, label
    assert response.json()["error"]["code"] == "forbidden", label


def test_every_refusal_is_indistinguishable(client: TestClient) -> None:
    """A different message for a wrong token than for a bad user makes this an oracle."""
    bodies = {
        label: client.get(f"{PROBE_PREFIX}/whoami", headers=headers).json()
        for label, headers in REFUSAL_CASES
    }
    distinct = {repr(body) for body in bodies.values()}
    assert len(distinct) == 1, f"the refusals can be told apart: {bodies}"


def test_the_refusal_leaks_neither_token_nor_user(client: TestClient) -> None:
    body = client.get(f"{PROBE_PREFIX}/whoami", headers={}).text
    assert SERVICE_TOKEN not in body
    assert USER_ID not in body
    assert "X-Ascend-User" not in body
    assert "Authorization" not in body


def test_the_refusal_message_is_a_sentence(client: TestClient) -> None:
    message = client.get(f"{PROBE_PREFIX}/whoami", headers={}).json()["error"]["message"]
    assert message.strip()
    assert "!" not in message


# ─── Criterion 11: the route table ────────────────────────────────────────────


def _guarded_get_routes(app: FastAPI) -> list[str]:
    paths = []
    for route in app.routes:
        path = str(getattr(route, "path", ""))
        methods = set(getattr(route, "methods", set()) or set())
        if not path.startswith("/v1/") or path.startswith(PROBE_PREFIX):
            continue
        if path in OPEN_PATHS or "GET" not in methods:
            continue
        paths.append(path)
    return paths


def _fill(path: str) -> str:
    out = []
    for segment in path.split("/"):
        out.append(str(uuid.uuid4()) if segment.startswith("{") else segment)
    return "/".join(out)


def test_health_is_mounted_under_v1(app: FastAPI) -> None:
    assert "/v1/health" in {str(getattr(route, "path", "")) for route in app.routes}


def test_health_answers_without_a_service_token(client: TestClient) -> None:
    response = client.get("/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"status", "version", "db"}
    assert body["status"] in {"ok", "degraded"}
    assert body["db"] in {"ok", "degraded"}
    assert isinstance(body["version"], str) and body["version"]


def test_health_also_answers_with_a_service_token(client: TestClient) -> None:
    assert client.get("/v1/health", headers=_full_headers()).status_code == 200


def test_health_leaks_no_connection_string(client: TestClient) -> None:
    body = client.get("/v1/health").text
    assert "postgres://" not in body
    assert SERVICE_TOKEN not in body


def test_every_other_get_route_refuses_without_the_token(
    app: FastAPI, client: TestClient
) -> None:
    for path in _guarded_get_routes(app):
        response = client.get(_fill(path))
        assert response.status_code == 403, f"{path} answered {response.status_code} unauthenticated"
        assert response.json()["error"]["code"] == "forbidden", path


def test_every_other_get_route_refuses_a_wrong_token(app: FastAPI, client: TestClient) -> None:
    for path in _guarded_get_routes(app):
        response = client.get(
            _fill(path), headers={**_auth(WRONG_TOKEN), "X-Ascend-User": USER_ID}
        )
        assert response.status_code == 403, path


# ─── The other two dependencies ───────────────────────────────────────────────


def test_deps_provides_the_three_dependencies(deps: Any) -> None:
    for name in ("current_user_id", "db_connection", "blob_store"):
        assert callable(getattr(deps, name, None)), f"deps.{name} is missing"


def test_blob_store_dependency_injects_something_implementing_the_protocol(
    client: TestClient,
) -> None:
    response = client.get(f"{PROBE_PREFIX}/blob-store")

    assert response.status_code == 200
    assert response.json() == dict.fromkeys(BLOB_STORE_METHODS, True)
