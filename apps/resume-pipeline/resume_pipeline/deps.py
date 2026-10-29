"""FastAPI dependencies: identity, connection, blob store (RG-004, D102).

This service binds to `127.0.0.1` and is never internet-reachable. Ascend holds the Cloudflare
Access identity and is the only client; it presents a shared service token and names the resolved
user in `X-Ascend-User`. So the identity assertion is trusted here — but only as far as *which*
user, never as far as *whether* to scope: every repository still carries `user_id = $n`, because
a bug in ascend must not become a cross-tenant read.

A wrong token and a bad user header produce the **same** 403 with the **same** sentence. Two
different answers would let a caller ask "was my token right?" and "does this user exist?"
separately, which is one question more than an unauthenticated caller should get answered.
"""

from __future__ import annotations

import hmac
import re
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, Header

from resume_pipeline.db import connection
from resume_pipeline.errors import Forbidden
from resume_pipeline.settings import Settings, get_settings
from resume_pipeline.storage.base import BlobStore
from resume_pipeline.storage.local import LocalBlobStore

_UUID_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)

#: One sentence for both failure modes. Do not specialise it.
_REFUSED = (
    "This request was refused because the caller is not recognised. "
    "Check the service credentials and try again."
)

_BEARER = "bearer "


def _presented_token(authorization: str | None) -> str:
    if not authorization:
        return ""
    if not authorization.lower().startswith(_BEARER):
        return ""
    return authorization[len(_BEARER) :].strip()


def verify_service_token(authorization: str | None, settings: Settings) -> None:
    presented = _presented_token(authorization)
    expected = settings.service_token
    # compare_digest on both halves, and only after the scheme check, so a token is never
    # compared with `==`.
    if not presented or not hmac.compare_digest(presented, expected):
        raise Forbidden(_REFUSED)


async def current_user_id(
    authorization: Annotated[str | None, Header()] = None,
    x_ascend_user: Annotated[str | None, Header()] = None,
) -> str:
    settings = get_settings()
    verify_service_token(authorization, settings)
    if not x_ascend_user or not _UUID_PATTERN.match(x_ascend_user):
        raise Forbidden(_REFUSED)
    return x_ascend_user


async def db_connection() -> AsyncIterator[Any]:
    async with connection() as conn:
        yield conn


def blob_store() -> BlobStore:
    settings = get_settings()
    return LocalBlobStore(Path(settings.documents_dir), url_secret=settings.document_url_secret)


CurrentUserId = Annotated[str, Depends(current_user_id)]
DbConnection = Annotated[Any, Depends(db_connection)]
Blobs = Annotated[BlobStore, Depends(blob_store)]
