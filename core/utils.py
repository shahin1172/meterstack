# core/prac_utils.py
import logging
from contextlib import contextmanager
from typing import Generator
from django.db import connection

logger = logging.getLogger(__name__)


@contextmanager
def managed_cursor() -> Generator:
    """
    Context manager that provides a database cursor and ensures it is closed
    after use, even if an error occurs.
    """
    logger.debug("Opening a new database cursor.")
    cursor = connection.cursor()          # 1. Open the cursor
    try:
        yield cursor                      # 2. Give the cursor to the caller
    finally:
        logger.debug("Closing the database cursor.")
        cursor.close()                    # 3. Always close the cursor