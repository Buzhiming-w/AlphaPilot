from __future__ import annotations

import os


DEFAULT_POSTGRES_URL = "postgresql+psycopg://alphapilot:alphapilot@localhost:5432/alphapilot"
DEFAULT_REDIS_URL = "redis://localhost:6379/0"
DEFAULT_ADMIN_EMAIL = "admin@alphapilot.dev"
DEFAULT_ADMIN_PASSWORD = "admin"


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


def get_admin_email() -> str:
    return os.getenv("ALPHAPILOT_ADMIN_EMAIL", DEFAULT_ADMIN_EMAIL).strip().lower()


def get_admin_password() -> str:
    return os.getenv("ALPHAPILOT_ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD)


def is_admin_password_configured() -> bool:
    return "ALPHAPILOT_ADMIN_PASSWORD" in os.environ


def is_copilot_llm_enabled() -> bool:
    raw = os.getenv("ALPHAPILOT_COPILOT_LLM_ENABLED")
    if raw is not None:
        return raw.strip().lower() in {"1", "true", "yes", "on"}
    provider = get_copilot_llm_provider()
    key_name = f"{provider.upper()}_API_KEY"
    return bool(os.getenv(key_name))


def get_copilot_llm_provider() -> str:
    return os.getenv("ALPHAPILOT_COPILOT_LLM_PROVIDER") or os.getenv(
        "TRADINGAGENTS_LLM_PROVIDER",
        "deepseek",
    )


def get_copilot_llm_model() -> str:
    return os.getenv("ALPHAPILOT_COPILOT_LLM_MODEL") or os.getenv(
        "TRADINGAGENTS_QUICK_THINK_LLM",
        "deepseek-v4-flash",
    )


def get_report_translation_provider() -> str:
    return os.getenv("ALPHAPILOT_REPORT_TRANSLATION_PROVIDER") or os.getenv(
        "ALPHAPILOT_COPILOT_LLM_PROVIDER"
    ) or os.getenv("TRADINGAGENTS_LLM_PROVIDER", "deepseek")


def get_report_translation_model() -> str:
    return os.getenv("ALPHAPILOT_REPORT_TRANSLATION_MODEL") or os.getenv(
        "ALPHAPILOT_COPILOT_LLM_MODEL"
    ) or os.getenv("TRADINGAGENTS_QUICK_THINK_LLM", "deepseek-v4-flash")


def is_report_translation_enabled() -> bool:
    return os.getenv("ALPHAPILOT_REPORT_TRANSLATION_ENABLED", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def get_report_translation_max_attempts() -> int:
    return int(os.getenv("ALPHAPILOT_REPORT_TRANSLATION_MAX_ATTEMPTS", "3"))


def is_security_master_auto_sync_enabled() -> bool:
    return os.getenv("ALPHAPILOT_SECURITY_MASTER_AUTO_SYNC_ENABLED", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
