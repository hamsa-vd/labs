"""The blob store protocol (RG-006, D1).

Blobs live on the Mac Mini today. The protocol exists so that moving them to S3 or Supabase
Storage is one new class and no change to a caller: every consumer is typed against `BlobStore`,
not against `LocalBlobStore`.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class BlobStore(Protocol):
    async def put(self, path: str, data: bytes, content_type: str) -> str: ...

    async def get(self, path: str) -> bytes: ...

    async def signed_url(self, path: str, ttl_seconds: int = 60) -> str: ...

    async def delete(self, path: str) -> None: ...

    async def exists(self, path: str) -> bool: ...
