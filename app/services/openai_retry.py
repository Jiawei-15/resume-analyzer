import logging
import time
from typing import Callable, TypeVar

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    OpenAIError,
    RateLimitError
)

from app.config import (
    get_openai_max_retries,
    get_openai_retry_backoff_seconds
)


LOGGER = logging.getLogger(__name__)
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
T = TypeVar("T")


def is_retryable_openai_error(exc: BaseException) -> bool:
    if isinstance(exc, (APITimeoutError, APIConnectionError, RateLimitError)):
        return True

    if isinstance(exc, APIStatusError):
        return exc.status_code in RETRYABLE_STATUS_CODES

    return False


def call_openai_with_retries(
    operation: Callable[[], T],
    *,
    operation_name: str,
    max_retries: int | None = None,
    backoff_seconds: float | None = None
) -> T:
    retry_limit = (
        get_openai_max_retries()
        if max_retries is None
        else max(max_retries, 0)
    )
    delay = (
        get_openai_retry_backoff_seconds()
        if backoff_seconds is None
        else max(backoff_seconds, 0.0)
    )

    for attempt in range(retry_limit + 1):
        try:
            return operation()
        except OpenAIError as exc:
            if not is_retryable_openai_error(exc) or attempt >= retry_limit:
                raise

            LOGGER.warning(
                "Retrying OpenAI %s after %s (%s/%s).",
                operation_name,
                type(exc).__name__,
                attempt + 1,
                retry_limit
            )

            if delay > 0:
                time.sleep(
                    min(
                        delay * (2 ** attempt),
                        2.0
                    )
                )

    raise RuntimeError("OpenAI retry loop exited unexpectedly.")


def public_openai_error_message(prefix: str, exc: BaseException) -> str:
    return f"{prefix}: {type(exc).__name__}."