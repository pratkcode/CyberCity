"""Shared types and base classes for all CyberCity models."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

# Identifiers are lowercase slugs such as "hosp-db-01". Keeping them strict
# makes them safe to use in URLs, logs and graph node keys without escaping.
IDENTIFIER_PATTERN = r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$"
IDENTIFIER_MAX_LENGTH = 48

Identifier = Annotated[
    str,
    StringConstraints(
        min_length=2,
        max_length=IDENTIFIER_MAX_LENGTH,
        pattern=IDENTIFIER_PATTERN,
    ),
]

DisplayName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=80),
]


class StrictModel(BaseModel):
    """Base model: immutable and rejects unknown fields.

    Immutability keeps simulation snapshots from being changed by accident,
    and rejecting extra fields turns client typos into clear 422 errors
    instead of silently ignored input.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")
