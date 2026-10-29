"""Signed document tokens (RG-006, D102).

Ascend redeems these. The token carries the storage path and an absolute expiry, authenticated
with HMAC-SHA256 over both, encoded URL-safe base64 so it survives a query string unescaped.

Three properties are load-bearing:

**One message for every failure.** A bad signature, an expired token and a token that is not
base64 at all all raise `Forbidden` with the same sentence. Distinguishable failures turn the
redemption route into an oracle: an attacker learns that a path exists, or that a signature was
the only thing wrong, and tunes the next attempt accordingly.

**Constant-time comparison.** `==` on a digest leaks its prefix through timing.

**`now` is injectable.** Expiry is then testable without a sleep, and a test that sleeps for a
TTL is a test somebody eventually shortens the TTL to avoid.
"""

from __future__ import annotations

import base64
import binascii
import hmac
import time
from hashlib import sha256

from resume_pipeline.errors import Forbidden

_DIGEST_SIZE = 32

#: Deliberately identical for every failure mode. Do not specialise it.
_REJECTED = "That document link is not valid or has expired. Open the document again to get a new link."


def _digest(secret: str, raw: bytes) -> bytes:
    return hmac.new(secret.encode("utf-8"), raw, sha256).digest()


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def sign_document_url(path: str, ttl_seconds: int, secret: str, *, now: int | None = None) -> str:
    """Mint a token for `path`, valid for `ttl_seconds` from `now`."""
    issued = int(time.time()) if now is None else int(now)
    expires = issued + int(ttl_seconds)
    raw = f"{expires}:{path}".encode()
    return _b64encode(raw + _digest(secret, raw))


def verify_document_token(token: str, secret: str, *, now: int | None = None) -> str:
    """Return the path the token authorises, or raise `Forbidden`.

    The signature is verified before the expiry is even parsed, so an unsigned token cannot
    reveal how expiry is encoded.
    """
    if not isinstance(token, str) or not token:
        raise Forbidden(_REJECTED)
    try:
        blob = _b64decode(token)
    except (binascii.Error, ValueError) as exc:
        raise Forbidden(_REJECTED) from exc
    if len(blob) <= _DIGEST_SIZE:
        raise Forbidden(_REJECTED)

    raw, signature = blob[:-_DIGEST_SIZE], blob[-_DIGEST_SIZE:]
    if not hmac.compare_digest(signature, _digest(secret, raw)):
        raise Forbidden(_REJECTED)

    try:
        expires_text, path = raw.decode("utf-8").split(":", 1)
        expires = int(expires_text)
    except (UnicodeDecodeError, ValueError) as exc:
        raise Forbidden(_REJECTED) from exc
    if not path:
        raise Forbidden(_REJECTED)

    current = int(time.time()) if now is None else int(now)
    if current >= expires:
        raise Forbidden(_REJECTED)
    return path
