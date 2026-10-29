"""`resume_pipeline.storage.local` and `storage.base` (WP3 §5, acceptance criteria 7 and 8).

`paths.document_path` is the first gate; this class is the second, and it is the one that actually
opens a file descriptor. The contract is explicit that the check here has to stand on its own —
"defence in depth behind `paths.py`, because this is the class that touches the disk" — so every
traversal test below hands the store a hostile path *directly*, bypassing `document_path`
entirely. A store that is only safe when called through the path builder is not safe.

`resolve()` is part of the requirement, not an implementation detail: the contract says each method
resolves the final path and asserts it is inside `root`. That is what the symlink test checks, and
it is the one an `os.path.normpath` implementation fails.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import pytest

from resume_pipeline.errors import NotFound, ValidationFailed

LOCAL_MODULE = "resume_pipeline.storage.local"
BASE_MODULE = "resume_pipeline.storage.base"

USER = "11111111-1111-4111-8111-111111111111"
APPLICATION = "22222222-2222-4222-8222-222222222222"
RUN = "33333333-3333-4333-8333-333333333333"

VALID_PATH = f"{USER}/{APPLICATION}/{RUN}/resume_tex.tex"
OTHER_PATH = f"{USER}/{APPLICATION}/{RUN}/resume_pdf.pdf"

TEX = b"\\documentclass{article}\\begin{document}Hello\\end{document}"

# Handed straight to the store, with no path builder in the way.
ESCAPING_PATHS = [
    "../../etc/passwd",
    "../outside.txt",
    "..",
    "/etc/passwd",
    "/tmp/outside.txt",
    f"{USER}/../../../etc/passwd",
    f"{USER}/{APPLICATION}/../../../../outside.txt",
    "./../outside.txt",
    "subdir/../../outside.txt",
]


@pytest.fixture(scope="module")
def local_mod() -> Any:
    try:
        return importlib.import_module(LOCAL_MODULE)
    except ModuleNotFoundError as exc:  # pragma: no cover - only before WP3 source lands
        pytest.fail(f"WP3 has not provided `{LOCAL_MODULE}` yet ({exc}).", pytrace=False)


@pytest.fixture
def root(tmp_path: Path) -> Path:
    path = tmp_path / "documents"
    path.mkdir()
    return path


@pytest.fixture
def store(local_mod: Any, root: Path) -> Any:
    return local_mod.LocalBlobStore(root)


def _files_under(root: Path) -> set[str]:
    return {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()}


# ─── The protocol ─────────────────────────────────────────────────────────────


def test_the_blob_store_protocol_declares_the_five_methods() -> None:
    try:
        base = importlib.import_module(BASE_MODULE)
    except ModuleNotFoundError as exc:  # pragma: no cover - only before WP3 source lands
        pytest.fail(f"WP3 has not provided `{BASE_MODULE}` yet ({exc}).", pytrace=False)
    for method in ("put", "get", "signed_url", "delete", "exists"):
        assert hasattr(base.BlobStore, method), f"BlobStore is missing {method}"


def test_local_store_implements_the_protocol(store: Any) -> None:
    for method in ("put", "get", "signed_url", "delete", "exists"):
        assert callable(getattr(store, method)), f"LocalBlobStore is missing {method}"


# ─── Criterion 8: the round trip ──────────────────────────────────────────────


async def test_put_get_exists_delete_round_trip(store: Any, root: Path) -> None:
    returned = await store.put(VALID_PATH, TEX, "text/plain")
    assert returned == VALID_PATH

    assert await store.exists(VALID_PATH) is True
    assert await store.get(VALID_PATH) == TEX

    await store.delete(VALID_PATH)

    assert await store.exists(VALID_PATH) is False
    with pytest.raises(NotFound):
        await store.get(VALID_PATH)
    assert _files_under(root) == set()


async def test_delete_on_a_missing_path_is_a_no_op(store: Any) -> None:
    await store.delete(VALID_PATH)
    await store.delete(VALID_PATH)


async def test_get_on_a_missing_path_raises_not_found(store: Any) -> None:
    with pytest.raises(NotFound):
        await store.get(VALID_PATH)


async def test_exists_on_a_missing_path_is_false(store: Any) -> None:
    assert await store.exists(VALID_PATH) is False


async def test_put_creates_parent_directories(store: Any, root: Path) -> None:
    await store.put(VALID_PATH, TEX, "text/plain")
    assert (root / USER / APPLICATION / RUN / "resume_tex.tex").is_file()


async def test_put_leaves_no_temporary_file_behind(store: Any, root: Path) -> None:
    """The write is temp-file-then-rename; the temp file is not part of the result."""
    await store.put(VALID_PATH, TEX, "text/plain")
    await store.put(OTHER_PATH, b"%PDF-1.7\n", "application/pdf")
    assert _files_under(root) == {VALID_PATH, OTHER_PATH}


async def test_put_overwrites_in_place(store: Any, root: Path) -> None:
    await store.put(VALID_PATH, b"first", "text/plain")
    await store.put(VALID_PATH, b"second", "text/plain")
    assert await store.get(VALID_PATH) == b"second"
    assert _files_under(root) == {VALID_PATH}


async def test_binary_content_round_trips_byte_for_byte(store: Any) -> None:
    payload = bytes(range(256)) * 8
    await store.put(OTHER_PATH, payload, "application/pdf")
    assert await store.get(OTHER_PATH) == payload


async def test_an_empty_payload_round_trips(store: Any) -> None:
    await store.put(VALID_PATH, b"", "text/plain")
    assert await store.exists(VALID_PATH) is True
    assert await store.get(VALID_PATH) == b""


async def test_a_root_that_does_not_exist_yet_is_created_on_put(
    local_mod: Any, tmp_path: Path
) -> None:
    root = tmp_path / "not-yet"
    store = local_mod.LocalBlobStore(root)
    await store.put(VALID_PATH, TEX, "text/plain")
    assert (root / VALID_PATH).is_file()


# ─── Criterion 7, second half: the store refuses to leave its root ────────────


@pytest.mark.parametrize("hostile", ESCAPING_PATHS)
async def test_get_refuses_to_read_outside_the_root(store: Any, hostile: str) -> None:
    with pytest.raises(ValidationFailed):
        await store.get(hostile)


@pytest.mark.parametrize("hostile", ESCAPING_PATHS)
async def test_put_refuses_to_write_outside_the_root(
    store: Any, root: Path, hostile: str
) -> None:
    with pytest.raises(ValidationFailed):
        await store.put(hostile, b"owned", "text/plain")
    assert _files_under(root) == set()


@pytest.mark.parametrize("hostile", ESCAPING_PATHS)
async def test_exists_refuses_to_probe_outside_the_root(store: Any, hostile: str) -> None:
    with pytest.raises(ValidationFailed):
        await store.exists(hostile)


@pytest.mark.parametrize("hostile", ESCAPING_PATHS)
async def test_delete_refuses_to_unlink_outside_the_root(store: Any, hostile: str) -> None:
    with pytest.raises(ValidationFailed):
        await store.delete(hostile)


@pytest.mark.parametrize("hostile", ESCAPING_PATHS)
async def test_signed_url_refuses_a_path_outside_the_root(store: Any, hostile: str) -> None:
    with pytest.raises(ValidationFailed):
        await store.signed_url(hostile)


async def test_a_traversal_put_does_not_create_the_file_outside(
    store: Any, tmp_path: Path
) -> None:
    target = tmp_path / "outside.txt"
    with pytest.raises(ValidationFailed):
        await store.put("../outside.txt", b"owned", "text/plain")
    assert not target.exists()


async def test_a_traversal_get_cannot_read_a_real_file_outside(
    store: Any, tmp_path: Path
) -> None:
    secret = tmp_path / "outside.txt"
    secret.write_bytes(b"another tenant's resume")
    with pytest.raises(ValidationFailed):
        await store.get("../outside.txt")


async def test_a_symlink_out_of_the_root_is_refused(
    store: Any, root: Path, tmp_path: Path
) -> None:
    """`normpath` says this path is inside the root. `resolve` says it is not, and it is right."""
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    (outside / "secret.txt").write_bytes(b"another tenant's resume")
    (root / "escape").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValidationFailed):
        await store.get("escape/secret.txt")
    with pytest.raises(ValidationFailed):
        await store.put("escape/planted.txt", b"owned", "text/plain")
    assert not (outside / "planted.txt").exists()


async def test_a_null_byte_in_the_path_is_refused(store: Any) -> None:
    """Either answer in the contract will do — refused, or absent. A raw `ValueError` is a 500."""
    with pytest.raises((ValidationFailed, NotFound)):
        await store.get(f"{USER}/{APPLICATION}/{RUN}/resume_tex.tex\x00.png")


# ─── signed_url ───────────────────────────────────────────────────────────────


async def test_signed_url_returns_a_string_for_a_valid_path(store: Any) -> None:
    await store.put(VALID_PATH, TEX, "text/plain")
    url = await store.signed_url(VALID_PATH, ttl_seconds=60)
    assert isinstance(url, str)
    assert url
    assert " " not in url
