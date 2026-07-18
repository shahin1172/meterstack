import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError

from rest_framework import status
from rest_framework.exceptions import (
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Global exception handler for the API.
    """

    response = exception_handler(exc, context)

    if response is not None:
        return response

    if isinstance(exc, IntegrityError):
        logger.exception("Database integrity error.")

        return Response(
            {
                "detail": (
                    "The requested operation violates a database constraint."
                )
            },
            status=status.HTTP_409_CONFLICT,
        )

    if isinstance(exc, (ValidationError, DjangoValidationError)):
        logger.warning("Validation error: %s", exc)

        return Response(
            {
                "detail": "Validation failed.",
                "errors": getattr(exc, "detail", str(exc)),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if isinstance(exc, AuthenticationFailed):
        logger.warning("Authentication failed.")

        return Response(
            {
                "detail": "Authentication failed."
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if isinstance(exc, NotAuthenticated):
        logger.warning("Authentication credentials were not provided.")

        return Response(
            {
                "detail": "Authentication credentials were not provided."
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if isinstance(exc, PermissionDenied):
        logger.warning("Permission denied.")

        return Response(
            {
                "detail": "You do not have permission to perform this action."
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    logger.exception(
        "Unhandled exception.",
        exc_info=exc,
    )

    return Response(
        {
            "detail": "An unexpected internal server error occurred."
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )