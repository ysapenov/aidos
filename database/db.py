"""
database/db.py — SQLite connection manager and schema initialisation.

Uses aiosqlite for async compatibility with python-telegram-bot's async handlers.
"""

import os
import logging
import aiosqlite
from config import settings

logger = logging.getLogger(__name__)

# ─── Schema ────────────────────────────────────────────────────────────────────

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    telegram_id   INTEGER PRIMARY KEY,
    username      TEXT,
    first_name    TEXT,
    is_allowed    INTEGER NOT NULL DEFAULT 0,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS translation_history (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL,
    word          TEXT NOT NULL,
    translation   TEXT NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(telegram_id)
);

CREATE INDEX IF NOT EXISTS idx_history_user
    ON translation_history(user_id);

CREATE INDEX IF NOT EXISTS idx_history_created
    ON translation_history(created_at);
"""


async def init_db() -> None:
    """Create the database file and tables if they don't already exist."""
    db_path = settings.database_path

    # Ensure the data directory exists
    os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)

    async with aiosqlite.connect(db_path) as db:
        await db.executescript(_SCHEMA)
        await db.commit()

    logger.info(f"Database initialised at: {db_path}")


def get_db_path() -> str:
    """Return the configured database path."""
    return settings.database_path
