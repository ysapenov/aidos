"""
database/models.py — Data access functions (CRUD) for users and translation history.

All functions are async and use aiosqlite.
"""

import logging
from typing import Optional
import aiosqlite
from database.db import get_db_path, get_db_context
from config import settings

logger = logging.getLogger(__name__)


# ─── User helpers ──────────────────────────────────────────────────────────────


async def upsert_user(
    telegram_id: int, username: Optional[str], first_name: Optional[str]
) -> None:
    """Insert or update a user record. Called on every /start."""
    async with get_db_context() as db:
        await db.execute(
            """
            INSERT INTO users (telegram_id, username, first_name, is_allowed)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username   = excluded.username,
                first_name = excluded.first_name
            """,
            (telegram_id, username, first_name, 0),
        )
        await db.commit()


async def is_user_allowed(user_id: int) -> bool:
    """Return True if user_id is in the static env whitelist OR the DB whitelist."""
    # Check static config first (fast path)
    if user_id in settings.allowed_user_ids:
        return True

    # Check DB whitelist (users added via /allow command)
    async with get_db_context() as db:
        async with db.execute(
            "SELECT is_allowed FROM users WHERE telegram_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return bool(row and row[0])


async def add_allowed_user(
    telegram_id: int, username: Optional[str], first_name: Optional[str]
) -> None:
    """Grant access to a user (admin /allow command). Persists to DB."""
    async with get_db_context() as db:
        await db.execute(
            """
            INSERT INTO users (telegram_id, username, first_name, is_allowed)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(telegram_id) DO UPDATE SET
                is_allowed = 1,
                username   = excluded.username,
                first_name = excluded.first_name
            """,
            (telegram_id, username, first_name),
        )
        await db.commit()
    logger.info("Granted access to user %s (@%s)", telegram_id, username)


async def remove_allowed_user(telegram_id: int) -> bool:
    """Revoke access from a user (admin /revoke command). Returns True if user existed."""
    async with get_db_context() as db:
        cursor = await db.execute(
            "UPDATE users SET is_allowed = 0 WHERE telegram_id = ?",
            (telegram_id,),
        )
        await db.commit()
        affected = cursor.rowcount

    logger.info("Revoked access from user %s", telegram_id)
    return affected > 0


async def list_allowed_users() -> list[dict]:
    """Return all users with is_allowed = 1 (DB only, not static env list)."""
    async with get_db_context() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT telegram_id, username, first_name, created_at
            FROM users
            WHERE is_allowed = 1
            ORDER BY created_at ASC
            """
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


# ─── Translation history ───────────────────────────────────────────────────────


async def add_translation(
    user_id: int, word: str, translation: str, kazakh_translation: Optional[str] = None
) -> None:
    """
    Save a translation to history and enforce the per-user history cap.
    Oldest entries are deleted if the cap is exceeded.
    """
    async with get_db_context() as db:
        # Insert new entry
        await db.execute(
            "INSERT INTO translation_history (user_id, word, translation, kazakh_translation) VALUES (?, ?, ?, ?)",
            (user_id, word, translation, kazakh_translation),
        )

        # Enforce cap: delete oldest entries beyond the limit
        await db.execute(
            """
            DELETE FROM translation_history
            WHERE id IN (
                SELECT id FROM translation_history
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT -1 OFFSET ?
            )
            """,
            (user_id, settings.history_cap),
        )

        await db.commit()


async def get_history(user_id: int, limit: int = 20) -> list[dict]:
    """Return the most recent `limit` translations for a user."""
    async with get_db_context() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT word, translation, kazakh_translation, created_at
            FROM translation_history
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_history_count(user_id: int) -> int:
    """Return total number of translations saved for a user."""
    async with get_db_context() as db:
        async with db.execute(
            "SELECT COUNT(*) FROM translation_history WHERE user_id = ?",
            (user_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


async def clear_history(user_id: int) -> int:
    """Delete all translation history for a user. Returns number of rows deleted."""
    async with get_db_context() as db:
        cursor = await db.execute(
            "DELETE FROM translation_history WHERE user_id = ?", (user_id,)
        )
        await db.commit()
        return cursor.rowcount


# ─── Vocabulary history ────────────────────────────────────────────────────────


async def save_vocabulary_entry(
    user_id: int,
    entry_type: str,
    english_text: str,
    russian_text: Optional[str] = None,
    kazakh_text: Optional[str] = None,
    topic: Optional[str] = None,
) -> None:
    """Save a generated vocabulary word/phrase to history."""
    async with get_db_context() as db:
        await db.execute(
            """
            INSERT INTO vocabulary_history
            (user_id, entry_type, english_text, russian_text, kazakh_text, topic)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, entry_type, english_text, russian_text, kazakh_text, topic),
        )
        await db.commit()


async def get_vocabulary_words(user_id: int) -> list[str]:
    """Return all previously generated english words/phrases for a user."""
    async with get_db_context() as db:
        async with db.execute(
            "SELECT english_text FROM vocabulary_history WHERE user_id = ?", (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]


# ─── Idiom history ─────────────────────────────────────────────────────────────


async def save_idiom(
    idiom: str,
    russian_equivalent: Optional[str] = None,
    kazakh_equivalent: Optional[str] = None,
) -> None:
    """Save a sent daily idiom to history."""
    async with get_db_context() as db:
        await db.execute(
            """
            INSERT INTO idiom_history (idiom, russian_equivalent, kazakh_equivalent)
            VALUES (?, ?, ?)
            """,
            (idiom, russian_equivalent, kazakh_equivalent),
        )
        await db.commit()


async def get_sent_idioms() -> list[str]:
    """Return all previously sent idioms."""
    async with get_db_context() as db:
        async with db.execute("SELECT idiom FROM idiom_history") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]


# ─── Idiom Subscriptions ───────────────────────────────────────────────────────


async def subscribe_user(user_id: int) -> None:
    """Subscribe a user to the daily idiom (ignores if already subscribed)."""
    async with get_db_context() as db:
        await db.execute(
            "INSERT OR IGNORE INTO idiom_subscribers (user_id) VALUES (?)", (user_id,)
        )
        await db.commit()


async def unsubscribe_user(user_id: int) -> bool:
    """Unsubscribe a user from the daily idiom. Returns True if affected."""
    async with get_db_context() as db:
        cursor = await db.execute(
            "DELETE FROM idiom_subscribers WHERE user_id = ?", (user_id,)
        )
        await db.commit()
        return cursor.rowcount > 0


async def is_subscribed(user_id: int) -> bool:
    """Check if a user is subscribed to the daily idiom."""
    async with get_db_context() as db:
        async with db.execute(
            "SELECT 1 FROM idiom_subscribers WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return bool(row)


async def get_subscribed_user_ids() -> list[int]:
    """Return list of all subscribed user IDs."""
    async with get_db_context() as db:
        async with db.execute("SELECT user_id FROM idiom_subscribers") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
