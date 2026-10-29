"""`resume_pipeline.crypto` — envelope encryption for BYOK keys (WP4 §4).

Two properties matter more than the round trip, and both are about what happens when something is
wrong rather than when everything is right.

**A ciphertext sealed for one user cannot be opened as another.** The data key is derived per user
with HKDF-SHA256 over the user id, so cross-user decryption fails at the GCM tag. That is the only
thing standing between a bug in a `where user_id = $1` clause and one tenant using another's API
key. It is tested directly.

**The failure says nothing.** Wrong user, tampered ciphertext, wrong master key — all three raise
`Forbidden` with the same message. An error that distinguishes them is an oracle: it tells an
attacker which half of the guess was right.

The third property is the boring one that a review would never catch by reading: the nonce is
fresh on every seal, so sealing the same key twice gives different bytes. Without it, equal
ciphertexts in the table would leak that two users share a key.
"""

from __future__ import annotations

import importlib
import inspect
import os
from types import ModuleType

import pytest

from resume_pipeline.errors import Forbidden
from tests.llm.conftest import SENTINEL_SECRET, ensure_settings_env

ensure_settings_env()

USER_A = "11111111-1111-4111-8111-111111111111"
USER_B = "22222222-2222-4222-8222-222222222222"

MASTER_KEY = b"0123456789abcdef0123456789abcdef"  # 32 bytes
OTHER_MASTER_KEY = b"fedcba9876543210fedcba9876543210"

NONCE_BYTES = 12
TAG_BYTES = 16


@pytest.fixture(scope="session")
def crypto() -> ModuleType:
    ensure_settings_env()
    try:
        return importlib.import_module("resume_pipeline.crypto")
    except ModuleNotFoundError as exc:  # pragma: no cover - only before WP4 source lands
        pytest.fail(f"WP4 has not provided `resume_pipeline.crypto` yet ({exc}).", pytrace=False)


# ─── Round trip ───────────────────────────────────────────────────────────────


def test_a_sealed_secret_opens_again(crypto: ModuleType) -> None:
    sealed = crypto.seal(USER_A, SENTINEL_SECRET, master_key=MASTER_KEY)

    assert crypto.open_sealed(USER_A, sealed, master_key=MASTER_KEY) == SENTINEL_SECRET


def test_seal_returns_bytes(crypto: ModuleType) -> None:
    sealed = crypto.seal(USER_A, SENTINEL_SECRET, master_key=MASTER_KEY)

    assert isinstance(sealed, bytes)


def test_open_sealed_returns_a_string(crypto: ModuleType) -> None:
    sealed = crypto.seal(USER_A, SENTINEL_SECRET, master_key=MASTER_KEY)

    assert isinstance(crypto.open_sealed(USER_A, sealed, master_key=MASTER_KEY), str)


def test_a_sealed_secret_opens_more_than_once(crypto: ModuleType) -> None:
    sealed = crypto.seal(USER_A, SENTINEL_SECRET, master_key=MASTER_KEY)

    assert crypto.open_sealed(USER_A, sealed, master_key=MASTER_KEY) == SENTINEL_SECRET
    assert crypto.open_sealed(USER_A, sealed, master_key=MASTER_KEY) == SENTINEL_SECRET


def test_unicode_survives_the_round_trip(crypto: ModuleType) -> None:
    secret = "clé-très-sécurisée-✅"

    sealed = crypto.seal(USER_A, secret, master_key=MASTER_KEY)

    assert crypto.open_sealed(USER_A, sealed, master_key=MASTER_KEY) == secret


def test_a_realistic_key_length_survives(crypto: ModuleType) -> None:
    secret = "sk-ant-api03-" + "x" * 95

    sealed = crypto.seal(USER_A, secret, master_key=MASTER_KEY)

    assert crypto.open_sealed(USER_A, sealed, master_key=MASTER_KEY) == secret


def test_the_master_key_comes_from_settings_when_none_is_passed(crypto: ModuleType) -> None:
    """The keyword exists for tests and key rotation; production passes nothing and gets
    `settings.master_key`."""
    sealed = crypto.seal(USER_A, SENTINEL_SECRET)

    assert crypto.open_sealed(USER_A, sealed) == SENTINEL_SECRET


# ─── The stored form ──────────────────────────────────────────────────────────


def test_sealing_the_same_secret_twice_gives_different_bytes(crypto: ModuleType) -> None:
    """A fresh 12-byte nonce per seal. Equal ciphertexts in the table would say that two users
    pasted the same key, which is not something the table is allowed to reveal."""
    first = crypto.seal(USER_A, SENTINEL_SECRET, master_key=MASTER_KEY)
    second = crypto.seal(USER_A, SENTINEL_SECRET, master_key=MASTER_KEY)

    assert first != second


def test_both_of_those_still_open(crypto: ModuleType) -> None:
    first = crypto.seal(USER_A, SENTINEL_SECRET, master_key=MASTER_KEY)
    second = crypto.seal(USER_A, SENTINEL_SECRET, master_key=MASTER_KEY)

    assert crypto.open_sealed(USER_A, first, master_key=MASTER_KEY) == SENTINEL_SECRET
    assert crypto.open_sealed(USER_A, second, master_key=MASTER_KEY) == SENTINEL_SECRET


def test_the_nonce_is_twelve_fresh_bytes_at_the_front(crypto: ModuleType) -> None:
    first = crypto.seal(USER_A, SENTINEL_SECRET, master_key=MASTER_KEY)
    second = crypto.seal(USER_A, SENTINEL_SECRET, master_key=MASTER_KEY)

    assert first[:NONCE_BYTES] != second[:NONCE_BYTES]


def test_the_stored_form_is_nonce_tag_and_payload(crypto: ModuleType) -> None:
    """`nonce || tag || payload`. AES-GCM's payload is the same length as the plaintext, so the
    whole thing is 28 bytes longer than the secret. A different length means a different layout,
    and the migration's `bytea` column has no other schema to check against."""
    secret = "sk-test-0123456789"

    sealed = crypto.seal(USER_A, secret, master_key=MASTER_KEY)

    assert len(sealed) == NONCE_BYTES + TAG_BYTES + len(secret.encode("utf-8"))


def test_the_ciphertext_does_not_contain_the_secret(crypto: ModuleType) -> None:
    sealed = crypto.seal(USER_A, SENTINEL_SECRET, master_key=MASTER_KEY)

    assert SENTINEL_SECRET.encode("utf-8") not in sealed


# ─── Cross-user and tampering ─────────────────────────────────────────────────


def test_a_ciphertext_sealed_for_one_user_does_not_open_for_another(crypto: ModuleType) -> None:
    """Acceptance criterion 1, and the reason the data key is derived per user at all."""
    sealed = crypto.seal(USER_A, SENTINEL_SECRET, master_key=MASTER_KEY)

    with pytest.raises(Forbidden):
        crypto.open_sealed(USER_B, sealed, master_key=MASTER_KEY)


def test_the_wrong_master_key_does_not_open_it(crypto: ModuleType) -> None:
    sealed = crypto.seal(USER_A, SENTINEL_SECRET, master_key=MASTER_KEY)

    with pytest.raises(Forbidden):
        crypto.open_sealed(USER_A, sealed, master_key=OTHER_MASTER_KEY)


def test_a_tampered_payload_does_not_open(crypto: ModuleType) -> None:
    sealed = bytearray(crypto.seal(USER_A, SENTINEL_SECRET, master_key=MASTER_KEY))
    sealed[-1] ^= 0xFF

    with pytest.raises(Forbidden):
        crypto.open_sealed(USER_A, bytes(sealed), master_key=MASTER_KEY)


def test_a_tampered_nonce_does_not_open(crypto: ModuleType) -> None:
    sealed = bytearray(crypto.seal(USER_A, SENTINEL_SECRET, master_key=MASTER_KEY))
    sealed[0] ^= 0xFF

    with pytest.raises(Forbidden):
        crypto.open_sealed(USER_A, bytes(sealed), master_key=MASTER_KEY)


def test_a_tampered_tag_does_not_open(crypto: ModuleType) -> None:
    sealed = bytearray(crypto.seal(USER_A, SENTINEL_SECRET, master_key=MASTER_KEY))
    sealed[NONCE_BYTES] ^= 0xFF

    with pytest.raises(Forbidden):
        crypto.open_sealed(USER_A, bytes(sealed), master_key=MASTER_KEY)


def test_a_truncated_ciphertext_does_not_open(crypto: ModuleType) -> None:
    sealed = crypto.seal(USER_A, SENTINEL_SECRET, master_key=MASTER_KEY)

    with pytest.raises(Forbidden):
        crypto.open_sealed(USER_A, sealed[:-1], master_key=MASTER_KEY)


def test_empty_bytes_do_not_open(crypto: ModuleType) -> None:
    with pytest.raises(Forbidden):
        crypto.open_sealed(USER_A, b"", master_key=MASTER_KEY)


# ─── The failure is not an oracle ─────────────────────────────────────────────


def _failure_message(crypto: ModuleType, user_id: str, blob: bytes, key: bytes) -> str:
    with pytest.raises(Forbidden) as caught:
        crypto.open_sealed(user_id, blob, master_key=key)
    return caught.value.message


def test_every_authentication_failure_reads_the_same(crypto: ModuleType) -> None:
    """Wrong user, wrong key, tampered bytes — one message. Anything that distinguishes them
    tells the person holding a stolen ciphertext which half of the guess was right."""
    sealed = crypto.seal(USER_A, SENTINEL_SECRET, master_key=MASTER_KEY)
    tampered = bytearray(sealed)
    tampered[-1] ^= 0xFF

    wrong_user = _failure_message(crypto, USER_B, sealed, MASTER_KEY)
    wrong_key = _failure_message(crypto, USER_A, sealed, OTHER_MASTER_KEY)
    wrong_bytes = _failure_message(crypto, USER_A, bytes(tampered), MASTER_KEY)

    assert wrong_user == wrong_key == wrong_bytes


def test_the_failure_message_carries_no_secret_and_no_ciphertext(crypto: ModuleType) -> None:
    sealed = crypto.seal(USER_A, SENTINEL_SECRET, master_key=MASTER_KEY)

    with pytest.raises(Forbidden) as caught:
        crypto.open_sealed(USER_B, sealed, master_key=MASTER_KEY)

    rendered = f"{caught.value!s} {caught.value!r} {caught.value.details!r}"
    assert SENTINEL_SECRET not in rendered
    assert sealed.hex() not in rendered
    assert str(sealed) not in rendered


def test_the_failure_message_follows_the_house_voice(crypto: ModuleType) -> None:
    sealed = crypto.seal(USER_A, SENTINEL_SECRET, master_key=MASTER_KEY)

    with pytest.raises(Forbidden) as caught:
        crypto.open_sealed(USER_B, sealed, master_key=MASTER_KEY)

    assert caught.value.message.strip() != ""
    assert "!" not in caught.value.message


def test_a_failure_is_forbidden_not_a_generic_error(crypto: ModuleType) -> None:
    """`Forbidden` renders a 403 through the shared handler. A `cryptography` exception escaping
    here would be a 500 with a stack trace in the log."""
    sealed = crypto.seal(USER_A, SENTINEL_SECRET, master_key=MASTER_KEY)

    with pytest.raises(Forbidden) as caught:
        crypto.open_sealed(USER_B, sealed, master_key=MASTER_KEY)

    assert caught.value.code == "forbidden"
    assert caught.value.status == 403


# ─── The master key ───────────────────────────────────────────────────────────


@pytest.mark.parametrize("length", [16, 31, 33, 64])
def test_a_master_key_that_is_not_thirty_two_bytes_is_refused(
    crypto: ModuleType, length: int
) -> None:
    """Acceptance criterion 2. AES-256 needs 32 bytes; a 16-byte key would silently give AES-128,
    and a 64-byte one usually means somebody pasted the base64 instead of decoding it."""
    with pytest.raises(Exception) as caught:  # noqa: B017 - the type is pinned below
        crypto.seal(USER_A, SENTINEL_SECRET, master_key=b"k" * length)

    assert not isinstance(caught.value, Forbidden), (
        "A misconfigured master key is an operator error, not an authentication failure. "
        "Raising `Forbidden` tells the operator the ciphertext was bad."
    )


def test_an_invalid_master_key_in_settings_is_refused(
    crypto: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The same rule on the path production takes: `settings.master_key` is base64 that decodes to
    exactly 32 bytes, and anything else stops the process rather than encrypting with a short key.

    Reads the key through `get_settings`, whose cache is cleared either side, so the rest of the
    suite keeps the valid key it was configured with.
    """
    settings_mod = importlib.import_module("resume_pipeline.settings")
    monkeypatch.setenv("RESUME_MASTER_KEY", "dG9vLXNob3J0")  # "too-short", 9 bytes decoded
    settings_mod.get_settings.cache_clear()

    try:
        with pytest.raises(Exception) as caught:  # noqa: B017 - the type is pinned below
            crypto.seal(USER_A, SENTINEL_SECRET)
        assert not isinstance(caught.value, Forbidden)
    finally:
        monkeypatch.undo()
        ensure_settings_env()
        settings_mod.get_settings.cache_clear()


# ─── Surface area ─────────────────────────────────────────────────────────────


def test_the_module_exposes_only_seal_and_open_sealed(crypto: ModuleType) -> None:
    """"No "get the data key" helper, because every extra surface is another place a key can
    leak." A module that hands out the derived key makes the two-function discipline pointless."""
    exported = {
        name
        for name, value in vars(crypto).items()
        if not name.startswith("_")
        and inspect.isfunction(value)
        and getattr(value, "__module__", "") == crypto.__name__
    }

    assert exported == {"seal", "open_sealed"}


def test_seal_and_open_sealed_take_the_master_key_by_keyword(crypto: ModuleType) -> None:
    for function in (crypto.seal, crypto.open_sealed):
        parameter = inspect.signature(function).parameters["master_key"]
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
        assert parameter.default is None


def test_the_environment_still_holds_a_valid_master_key() -> None:
    """A guard for the test above: if it leaves a broken key behind, every later test in the run
    fails for a reason that has nothing to do with the code under test."""
    assert os.environ.get("RESUME_MASTER_KEY")
