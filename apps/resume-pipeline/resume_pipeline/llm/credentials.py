"""Per-run BYOK credentials (RG-023).

A run decrypts its provider keys once, into memory, inside the pipeline process. From there a key
reaches exactly one place: the constructor of the client that spends it. It is never bound to a
log context, never written to `resume_runs` jsonb, and never in an exception message.

`RunCredentials` writes its own `__repr__`. A dataclass's generated one prints every field, which
would put plaintext keys into any log line or traceback that renders the object — and a traceback
is precisely when everything gets rendered. The mapping itself is wrapped so that even
`dataclasses.asdict` and an f-string on `.keys` produce the redacted form.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from typing import Any

from resume_pipeline.crypto import open_sealed
from resume_pipeline.errors import MissingApiKey
from resume_pipeline.repositories import keys as keys_repo

_REDACTED = "{…redacted…}"


class _SecretMapping(Mapping[str, str]):
    """A provider → key mapping that will not render its values.

    Reading a value is explicit (`creds.require("openai")`, `creds.keys["openai"]`); printing the
    mapping, or letting something else print it for you, is not.
    """

    __slots__ = ("_values",)

    def __init__(self, values: Mapping[str, str]) -> None:
        self._values = dict(values)

    def __getitem__(self, key: str) -> str:
        return self._values[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._values)

    def __len__(self) -> int:
        return len(self._values)

    def __repr__(self) -> str:
        return _REDACTED

    def __str__(self) -> str:
        return _REDACTED


@dataclass(frozen=True, repr=False)
class RunCredentials:
    """The provider keys one run may spend. In memory only, for the life of the run."""

    keys: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "keys", _SecretMapping(self.keys))

    def require(self, provider: str) -> str:
        """The key for `provider`, or `MissingApiKey` naming the provider that is missing."""
        key = self.keys.get(provider)
        if not key:
            raise MissingApiKey(
                f"This run needs a {provider} key. Add one in settings and start the run again.",
                details={"provider": provider},
            )
        return key

    def providers(self) -> list[str]:
        return sorted(self.keys)

    def __repr__(self) -> str:
        # Provider names are safe to show and are the only useful thing in a log line; the values
        # are not shown at any verbosity.
        return f"RunCredentials(providers={self.providers()!r})"

    __str__ = __repr__


async def resolve_for_run(
    conn: Any, user_id: str, providers: Iterable[str], *, master_key: bytes | None = None
) -> RunCredentials:
    """Decrypt this user's keys for `providers` — once, in one query, before the graph starts.

    Resolving up front is the point. A run that reaches the review node and only then discovers it
    has no Anthropic key has already spent the user's money on generation.

    A provider with no stored key is absent from the result rather than an error here. Whether an
    absent key is fatal depends on what the run is about to do with it, and that is the caller's
    knowledge: `RunCredentials.require` and `clients_for_run` raise `MissingApiKey` naming the
    provider.
    """
    wanted = list(dict.fromkeys(providers))
    sealed = await keys_repo.fetch_ciphertexts(conn, user_id, wanted)
    resolved = {
        provider: open_sealed(user_id, sealed[provider], master_key=master_key)
        for provider in wanted
        if provider in sealed
    }
    return RunCredentials(keys=resolved)
