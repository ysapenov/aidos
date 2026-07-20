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

CREATE TABLE IF NOT EXISTS vocabulary_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    entry_type      TEXT NOT NULL,  -- 'word', 'phrasal_verb', 'expression'
    english_text    TEXT NOT NULL,
    russian_text    TEXT,
    kazakh_text     TEXT,
    topic           TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(telegram_id)
);

CREATE INDEX IF NOT EXISTS idx_vocab_user
    ON vocabulary_history(user_id);

CREATE TABLE IF NOT EXISTS idiom_history (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    idiom               TEXT NOT NULL,
    russian_equivalent  TEXT,
    kazakh_equivalent   TEXT,
    sent_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS idiom_subscribers (
    user_id     INTEGER PRIMARY KEY,
    subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(telegram_id)
);
"""


async def init_db() -> None:
    """Create the database file and tables if they don't already exist."""
    db_path = settings.database_path

    # Ensure the data directory exists
    os.makedirs(
        os.path.dirname(db_path) if os.path.dirname(db_path) else ".",
        exist_ok=True,
    )

    async with aiosqlite.connect(db_path) as db:
        await db.executescript(_SCHEMA)

        # Add kazakh_translation column to existing translation_history table
        try:
            await db.execute(
                "ALTER TABLE translation_history ADD COLUMN kazakh_translation TEXT"
            )
        except aiosqlite.OperationalError:
            # Column already exists or other schema error we can ignore
            pass

        await db.commit()

    logger.info(f"Database initialised at: {db_path}")


def get_db_path() -> str:
    """Return the configured database path."""
    return settings.database_path
