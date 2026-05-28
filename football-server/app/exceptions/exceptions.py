"""Custom exception hierarchy for the application.

All business / validation / infrastructure errors inherit from AppException
so the global error-handler middleware can convert them into a unified
ApiResponse format.
"""

from __future__ import annotations


class AppException(Exception):
    """Base application exception.

    Attributes:
        code: HTTP-equivalent numeric error code (e.g. 400, 404, 500).
        message: Human-readable error description.
    """

    def __init__(self, code: int = 500, message: str = "Internal server error") -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class NotFoundError(AppException):
    """Raised when a requested resource cannot be found."""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(code=404, message=message)


class ValidationError(AppException):
    """Raised when request input fails validation rules."""

    def __init__(self, message: str = "Validation error") -> None:
        super().__init__(code=422, message=message)


class BusinessError(AppException):
    """Raised when a business rule is violated."""

    def __init__(self, message: str = "Business rule violation") -> None:
        super().__init__(code=400, message=message)


class ExternalServiceError(AppException):
    """Raised when a call to an external service (AI, data provider) fails."""

    def __init__(self, message: str = "External service unavailable") -> None:
        super().__init__(code=502, message=message)
