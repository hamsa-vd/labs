"""Filesystem blob store (RG-006).

The second of the two layers guarding the document root. `paths.py` validates identifiers before
they are joined; this class resolves the joined result and confirms it is still inside `root`
before every single operation, including the ones that only read. The duplication is deliberate:
this is the class that opens file handles, and it must be correct even when handed a path that
never went through `paths.py` at all.

Writes are atomic — temp file in the destination directory, then `os.replace`. A process killed
mid-write leaves a stray temp file, never a half-written PDF that a `content_hash` says is whole.
"""

from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path

from resume_pipeline.errors import NotFound, ValidationFailed
from resume_pipeline.storage.signed import sign_document_url

_OUTSIDE_ROOT = (
    "That document path is not valid because it points outside the document store. "
    "Check the path and try again."
)

_MISSING = "That document was not found. Generate it again, or check the document id."

DEFAULT_TTL_SECONDS = 60


class LocalBlobStore:
    """`BlobStore` over a directory tree rooted at `root`."""

    def __init__(self, root: Path, *, url_secret: str | None = None) -> None:
        self.root = Path(root).resolve()
        self._url_secret = url_secret

    # -- containment ---------------------------------------------------------------------

    def resolve(self, path: str) -> Path:
        """Resolve `path` under the root, or refuse.

        `Path.joinpath` with an absolute right-hand side discards the root entirely, and a
        relative path with enough `..` walks out of it, so the check is on the *resolved*
        result rather than on the input string.
        """
        if not isinstance(path, str) or not path.strip():
            raise ValidationFailed(_OUTSIDE_ROOT, details={"field": "path"})
        candidate = (self.root / path).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise ValidationFailed(_OUTSIDE_ROOT, details={"field": "path"})
        if candidate == self.root:
            raise ValidationFailed(_OUTSIDE_ROOT, details={"field": "path"})
        return candidate

    # -- protocol ------------------------------------------------------------------------

    async def put(self, path: str, data: bytes, content_type: str) -> str:
        target = self.resolve(path)
        await asyncio.to_thread(self._write_atomic, target, data)
        return path

    async def get(self, path: str) -> bytes:
        target = self.resolve(path)
        try:
            return await asyncio.to_thread(target.read_bytes)
        except (FileNotFoundError, IsADirectoryError, NotADirectoryError) as exc:
            raise NotFound(_MISSING) from exc

    async def signed_url(self, path: str, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> str:
        # Validate first: a token must never be minted for a path this store would refuse.
        self.resolve(path)
        return sign_document_url(path, ttl_seconds, self._secret())

    async def delete(self, path: str) -> None:
        target = self.resolve(path)
        # A delete that finds nothing has already achieved what the caller asked for.
        await asyncio.to_thread(self._unlink_quietly, target)

    async def exists(self, path: str) -> bool:
        target = self.resolve(path)
        return await asyncio.to_thread(target.is_file)

    # -- internals -----------------------------------------------------------------------

    def _secret(self) -> str:
        if self._url_secret is not None:
            return self._url_secret
        from resume_pipeline.settings import get_settings

        return get_settings().document_url_secret

    @staticmethod
    def _write_atomic(target: Path, data: bytes) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        handle, temp_name = tempfile.mkstemp(dir=target.parent, prefix=".tmp-")
        try:
            with os.fdopen(handle, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_name, target)
        except BaseException:
            Path(temp_name).unlink(missing_ok=True)
            raise

    @staticmethod
    def _unlink_quietly(target: Path) -> None:
        try:
            target.unlink(missing_ok=True)
        except IsADirectoryError:
            return
