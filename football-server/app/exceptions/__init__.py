"""Exception hierarchy for the application."""

from app.exceptions.exceptions import (
    AppException,
    BusinessError,
    ExternalServiceError,
    NotFoundError,
    ValidationError,
)

__all__ = [
    "AppException",
    "BusinessError",
    "ExternalServiceError",
    "NotFoundError",
    "ValidationError",
]
