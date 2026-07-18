import logging
import random
import time
from functools import wraps
from typing import Any, Callable, TypeVar

from django.db import IntegrityError, OperationalError

logger = logging.getLogger(__name__)

RT = TypeVar("RT")


def retry_on_deadlock(
    max_retries: int = 3,
    initial_backoff: float = 0.1,
    max_jitter: float = 0.05,
) -> Callable:
    """
    Retry a database operation when a deadlock or serialization failure occurs.

    Features:
    - Exponential backoff
    - Random jitter
    - Structured logging
    - Reusable decorator
    """

    def decorator(func: Callable[..., RT]) -> Callable[..., RT]:

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> RT:
            last_exception = None

            for attempt in range(max_retries + 1):

                try:
                    return func(*args, **kwargs)

                except (OperationalError, IntegrityError) as exc:
                    last_exception = exc

                    message = str(exc).lower()

                    is_retryable = any(
                        error in message
                        for error in (
                            "deadlock",
                            "could not serialize",
                            "serialization failure",
                            "lock timeout",
                        )
                    )

                    if not is_retryable:
                        raise

                    if attempt >= max_retries:
                        logger.exception(
                            "Database operation failed after %s retries.",
                            max_retries,
                        )
                        raise

                    backoff = initial_backoff * (2 ** attempt)
                    jitter = random.uniform(0, max_jitter)

                    sleep_time = backoff + jitter

                    logger.warning(
                        (
                            "Retrying database operation "
                            "(attempt %s/%s) "
                            "after %.3f seconds."
                        ),
                        attempt + 1,
                        max_retries,
                        sleep_time,
                    )

                    time.sleep(sleep_time)

            raise last_exception

        return wrapper

    return decorator