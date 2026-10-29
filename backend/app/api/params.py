"""Shared, validated path and query parameter types."""

from typing import Annotated

from fastapi import Path, Query

from app.models.common import IDENTIFIER_MAX_LENGTH, IDENTIFIER_PATTERN

_ID_RULES = {
    "min_length": 2,
    "max_length": IDENTIFIER_MAX_LENGTH,
    "pattern": IDENTIFIER_PATTERN,
}

DeviceIdPath = Annotated[str, Path(description="Device id, e.g. 'hosp-ehr-db-01'.", **_ID_RULES)]
ServiceIdPath = Annotated[str, Path(description="Service id, e.g. 'svc-ehr'.", **_ID_RULES)]
SourceIdQuery = Annotated[str, Query(description="Source device id.", **_ID_RULES)]
TargetIdQuery = Annotated[str, Query(description="Target device id.", **_ID_RULES)]
