"""The FastAPI application (RG-004).

Three things are worth stating outright.

**One error shape.** Every `AppError` renders through `.envelope()` at its own status, so a client
switches on `error.code` and never has to parse prose. An unhandled exception renders as
`internal_error` with a fixed sentence — never a stack trace, never the exception's own message,
because that message is where a DSN, a file path, or a fragment of a resume ends up.

**One request id.** The middleware accepts `X-Request-Id` or mints one, binds it to the log
context for the life of the request, and echoes it in the response header. That echo is what lets
a user paste an id from an ascend error into a search of this service's logs.

**Bound to loopback.** Ascend is the only client; there is no public ingress. The service token in
`deps.py` is what stops another process on the same machine from calling it.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.responses import Response

from resume_pipeline.db import close_pool
from resume_pipeline.errors import AppError
from resume_pipeline.logging import bind_request, clear_request, configure_logging
from resume_pipeline.routers import health
from resume_pipeline.settings import get_settings

REQUEST_ID_HEADER = "X-Request-Id"

API_PREFIX = "/v1"

_INTERNAL = (
    "Something went wrong on the resume service, so the request did not complete. "
    "Try again; if it keeps happening, quote the request id."
)

log = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    await close_pool()


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title="Resume pipeline",
        version="0.1.0",
        docs_url="/docs",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    @app.middleware("http")
    async def request_id_middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        clear_request()
        bind_request(request_id)
        request.state.request_id = request_id
        try:
            response = await call_next(request)
        finally:
            clear_request()
        response.headers[REQUEST_ID_HEADER] = request_id
        return response

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        log.info(
            "request.failed",
            code=exc.code,
            status=exc.status,
            path=request.url.path,
            request_id=request_id,
        )
        response = JSONResponse(status_code=exc.status, content=exc.envelope())
        if request_id:
            response.headers[REQUEST_ID_HEADER] = request_id
        return response

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        # `exc_info` goes to the log, where the redaction processor can see it. It never goes
        # into the body: the exception's own message is untrusted text from this service's
        # internals, and the caller has the request id to correlate with.
        # `request_id` is passed rather than relied on from the log context: Starlette runs
        # this handler in its server-error middleware, which sits outside the middleware that
        # binds the context, so by now the context has already been cleared.
        log.error(
            "request.unhandled", path=request.url.path, request_id=request_id, exc_info=exc
        )
        response = JSONResponse(
            status_code=500,
            content={"error": {"code": "internal_error", "message": _INTERNAL, "details": {}}},
        )
        if request_id:
            response.headers[REQUEST_ID_HEADER] = request_id
        return response

    app.include_router(health.router, prefix=API_PREFIX)
    return app


app = create_app()
