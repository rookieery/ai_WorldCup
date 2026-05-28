"""Middleware package for the application."""

from app.middleware.cors import add_cors_middleware
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.middleware.logging import LoggingMiddleware

__all__ = [
    "ErrorHandlerMiddleware",
    "LoggingMiddleware",
    "add_cors_middleware",
]
