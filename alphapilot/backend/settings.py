from __future__ import annotations

import os


DEFAULT_POSTGRES_URL = "postgresql+psycopg://alphapilot:alphapilot@localhost:5432/alphapilot"
DEFAULT_REDIS_URL = "redis://localhost:6379/0"


def get_database_url() -> str | None:
    """Return the configured SQL database URL.

    When unset, the API falls back to the in-memory MVP store so imports and
    tests do not require a running PostgreSQL service. Local development should
    set ALPHAPILOT_DATABASE_URL to DEFAULT_POSTGRES_URL via .env or the shell.
    """
    return os.getenv("ALPHAPILOT_DATABASE_URL") or None


def get_redis_url() -> str:
    return os.getenv("ALPHAPILOT_REDIS_URL", DEFAULT_REDIS_URL)


def get_queue_backend() -> str:
    return os.getenv("ALPHAPILOT_QUEUE_BACKEND", "inline").strip().lower()


def is_rate_limit_enabled() -> bool:
    return os.getenv("ALPHAPILOT_RATE_LIMIT_ENABLED", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def get_rate_limit() -> int:
    return int(os.getenv("ALPHAPILOT_RATE_LIMIT", "60"))


def get_rate_limit_window_seconds() -> int:
    return int(os.getenv("ALPHAPILOT_RATE_LIMIT_WINDOW_SECONDS", "60"))
