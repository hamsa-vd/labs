"""Tectonic compile service (RG-035, decision D2).

Two routes, no state, no database, no knowledge of users. It receives a `.tex`, runs Tectonic in a
throwaway directory on tmpfs, and returns either the PDF bytes or a one-sentence description of
what went wrong.

The `.tex` arriving here is untrusted. Hardening is in three layers and all three are required:

1. the macro denylist the API applies before a request is ever sent
   (`resume_pipeline.latex.validate`);
2. `--untrusted`, which disables shell escape and external programs inside the engine, plus
   `--only-cached`, which forbids the engine from reaching the network for a package — the cache
   is pre-warmed into the image precisely so it never needs to;
3. the container constraints in `docker-compose.dev.yml`: read-only root filesystem, tmpfs
   scratch, all capabilities dropped, non-root user, 512 MB, 1 CPU.

The subprocess gets its own session so a wall-clock timeout can kill the whole process group, and
a closed stdin so nothing can ever block waiting for input.
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import re
import shutil
import signal
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from parse_log import page_count, parse_log

MAX_TEX_BYTES = 200 * 1024
COMPILE_TIMEOUT_SECONDS = 20.0
SCRATCH_ROOT = "/tmp"
JOB_NAME = "resume"

app = FastAPI(title="resume-latex", docs_url=None, redoc_url=None, openapi_url=None)

_tectonic_version: str | None = None


def _envelope(code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "details": details or {}}}


def _read_version() -> str:
    """Tectonic's version string, resolved once and cached."""
    global _tectonic_version
    if _tectonic_version is not None:
        return _tectonic_version
    try:
        completed = subprocess.run(
            ["tectonic", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
            stdin=subprocess.DEVNULL,
        )
        raw = (completed.stdout or completed.stderr or "").strip()
    except (OSError, subprocess.SubprocessError):
        raw = ""
    match = re.search(r"\d+\.\d+\.\d+", raw)
    _tectonic_version = match.group(0) if match else (raw or "unknown")
    return _tectonic_version


class CompileRequest(BaseModel):
    tex: str
    passes: int = Field(default=2, ge=1, le=5)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "tectonic": _read_version()}


async def _run_tectonic(work: Path, source: Path, passes: int) -> tuple[int, str, bool]:
    """Run one compile. Returns (returncode, stderr text, timed_out)."""
    command = [
        "tectonic",
        "-X",
        "compile",
        "--untrusted",
        "--only-cached",
        "--keep-logs",
        "--reruns",
        str(max(passes - 1, 0)),
        "--outdir",
        str(work),
        str(source),
    ]
    process = await asyncio.create_subprocess_exec(
        *command,
        cwd=str(work),
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        # Its own session, so the timeout can take down the engine and anything it spawned.
        start_new_session=True,
    )
    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(), timeout=COMPILE_TIMEOUT_SECONDS
        )
    except (TimeoutError, asyncio.TimeoutError):
        _kill_group(process)
        with contextlib.suppress(Exception):
            await asyncio.wait_for(process.wait(), timeout=5)
        return -1, "", True
    text = (stdout or b"").decode("utf-8", "replace") + (stderr or b"").decode("utf-8", "replace")
    return process.returncode or 0, text, False


def _kill_group(process: asyncio.subprocess.Process) -> None:
    if process.returncode is not None:
        return
    with contextlib.suppress(ProcessLookupError, PermissionError, OSError):
        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
    with contextlib.suppress(ProcessLookupError, OSError):
        process.kill()


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


@app.post("/compile")
async def compile_tex(request: CompileRequest) -> Response:
    size = len(request.tex.encode("utf-8"))
    if size > MAX_TEX_BYTES:
        return JSONResponse(
            status_code=413,
            content=_envelope(
                "payload_too_large",
                f"The LaTeX source is {size // 1024} KB, over the {MAX_TEX_BYTES // 1024} KB "
                "limit. Remove unused content and compile again.",
                {"bytes": size, "limit": MAX_TEX_BYTES},
            ),
        )

    started = time.monotonic()
    work = Path(tempfile.mkdtemp(prefix="compile-", dir=SCRATCH_ROOT))
    try:
        source = work / f"{JOB_NAME}.tex"
        source.write_text(request.tex, encoding="utf-8")

        returncode, output, timed_out = await _run_tectonic(work, source, request.passes)
        elapsed_ms = int((time.monotonic() - started) * 1000)
        log = _read_text(work / f"{JOB_NAME}.log")

        if timed_out:
            return JSONResponse(
                status_code=422,
                content=_envelope(
                    "compile_timeout",
                    f"The document did not finish compiling within "
                    f"{int(COMPILE_TIMEOUT_SECONDS)} seconds. Simplify the template and compile "
                    "again.",
                    {"line": None, "log": log or output, "compile_ms": elapsed_ms},
                ),
            )

        pdf_path = work / f"{JOB_NAME}.pdf"
        pdf = pdf_path.read_bytes() if pdf_path.exists() else b""

        if returncode != 0 or not pdf:
            # Tectonic puts the TeX log in `resume.log`; its own diagnostics go to stderr. Either
            # may carry the `! ` line, so both are searched, the log first.
            error = parse_log(log) or parse_log(output)
            message = (
                error.message
                if error
                else "The document could not be compiled. Check the template and compile again."
            )
            return JSONResponse(
                status_code=422,
                content=_envelope(
                    "compile_failed",
                    message,
                    {
                        "line": error.line if error else None,
                        "log": log or output,
                        "compile_ms": elapsed_ms,
                    },
                ),
            )

        # Tectonic reports the page count on stderr; the TeX log carries `Output written on`.
        pages = page_count(log) or page_count(output)
        headers = {"X-Compile-Ms": str(elapsed_ms)}
        if pages is not None:
            headers["X-Page-Count"] = str(pages)
        return Response(content=pdf, media_type="application/pdf", headers=headers)
    finally:
        shutil.rmtree(work, ignore_errors=True)
