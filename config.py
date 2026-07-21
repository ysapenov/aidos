"""
config.py — Centralised configuration for the Aidos bot.

Loads all settings from environment variables (via .env file).
Import `settings` from this module anywhere in the project.
"""

import os
import logging
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


def _parse_id_list(env_var: str) -> set[int]:
    """Parse a comma-separated string of integers from an env var."""
    raw = os.getenv(env_var, "")
    ids = set()
    for item in raw.split(","):
        item = item.strip()
        if item:
            try:
                ids.add(int(item))
            except ValueError:
                logging.warning(f"Invalid ID in {env_var}: '{item}' — skipping.")
    return ids


@dataclass
class Settings:
    # Telegram
    telegram_token: str = field(
        default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", "")
    )

    # Google Gemini
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    gemini_model: str = "gemini-2.5-flash"

    # Access control
    allowed_user_ids: set[int] = field(
        default_factory=lambda: _parse_id_list("ALLOWED_USER_IDS")
    )
    admin_user_ids: set[int] = field(
        default_factory=lambda: _parse_id_list("ADMIN_USER_IDS")
    )

    # Database
    database_path: str = field(
        default_factory=lambda: os.getenv("DATABASE_PATH", "data/aidos.db")
    )

    # History cap per user
    history_cap: int = 1000

    # Logging
    log_level: str = field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper()
    )

    def validate(self) -> None:
        """Raise ValueError if required settings are missing."""
        if not self.telegram_token:
            raise ValueError("TELEGRAM_BOT_TOKEN is not set in .env")
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is not set in .env")
        if not self.allowed_user_ids:
            raise ValueError("ALLOWED_USER_IDS is not set in .env")
        if not self.admin_user_ids:
            raise ValueError("ADMIN_USER_IDS is not set in .env")


# Singleton — import this everywhere
settings = Settings()
