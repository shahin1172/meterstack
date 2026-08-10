import logging
from contextlib import contextmanager
from typing import Generator

from django.db import connection

logger = logging.getLogger(__name__)


@contextmanager
def managed_cursor() -> Generator:
    """Context manager that provides a database cursor and ensures it is closed."""
    logger.debug("Opening a new database cursor.")
    cursor = connection.cursor()
    try:
        yield cursor
    finally:
        logger.debug("Closing the database cursor.")
        cursor.close()
