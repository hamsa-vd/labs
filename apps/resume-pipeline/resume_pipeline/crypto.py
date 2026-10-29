"""Envelope encryption for BYOK provider keys (RG-023).

Two functions, and deliberately only two. A `get_data_key` helper would be convenient exactly
once and a leak surface forever, so the derived key never leaves this module.

Shape:

* the master key is 32 raw bytes, carried in settings as base64;
* the data key is derived per user with HKDF-SHA256 using the user id as `info`, so a ciphertext
  sealed for user A cannot be opened as user B even with the same master key;
* the payload is AES-256-GCM with a fresh 12-byte nonce per seal, so sealing the same key twice
  gives different bytes;
* the stored form is `nonce || tag || payload`, which is what goes into the `bytea` column.

`open_sealed` raises `Forbidden` with one message for every authentication failure. Saying which
part was wrong — wrong user, wrong ciphertext, wrong master key — would turn the error into an
oracle.
"""

from __future__ import annotations

import base64
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from resume_pipeline.errors import Forbidden

#: AES-256 needs a 32-byte key; anything else is a misconfiguration, not a shorter key.
MASTER_KEY_BYTES = 32
NONCE_BYTES = 12
TAG_BYTES = 16

#: A constant salt. HKDF's security here comes from the master key and the per-user `info`; a
#: random salt would have to be stored alongside every ciphertext to be usable.
_HKDF_SALT = b"resume-pipeline/byok/v1"

class MasterKeyError(ValueError, RuntimeError):
    """Raised at load when the master key is absent or is not exactly 32 decoded bytes.

    It derives from both `ValueError` and `RuntimeError`, mirroring `settings.MissingSettings`:
    this is a configuration failure, and callers reasonably reach for either. It is an exception
    type rather than a third function — the module still exposes exactly `seal` and `open_sealed`,
    because every extra way to touch a key is another place one can leak.
    """


#: The one message any authentication failure produces.
_OPEN_FAILED = (
    "That stored key could not be opened for this account. Delete the key and add it again."
)


def seal(user_id: str, plaintext: str, *, master_key: bytes | None = None) -> bytes:
    """Encrypt `plaintext` for `user_id`. Returns `nonce || tag || payload`."""
    key = _data_key(user_id, _resolve_master_key(master_key))
    nonce = os.urandom(NONCE_BYTES)
    sealed = AESGCM(key).encrypt(nonce, plaintext.encode("utf-8"), None)
    # `cryptography` returns payload||tag; the stored layout puts the tag first.
    payload, tag = sealed[:-TAG_BYTES], sealed[-TAG_BYTES:]
    return nonce + tag + payload


def open_sealed(user_id: str, ciphertext: bytes, *, master_key: bytes | None = None) -> str:
    """Decrypt a `seal` result for `user_id`, or raise `Forbidden`.

    The master key is resolved before the try block on purpose: a missing or malformed master key
    is an operator misconfiguration and must surface as one, not as a user-facing `Forbidden`.
    """
    resolved = _resolve_master_key(master_key)
    try:
        blob = bytes(ciphertext)
        if len(blob) <= NONCE_BYTES + TAG_BYTES:
            raise InvalidTag
        nonce = blob[:NONCE_BYTES]
        tag = blob[NONCE_BYTES : NONCE_BYTES + TAG_BYTES]
        payload = blob[NONCE_BYTES + TAG_BYTES :]
        opened = AESGCM(_data_key(user_id, resolved)).decrypt(nonce, payload + tag, None)
        return opened.decode("utf-8")
    except Exception as exc:
        # Every failure — wrong user, truncated blob, tampered tag, rotated master key — leaves by
        # the same door with the same words.
        raise Forbidden(_OPEN_FAILED) from exc


# ─── Internals ────────────────────────────────────────────────────────────────


def _data_key(user_id: str, master_key: bytes) -> bytes:
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=MASTER_KEY_BYTES,
        salt=_HKDF_SALT,
        info=user_id.encode("utf-8"),
    )
    return hkdf.derive(master_key)


def _resolve_master_key(master_key: bytes | None) -> bytes:
    """Return the 32-byte master key, raising `MasterKeyError` when it is not exactly that."""
    if master_key is not None:
        return _require_32_bytes(master_key)
    return _require_32_bytes(_decode_master_key(_configured_master_key()))


def _require_32_bytes(key: bytes) -> bytes:
    if len(key) != MASTER_KEY_BYTES:
        raise MasterKeyError(
            f"The master key must decode to exactly {MASTER_KEY_BYTES} bytes. "
            "Generate a new one and set it before starting the service."
        )
    return key


def _decode_master_key(encoded: str) -> bytes:
    try:
        return base64.b64decode(encoded, validate=True)
    except Exception as exc:
        raise MasterKeyError(
            "The master key is not valid base64. Generate a new one and set it before starting "
            "the service."
        ) from exc


def _configured_master_key() -> str:
    """The configured master key, from settings when it exists and the environment otherwise.

    `settings.py` belongs to another work package and may not be importable yet, so the same
    variable it reads is the fallback. This is the operator's key, never a user's provider key —
    a BYOK key has no environment fallback anywhere in this package.
    """
    configured: str | None = None
    try:
        from resume_pipeline.settings import get_settings
    except Exception:
        configured = None
    else:
        configured = str(getattr(get_settings(), "master_key", "") or "") or None

    if configured is None:
        configured = os.environ.get("RESUME_MASTER_KEY") or None

    if not configured:
        raise MasterKeyError(
            "The master key is not configured. Set RESUME_MASTER_KEY to a base64 32-byte value "
            "before starting the service."
        )
    return configured
