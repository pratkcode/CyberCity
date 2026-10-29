"""Access policy models: zone-to-zone rules for modeled traffic.

The models only describe rules. Evaluation lives in
``app.simulation.policy``, apart from both the models and the graph.
"""

from enum import StrEnum

from pydantic import Field, field_validator

from app.models.common import Identifier, StrictModel
from app.models.network import Protocol

MAX_PRIORITY = 10_000


class PolicyAction(StrEnum):
    ALLOW = "allow"
    DENY = "deny"


class PolicyRule(StrictModel):
    """One rule. ``None`` zones and an empty ``protocols`` tuple mean "any"."""

    id: Identifier
    priority: int = Field(
        ge=0, le=MAX_PRIORITY, description="Lower numbers are evaluated first."
    )
    action: PolicyAction
    source_zone_id: Identifier | None = None
    destination_zone_id: Identifier | None = None
    protocols: tuple[Protocol, ...] = ()
    description: str = Field(default="", max_length=200)

    @field_validator("protocols")
    @classmethod
    def _unique_protocols(cls, value: tuple[Protocol, ...]) -> tuple[Protocol, ...]:
        if len(set(value)) != len(value):
            raise ValueError("protocols must not contain duplicates.")
        return value


class AccessPolicy(StrictModel):
    rules: tuple[PolicyRule, ...] = ()

    @field_validator("rules")
    @classmethod
    def _unique_rule_ids(cls, value: tuple[PolicyRule, ...]) -> tuple[PolicyRule, ...]:
        ids = [r.id for r in value]
        if len(set(ids)) != len(ids):
            raise ValueError("Policy rule ids must be unique.")
        return value


class PolicyDecision(StrictModel):
    allowed: bool
    source_zone_id: Identifier
    destination_zone_id: Identifier
    protocol: Protocol
    matched_rule_id: Identifier | None
    default_applied: bool
    reason: str
