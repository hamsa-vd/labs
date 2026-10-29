"""Response shapes shared by every router (RG-004).

The error envelope is defined here as a model as well as being produced by `AppError.envelope()`,
so the generated OpenAPI — which is what `packages/typescript/resume-contracts` is built from —
describes the failure shape the service actually returns. A client generated against a schema
that omits errors has to invent them.

`Money` is the one type worth stating twice: a `Decimal` that serialises as a **string**. JSON has
no decimal, so a number here becomes a float in every client in the stack, and a float is not a
currency.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Any

from pydantic import BaseModel, Field, PlainSerializer

Money = Annotated[Decimal, PlainSerializer(lambda value: str(value), return_type=str)]


class ErrorBody(BaseModel):
    code: str = Field(description="Stable snake_case code the UI switches on.")
    message: str = Field(description="One sentence: what happened, then what to do.")
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorEnvelope(BaseModel):
    """Every failure this service returns has exactly this shape."""

    error: ErrorBody


class HealthStatus(BaseModel):
    status: str
    version: str
    db: str


class Page[T](BaseModel):
    """A cursor page. `next_cursor` is null on the last page.

    Cursors, never offsets: these lists are ordered by `updated_at`, and an offset page over a
    list that reorders whenever a row is touched both drops and repeats rows.
    """

    items: list[T]
    next_cursor: str | None = None


class Acknowledged(BaseModel):
    """The body for an accepted-but-not-finished action, such as starting a run."""

    id: str
    status: str
