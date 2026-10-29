"""Errors raised by the simulation core. The service layer maps them to HTTP errors."""


class NetworkModelError(ValueError):
    """Base class for invalid operations on the modeled network."""


class UnknownDeviceError(NetworkModelError, LookupError):
    def __init__(self, device_id: str) -> None:
        super().__init__(f"Device '{device_id}' does not exist.")
        self.device_id = device_id


class UnknownZoneError(NetworkModelError, LookupError):
    def __init__(self, zone_id: str) -> None:
        super().__init__(f"Zone '{zone_id}' does not exist.")
        self.zone_id = zone_id


class UnknownConnectionError(NetworkModelError, LookupError):
    def __init__(self, connection_id: str) -> None:
        super().__init__(f"Connection '{connection_id}' does not exist.")
        self.connection_id = connection_id


class DuplicateIdentifierError(NetworkModelError):
    def __init__(self, kind: str, identifier: str) -> None:
        super().__init__(f"A {kind} with id '{identifier}' already exists.")
        self.kind = kind
        self.identifier = identifier


class InvalidConnectionError(NetworkModelError):
    """A connection that is well-formed but cannot be added (e.g. a parallel link)."""
