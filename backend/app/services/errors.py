"""Domain errors raised by services and translated to HTTP responses by the API layer.

Keeping these free of FastAPI imports lets the services be used from tests,
scripts or a future CLI without dragging in HTTP concerns.
"""

from typing import Any


class CyberCityError(Exception):
    """Base class for expected, user-facing errors."""

    code = "cybercity_error"
    status_code = 400

    def __init__(self, message: str, details: list[Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or []


class NotFoundError(CyberCityError):
    code = "not_found"
    status_code = 404


class InvalidTopologyError(CyberCityError):
    code = "invalid_topology"
    status_code = 422
