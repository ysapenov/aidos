"""
database/db.py — SQLite connection manager and schema initialisation.

Uses aiosqlite for async compatibility with python-telegram-bot's async handlers.
"""

import os
import logging
import aiosqlite
from config import settings
from contextlib import asynccontextmanager

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

CREATE INDEX IF NOT EXISTS idx_history_user_created
    ON translation_history(user_id, created_at);

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

CREATE TABLE IF NOT EXISTS journal_entries (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id            INTEGER NOT NULL,
    title              TEXT NOT NULL,
    category           TEXT NOT NULL,
    summary            TEXT NOT NULL,
    key_points         TEXT,
    action_items       TEXT,
    raw_transcript     TEXT NOT NULL,
    tags               TEXT,
    language           TEXT,
    mood               TEXT,
    energy_level       TEXT,
    duration_seconds   INTEGER,
    telegram_file_id   TEXT,
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(telegram_id)
);

CREATE INDEX IF NOT EXISTS idx_journal_user
    ON journal_entries(user_id);

CREATE INDEX IF NOT EXISTS idx_journal_category
    ON journal_entries(category);

CREATE INDEX IF NOT EXISTS idx_journal_created
    ON journal_entries(created_at);

CREATE TABLE IF NOT EXISTS action_items (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    journal_id      INTEGER,
    task_text       TEXT NOT NULL,
    is_completed    INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at    TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(telegram_id),
    FOREIGN KEY (journal_id) REFERENCES journal_entries(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_action_items_user
    ON action_items(user_id, is_completed);
"""



@asynccontextmanager
async def get_db_context():
    """Context manager that opens a fresh connection per operation.

    Each caller gets its own connection, avoiding global state and
    concurrent access issues with SQLite's single-writer limitation.
    """
    db = await aiosqlite.connect(
        settings.database_path,
        timeout=10.0,
    )
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()


async def init_db() -> None:
    """Create the database file and tables if they don't already exist."""
    db_path = settings.database_path

    # Ensure the data directory exists
    os.makedirs(
        os.path.dirname(db_path) if os.path.dirname(db_path) else ".",
        exist_ok=True,
    )

    async with get_db_context() as db:
        await db.executescript(_SCHEMA)

        # Add kazakh_translation column to existing translation_history table
        try:
            await db.execute(
                "ALTER TABLE translation_history ADD COLUMN kazakh_translation TEXT"
            )
        except aiosqlite.OperationalError:
            pass

        # Migrate journal_entries for mood & energy_level
        for col in ["mood", "energy_level"]:
            try:
                await db.execute(f"ALTER TABLE journal_entries ADD COLUMN {col} TEXT")
            except aiosqlite.OperationalError:
                pass

        await db.commit()

    logger.info("Database initialised at: %s", db_path)
