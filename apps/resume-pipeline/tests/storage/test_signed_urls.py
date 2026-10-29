"""`resume_pipeline.storage.signed` (WP3 §5, acceptance criterion 6).

This is the one piece of WP3 that an unauthenticated party gets to poke at: ascend hands a signed
token to a browser, and the browser hands it back. Three things therefore have to hold.

**Expiry is enforced against an injected clock.** `now` is a parameter precisely so this suite does
not sleep, and so a test can sit one second either side of the boundary without flaking.

**Tampering fails closed.** A flipped byte, a spliced token, a re-pointed path, a token signed with
a different secret: all `Forbidden`.

**The failures are indistinguishable.** This is the assertion that matters most and the easiest one
to lose: if "expired" and "bad signature" carry different messages, an attacker holding a stale
token learns that their forgery *would* have been accepted, and one holding a forged token learns
which half of it to keep working on. So the tests below do not check each message individually —
they check that every failure produces the *same* message, and that the message names neither the
path nor the secret.

Constant-time comparison is in the contract and is not observable from here; it is the one clause
this file cannot verify.
"""

from __future__ import annotations

import base64
import importlib
import re
from typing import Any

import pytest

from resume_pipeline.errors import Forbidden

SIGNED_MODULE = "resume_pipeline.storage.signed"

SECRET = "url-signing-secret-4f0c9a2e"
OTHER_SECRET = "url-signing-secret-4f0c9a2f"

USER = "11111111-1111-4111-8111-111111111111"
APPLICATION = "22222222-2222-4222-8222-222222222222"
RUN = "33333333-3333-4333-8333-333333333333"

PATH = f"{USER}/{APPLICATION}/{RUN}/resume_pdf.pdf"
# Same length as PATH, so a forged token can be built by substitution.
OTHER_PATH = f"{USER}/{APPLICATION}/{RUN}/resume_tex.pdf"

NOW = 1_700_000_000
TTL = 60

URL_SAFE = re.compile(r"^[A-Za-z0-9_\-.=]+$")

MALFORMED_TOKENS = [
    "",
    "x",
    "!!!not-base-64!!!",
    "....",
    "a.b.c.d.e",
    "ééé",
    base64.urlsafe_b64encode(b"just some bytes").decode(),
    base64.urlsafe_b64encode(b'{"path":"' + PATH.encode() + b'","exp":9999999999}').decode(),
    "../../etc/passwd",
]


@pytest.fixture(scope="module")
def signed() -> Any:
    try:
        return importlib.import_module(SIGNED_MODULE)
    except ModuleNotFoundError as exc:  # pragma: no cover - only before WP3 source lands
        pytest.fail(f"WP3 has not provided `{SIGNED_MODULE}` yet ({exc}).", pytrace=False)


def _token(signed: Any, path: str = PATH, ttl: int = TTL, secret: str = SECRET) -> str:
    return signed.sign_document_url(path, ttl, secret, now=NOW)  # type: ignore[no-any-return]


def _flip(token: str, index: int) -> str:
    """Change exactly one character to another character of the URL-safe base64 alphabet."""
    index %= len(token)
    original = token[index]
    replacement = "A" if original != "A" else "B"
    return token[:index] + replacement + token[index + 1 :]


def _decode_loose(token: str) -> bytes | None:
    try:
        return base64.urlsafe_b64decode(token + "=" * (-len(token) % 4))
    except Exception:  # noqa: BLE001 - a token that will not decode is simply not repointable
        return None


def _repoint_at_another_path(signed: Any, token: str) -> str:
    """A token that claims `OTHER_PATH` but carries the signature over `PATH`.

    The token's internal layout is the implementation's business, so this tries the two shapes a
    signature over `(path, expiry)` can take — the path visible in the token text, or visible once
    the token is base64-decoded — and falls back to splicing two legitimately signed tokens, which
    is a signature mismatch under any layout.
    """
    assert len(PATH) == len(OTHER_PATH)
    if PATH in token:
        return token.replace(PATH, OTHER_PATH, 1)

    raw = _decode_loose(token)
    if raw is not None and PATH.encode() in raw:
        forged = raw.replace(PATH.encode(), OTHER_PATH.encode(), 1)
        return base64.urlsafe_b64encode(forged).decode().rstrip("=")

    other = _token(signed, path=OTHER_PATH)
    half = len(other) // 2
    return other[:half] + token[half:]


# ─── The happy path ───────────────────────────────────────────────────────────


def test_a_fresh_token_verifies_to_its_path(signed: Any) -> None:
    token = _token(signed)
    assert signed.verify_document_token(token, SECRET, now=NOW) == PATH


def test_a_token_verifies_right_up_to_its_ttl(signed: Any) -> None:
    token = _token(signed)
    assert signed.verify_document_token(token, SECRET, now=NOW + TTL - 1) == PATH


def test_a_token_verifies_without_an_injected_clock(signed: Any) -> None:
    token = signed.sign_document_url(PATH, 300, SECRET)
    assert signed.verify_document_token(token, SECRET) == PATH


def test_the_token_is_url_safe(signed: Any) -> None:
    token = _token(signed)
    assert URL_SAFE.match(token), token
    assert "+" not in token
    assert "/" not in token
    assert token.strip() == token


def test_different_paths_produce_different_tokens(signed: Any) -> None:
    assert _token(signed, path=PATH) != _token(signed, path=OTHER_PATH)


def test_different_expiries_produce_different_tokens(signed: Any) -> None:
    assert _token(signed, ttl=60) != _token(signed, ttl=120)


def test_a_token_carries_its_own_path_not_another(signed: Any) -> None:
    token = _token(signed, path=OTHER_PATH)
    assert signed.verify_document_token(token, SECRET, now=NOW) == OTHER_PATH


# ─── Criterion 6: expiry ──────────────────────────────────────────────────────


def test_a_token_is_forbidden_after_its_ttl(signed: Any) -> None:
    token = _token(signed)
    with pytest.raises(Forbidden):
        signed.verify_document_token(token, SECRET, now=NOW + TTL + 1)


def test_a_long_expired_token_is_forbidden(signed: Any) -> None:
    token = _token(signed)
    with pytest.raises(Forbidden):
        signed.verify_document_token(token, SECRET, now=NOW + 86_400)


# ─── Criterion 6: tampering ───────────────────────────────────────────────────


# Positions stay clear of the final base64 group, whose spare low bits are discarded on
# decode: a flip there can round-trip to the same bytes and would prove nothing.
@pytest.mark.parametrize("position", [0, 1, 5, 11, 23, 37, -12, -8])
def test_one_flipped_byte_is_forbidden(signed: Any, position: int) -> None:
    token = _token(signed)
    with pytest.raises(Forbidden):
        signed.verify_document_token(_flip(token, position), SECRET, now=NOW)


def test_a_token_repointed_at_another_path_is_forbidden(signed: Any) -> None:
    forged = _repoint_at_another_path(signed, _token(signed))
    with pytest.raises(Forbidden):
        signed.verify_document_token(forged, SECRET, now=NOW)


def test_a_token_signed_with_another_secret_is_forbidden(signed: Any) -> None:
    token = _token(signed, secret=OTHER_SECRET)
    with pytest.raises(Forbidden):
        signed.verify_document_token(token, SECRET, now=NOW)


def test_a_truncated_token_is_forbidden(signed: Any) -> None:
    token = _token(signed)
    with pytest.raises(Forbidden):
        signed.verify_document_token(token[:-4], SECRET, now=NOW)


def test_an_extended_token_is_forbidden(signed: Any) -> None:
    token = _token(signed)
    with pytest.raises(Forbidden):
        signed.verify_document_token(token + "AAAA", SECRET, now=NOW)


@pytest.mark.parametrize("token", MALFORMED_TOKENS)
def test_a_malformed_token_is_forbidden_not_a_crash(signed: Any, token: str) -> None:
    """Garbage in must be `Forbidden`, not a `ValueError` escaping as a 500."""
    with pytest.raises(Forbidden):
        signed.verify_document_token(token, SECRET, now=NOW)


# ─── Criterion 6: the failures are indistinguishable ──────────────────────────


def _failure_messages(signed: Any) -> dict[str, Forbidden]:
    """Every distinct way verification can fail, keyed by how it failed."""
    valid = _token(signed)
    failures: dict[str, Forbidden] = {}

    cases: list[tuple[str, str, int]] = [
        ("expired", valid, NOW + TTL + 1),
        ("flipped byte", _flip(valid, len(valid) // 2), NOW),
        ("flipped first byte", _flip(valid, 0), NOW),
        ("truncated", valid[:-4], NOW),
        ("repointed path", _repoint_at_another_path(signed, valid), NOW),
        ("wrong secret", _token(signed, secret=OTHER_SECRET), NOW),
        ("empty", "", NOW),
        ("not base64", "!!!not-base-64!!!", NOW),
        ("random bytes", base64.urlsafe_b64encode(b"just some bytes").decode(), NOW),
    ]

    for name, token, now in cases:
        with pytest.raises(Forbidden) as excinfo:
            signed.verify_document_token(token, SECRET, now=now)
        failures[name] = excinfo.value
    return failures


def test_every_failure_carries_the_same_message(signed: Any) -> None:
    failures = _failure_messages(signed)
    messages = {name: failure.message for name, failure in failures.items()}
    distinct = set(messages.values())
    assert len(distinct) == 1, f"failures are distinguishable and can be probed: {messages}"


def test_every_failure_carries_the_same_envelope(signed: Any) -> None:
    failures = _failure_messages(signed)
    envelopes = {name: failure.envelope() for name, failure in failures.items()}
    first = next(iter(envelopes.values()))
    for name, envelope in envelopes.items():
        assert envelope == first, f"`{name}` renders differently from the rest"
    assert first["error"]["code"] == "forbidden"


def test_every_failure_is_a_403(signed: Any) -> None:
    for failure in _failure_messages(signed).values():
        assert failure.status == 403


def test_the_failure_message_leaks_neither_path_nor_secret(signed: Any) -> None:
    message = next(iter(_failure_messages(signed).values())).message
    assert PATH not in message
    assert OTHER_PATH not in message
    assert SECRET not in message
    assert USER not in message
    assert "!" not in message, "arey copy carries no exclamation marks"
    assert message.strip(), "a refusal still has to say something"
