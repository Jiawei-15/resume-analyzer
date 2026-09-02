import os
from dotenv import load_dotenv

load_dotenv()


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
USE_OPENAI_EMBEDDINGS = os.getenv("USE_OPENAI_EMBEDDINGS", "False") == "True"

MAX_UPLOAD_BYTES_ENV_VAR = "AI_RECRUITMENT_COPILOT_MAX_UPLOAD_BYTES"
MAX_RESUME_TEXT_CHARS_ENV_VAR = "AI_RECRUITMENT_COPILOT_MAX_RESUME_TEXT_CHARS"
MAX_JOB_DESCRIPTION_CHARS_ENV_VAR = "AI_RECRUITMENT_COPILOT_MAX_JOB_DESCRIPTION_CHARS"
OPENAI_TIMEOUT_SECONDS_ENV_VAR = "AI_RECRUITMENT_COPILOT_OPENAI_TIMEOUT_SECONDS"
OPENAI_MAX_RETRIES_ENV_VAR = "AI_RECRUITMENT_COPILOT_OPENAI_MAX_RETRIES"
OPENAI_RETRY_BACKOFF_SECONDS_ENV_VAR = "AI_RECRUITMENT_COPILOT_OPENAI_RETRY_BACKOFF_SECONDS"

DEFAULT_MAX_UPLOAD_BYTES = 5 * 1024 * 1024
DEFAULT_MAX_RESUME_TEXT_CHARS = 100_000
DEFAULT_MAX_JOB_DESCRIPTION_CHARS = 20_000
DEFAULT_OPENAI_TIMEOUT_SECONDS = 20.0
DEFAULT_OPENAI_MAX_RETRIES = 1
DEFAULT_OPENAI_RETRY_BACKOFF_SECONDS = 0.25
UPLOAD_READ_CHUNK_BYTES = 64 * 1024


def _get_int_env(name: str, default: int, minimum: int) -> int:
    raw_value = os.getenv(name)

    if raw_value is None:
        return default

    try:
        value = int(raw_value)
    except ValueError:
        return default

    return max(value, minimum)


def _get_float_env(name: str, default: float, minimum: float) -> float:
    raw_value = os.getenv(name)

    if raw_value is None:
        return default

    try:
        value = float(raw_value)
    except ValueError:
        return default

    return max(value, minimum)


def get_max_upload_bytes() -> int:
    return _get_int_env(
        MAX_UPLOAD_BYTES_ENV_VAR,
        DEFAULT_MAX_UPLOAD_BYTES,
        1
    )


def get_max_resume_text_chars() -> int:
    return _get_int_env(
        MAX_RESUME_TEXT_CHARS_ENV_VAR,
        DEFAULT_MAX_RESUME_TEXT_CHARS,
        1
    )


def get_max_job_description_chars() -> int:
    return _get_int_env(
        MAX_JOB_DESCRIPTION_CHARS_ENV_VAR,
        DEFAULT_MAX_JOB_DESCRIPTION_CHARS,
        1
    )


def get_openai_timeout_seconds() -> float:
    return _get_float_env(
        OPENAI_TIMEOUT_SECONDS_ENV_VAR,
        DEFAULT_OPENAI_TIMEOUT_SECONDS,
        0.1
    )


def get_openai_max_retries() -> int:
    return _get_int_env(
        OPENAI_MAX_RETRIES_ENV_VAR,
        DEFAULT_OPENAI_MAX_RETRIES,
        0
    )


def get_openai_retry_backoff_seconds() -> float:
    return _get_float_env(
        OPENAI_RETRY_BACKOFF_SECONDS_ENV_VAR,
        DEFAULT_OPENAI_RETRY_BACKOFF_SECONDS,
        0.0
    )