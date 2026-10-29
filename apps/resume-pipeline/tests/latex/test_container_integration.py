"""The compiler container, driven for real (WP7 §3, acceptance criteria 1, 2, 7 and 10).

Everything here needs a running `ascend-rg-latex`, so everything here skips cleanly without one:

    docker compose -f docker-compose.dev.yml up -d latex
    RESUME_LATEX_URL=http://127.0.0.1:58080 uv run pytest tests/latex -q

These are the only tests in the repository allowed to open a socket, hence the `network` marker
that lifts the suite-wide guard from `tests/conftest.py`. They talk to 127.0.0.1 and nothing else.

The timeout test deliberately sends a document that never terminates. It gives itself a much
larger budget than the service's 20 second limit so that a *hang* fails loudly instead of stalling
the whole suite behind a socket read.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import httpx
import pytest

from tests.latex.conftest import seed_template_paths

pytestmark = pytest.mark.network

# The service caps itself at 20 seconds. Anything beyond this is a hang, not a slow compile.
SERVICE_TIMEOUT_SECONDS = 20
TEST_BUDGET_SECONDS = 45
CLIENT_TIMEOUT_SECONDS = 90

# A document that loops forever without growing TeX's memory, so it cannot exit early by
# exhausting capacity. Only the wall-clock timeout can stop it.
INFINITE_LOOP_TEX = (
    "\\documentclass[11pt]{article}\n"
    "\\newcount\\spin\n"
    "\\spin=0\n"
    "\\begin{document}\n"
    "\\loop\\advance\\spin by 0\\ifnum\\spin<1\\repeat\n"
    "This line is never reached.\n"
    "\\end{document}\n"
)

# `\resumeHeading` is never defined, so Tectonic reports an undefined control sequence at line 5.
BROKEN_TEX_ERROR_LINE = 5
BROKEN_TEX = (
    "\\documentclass[11pt]{article}\n"
    "\\begin{document}\n"
    "Senior backend engineer.\n"
    "\n"
    "\\resumeHeading{Liv-ex}{London, UK}\n"
    "\\end{document}\n"
)


@pytest.fixture
def service(latex_service_url: str) -> Iterator[httpx.Client]:
    with httpx.Client(base_url=latex_service_url, timeout=CLIENT_TIMEOUT_SECONDS) as client:
        yield client


def envelope_of(response: httpx.Response) -> dict[str, Any]:
    body = response.json()
    assert "error" in body, f"A failure must use the shared error envelope, got {body!r}."
    return dict(body["error"])


# ─── Health ───────────────────────────────────────────────────────────────────


def test_health_reports_the_tectonic_version(service: httpx.Client) -> None:
    response = service.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["tectonic"], "The health check must name the Tectonic build actually installed."


# ─── A real template compiles ─────────────────────────────────────────────────


@pytest.mark.parametrize("template", seed_template_paths(), ids=lambda p: p.stem)
def test_a_seeded_template_compiles_to_a_pdf(service: httpx.Client, template: Path) -> None:
    """Acceptance criterion 1. If a shipped template cannot compile in the image, the package
    cache in `warmup.tex` is missing something and every run using it will fail."""
    response = service.post("/compile", json={"tex": template.read_text(encoding="utf-8")})

    assert response.status_code == 200, f"{template.name} failed: {response.text[:800]}"
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.content.startswith(b"%PDF-"), "The response body must be a PDF."
    assert b"%%EOF" in response.content[-2048:]

    pages = int(response.headers["X-Page-Count"])
    assert pages >= 1, "A resume with no pages is not a plausible page count."
    assert pages <= 4, f"{template.name} produced {pages} pages, which is not a resume."
    assert int(response.headers["X-Compile-Ms"]) >= 0


def test_a_single_page_template_produces_one_page(service: httpx.Client) -> None:
    """The `single_page__` prefix is a promise made to the template selector in WP4."""
    template = next(p for p in seed_template_paths() if p.stem.startswith("single_page__"))
    response = service.post("/compile", json={"tex": template.read_text(encoding="utf-8")})

    assert response.status_code == 200
    assert int(response.headers["X-Page-Count"]) == 1


# ─── A broken document ────────────────────────────────────────────────────────


def test_a_broken_document_returns_the_line_and_a_one_sentence_message(
    service: httpx.Client,
) -> None:
    """Acceptance criterion 2. The full log is present, but not in the message."""
    response = service.post("/compile", json={"tex": BROKEN_TEX})

    assert response.status_code == 422
    error = envelope_of(response)
    assert error["code"] == "compile_failed"
    assert error["details"]["line"] == BROKEN_TEX_ERROR_LINE, (
        f"Expected the undefined control sequence at line {BROKEN_TEX_ERROR_LINE}, "
        f"got {error['details']['line']}."
    )

    message = error["message"]
    assert "\n" not in message.strip(), f"The message must be one sentence, got {message!r}."
    assert len(message) <= 200

    log = error["details"]["log"]
    assert "Undefined control sequence" in log
    assert len(log) > len(message), "The full log belongs in details, not in the message."
    assert log not in message


def test_a_broken_document_does_not_leak_the_source_into_the_message(
    service: httpx.Client,
) -> None:
    secret = "Architected a Kafka pipeline for Liv-ex settlement"
    tex = BROKEN_TEX.replace("Senior backend engineer.", secret)

    response = service.post("/compile", json={"tex": tex})

    assert response.status_code == 422
    assert secret not in envelope_of(response)["message"]


# ─── The timeout ──────────────────────────────────────────────────────────────


def test_an_infinite_loop_is_killed_by_the_timeout(service: httpx.Client) -> None:
    """Acceptance criterion 7. A document that never terminates must not hold a worker forever.

    The client budget is well above the service's own 20 seconds so that a genuine hang shows up
    as a failed assertion here rather than a stalled suite.
    """
    started = time.monotonic()
    response = service.post("/compile", json={"tex": INFINITE_LOOP_TEX})
    elapsed = time.monotonic() - started

    assert elapsed < TEST_BUDGET_SECONDS, (
        f"The compile ran for {elapsed:.1f}s. The service must kill it at "
        f"{SERVICE_TIMEOUT_SECONDS}s."
    )
    assert response.status_code == 422
    error = envelope_of(response)
    assert error["code"] == "compile_timeout", (
        f"A timeout is distinguishable from a TeX error, got {error['code']!r}."
    )
    assert error["message"]
    assert "\n" not in error["message"].strip()


def test_the_service_still_answers_after_a_timeout(service: httpx.Client) -> None:
    """A killed process group must not leave the worker or the tmpfs scratch wedged."""
    service.post("/compile", json={"tex": INFINITE_LOOP_TEX})

    response = service.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# ─── Input limits ─────────────────────────────────────────────────────────────


def test_a_source_over_two_hundred_kilobytes_is_refused(service: httpx.Client) -> None:
    oversized = (
        "\\documentclass[11pt]{article}\n"
        "\\begin{document}\n" + ("% padding\n" * 25000) + "\\end{document}\n"
    )
    assert len(oversized.encode("utf-8")) > 200 * 1024

    response = service.post("/compile", json={"tex": oversized})

    assert response.status_code == 413


# ─── The sandbox ──────────────────────────────────────────────────────────────


def docker_inspect(container: str) -> dict[str, Any]:
    if shutil.which("docker") is None:
        pytest.skip("Docker is not available on this machine.")
    probe = subprocess.run(
        ["docker", "inspect", container],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if probe.returncode != 0:
        pytest.skip(f"Container {container} is not running: {probe.stderr.strip()[:200]}")
    parsed = json.loads(probe.stdout)
    assert parsed, f"docker inspect {container} returned nothing."
    return dict(parsed[0])


def test_the_container_root_filesystem_is_read_only(latex_container_name: str) -> None:
    """Acceptance criterion 10, layer three of the defence. Untrusted LaTeX runs in here."""
    inspected = docker_inspect(latex_container_name)

    assert inspected["HostConfig"]["ReadonlyRootfs"] is True, (
        "The root filesystem must be read only. A writable root undoes the sandbox."
    )


def test_the_container_runs_as_a_non_root_user(latex_container_name: str) -> None:
    inspected = docker_inspect(latex_container_name)

    user = str(inspected["Config"]["User"] or "")
    assert user, "The container must declare a user; an empty value means root."
    uid = user.split(":")[0]
    assert uid not in ("0", "root"), f"The container runs as {user!r}."
    assert uid.isdigit() and int(uid) != 0


def test_the_container_drops_every_capability(latex_container_name: str) -> None:
    inspected = docker_inspect(latex_container_name)

    dropped = [capability.upper() for capability in (inspected["HostConfig"]["CapDrop"] or [])]
    assert "ALL" in dropped, f"Expected every capability dropped, got {dropped}."


def test_the_container_scratch_space_is_a_tmpfs(latex_container_name: str) -> None:
    """Compiles write to /tmp. With a read-only root that has to be a tmpfs, or nothing works."""
    inspected = docker_inspect(latex_container_name)

    tmpfs = inspected["HostConfig"]["Tmpfs"] or {}
    assert "/tmp" in tmpfs, f"Expected a tmpfs at /tmp, got {tmpfs}."


def test_the_container_memory_and_cpu_are_capped(latex_container_name: str) -> None:
    """A compile that allocates without bound must starve itself, not the host."""
    host = docker_inspect(latex_container_name)["HostConfig"]

    assert 0 < host["Memory"] <= 512 * 1024 * 1024, f"Memory cap is {host['Memory']} bytes."
    cpus = host.get("NanoCpus") or 0
    quota, period = host.get("CpuQuota") or 0, host.get("CpuPeriod") or 0
    effective = cpus / 1_000_000_000 if cpus else (quota / period if quota and period else 0)
    assert 0 < effective <= 1.0, f"CPU cap is {effective}."


def test_the_container_cannot_reach_the_network(latex_container_name: str) -> None:
    """The package cache is baked into the image precisely so a compile never reaches out.

    With egress open, Tectonic silently downloads whatever `warmup.tex` missed. That turns a
    reproducible image into one whose behaviour depends on the internet, and it hands untrusted
    LaTeX a channel out of the sandbox.
    """
    if shutil.which("docker") is None:
        pytest.skip("Docker is not available on this machine.")

    probe = subprocess.run(
        [
            "docker",
            "exec",
            latex_container_name,
            "python3",
            "-c",
            "import socket,sys\n"
            "try:\n"
            "    socket.create_connection(('1.1.1.1', 443), timeout=3).close()\n"
            "    sys.stdout.write('reachable')\n"
            "except OSError:\n"
            "    sys.stdout.write('blocked')\n",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if probe.returncode != 0 and "blocked" not in probe.stdout:
        pytest.skip(f"Could not probe {latex_container_name}: {probe.stderr.strip()[:200]}")

    assert probe.stdout.strip() == "blocked", (
        "The compiler container can reach the internet. The image ships a pre-warmed package "
        "cache so that it does not need to, and untrusted LaTeX runs in here."
    )


def test_the_container_cannot_gain_new_privileges(latex_container_name: str) -> None:
    inspected = docker_inspect(latex_container_name)

    options = inspected["HostConfig"]["SecurityOpt"] or []
    assert any("no-new-privileges" in option for option in options), (
        f"Expected no-new-privileges, got {options}."
    )
