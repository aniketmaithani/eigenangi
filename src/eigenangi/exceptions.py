class EigenangiError(Exception):
    """Base exception for this library."""


class CredentialsNotFound(EigenangiError):
    """Raised when AWS credentials or region are missing."""


class PermissionDenied(EigenangiError):
    """Raised when AWS denies access to a resource."""


class ServiceUnavailable(EigenangiError):
    """Raised on transient AWS errors (throttling, outages)."""
