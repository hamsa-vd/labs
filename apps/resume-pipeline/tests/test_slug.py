"""`resume_pipeline.util.slug.slugify` (WP3 §6).

The contract says this is ported verbatim from v1's `resume_agent/storage.py::slugify`, so every
expectation below was produced by running *that* function, not by reading the port. The v1 body is:

    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    lowered = normalized.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or fallback

Four behaviours carry weight, because `applications.create` stores the result and a slug is part of
a user-visible identity: NFKD compatibility decomposition (so `½` becomes `12`, not nothing),
dropping anything that survives as non-ASCII, collapsing separator runs to a single `-`, and the
fallback that keeps an all-punctuation company name from producing an empty string.
"""

from __future__ import annotations

import importlib
import re
from collections.abc import Callable
from typing import Any

import pytest

SLUG_MODULE = "resume_pipeline.util.slug"


@pytest.fixture(scope="module")
def slugify() -> Callable[..., str]:
    """The ported `slugify`, imported lazily so collection does not depend on WP3's source."""
    try:
        module: Any = importlib.import_module(SLUG_MODULE)
    except ModuleNotFoundError as exc:  # pragma: no cover - only before WP3 source lands
        pytest.fail(f"WP3 has not provided `{SLUG_MODULE}` yet ({exc}).", pytrace=False)
    return module.slugify  # type: ignore[no-any-return]


# Every pair here is v1's own output for that input.
VERBATIM_CASES = [
    ("Liv-ex", "liv-ex"),
    ("Ltd.", "ltd"),
    ("ACME  Corp", "acme-corp"),
    ("  Leading and trailing  ", "leading-and-trailing"),
    ("--Hello--", "hello"),
    ("A / B__C", "a-b-c"),
    ("Series 7 (2024)", "series-7-2024"),
    ("Data Science/ML", "data-science-ml"),
    ("C++ Developer", "c-developer"),
    ("Senior Backend Engineer — Platform", "senior-backend-engineer-platform"),
]

# NFKD then ascii-ignore. `ß` does not decompose, so it disappears; `½` decomposes to `1⁄2`
# whose fraction slash is dropped, leaving `12`.
UNICODE_CASES = [
    ("Café Ltd.", "cafe-ltd"),
    ("Ångström & Co", "angstrom-co"),
    ("aéb", "aeb"),
    ("Núvola", "nuvola"),
    ("①", "1"),
    ("½ portion", "12-portion"),
    ("Straße", "strae"),
]

EMPTY_CASES = ["", "   ", "!!!", "日本語", "---", " ", "?/?"]


@pytest.mark.parametrize(("value", "expected"), VERBATIM_CASES)
def test_slugify_matches_v1(slugify: Callable[..., str], value: str, expected: str) -> None:
    assert slugify(value) == expected


@pytest.mark.parametrize(("value", "expected"), UNICODE_CASES)
def test_slugify_nfkd_normalises_then_drops_non_ascii(
    slugify: Callable[..., str], value: str, expected: str
) -> None:
    assert slugify(value) == expected


@pytest.mark.parametrize("value", EMPTY_CASES)
def test_slugify_falls_back_when_nothing_survives(slugify: Callable[..., str], value: str) -> None:
    assert slugify(value) == "untitled"


@pytest.mark.parametrize("value", EMPTY_CASES)
def test_slugify_honours_a_custom_fallback(slugify: Callable[..., str], value: str) -> None:
    assert slugify(value, "unknown") == "unknown"


def test_slugify_default_fallback_is_untitled(slugify: Callable[..., str]) -> None:
    assert slugify("!!!") == "untitled"


@pytest.mark.parametrize(
    "value",
    [
        "Liv-ex",
        "Café Ltd.",
        "Senior Backend Engineer — Platform",
        "  __ weird -- input // ",
        "½ portion",
        "!!!",
    ],
)
def test_slug_shape_is_always_url_safe(slugify: Callable[..., str], value: str) -> None:
    """Whatever goes in, what comes out is lower-case alphanumerics and single hyphens."""
    slug = slugify(value)
    assert slug, "a slug is never empty; the fallback covers that"
    assert re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug), slug
    assert not slug.startswith("-")
    assert not slug.endswith("-")
    assert "--" not in slug


def test_slugify_is_idempotent(slugify: Callable[..., str]) -> None:
    once = slugify("Senior Backend Engineer — Platform")
    assert slugify(once) == once
