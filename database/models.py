"""
database/models.py — Data access functions (CRUD) for users and translation history.

All functions are async and use aiosqlite.
"""

import logging
from datetime import datetime
from typing import Optional
import aiosqlite
from database.db import get_db_path
from config import settings

logger = logging.getLogger(__name__)


# ─── User helpers ──────────────────────────────────────────────────────────────

async def upsert_user(telegram_id: int, username: Optional[str], first_name: Optional[str]) -> None:
    """Insert or update a user record. Called on every /start."""
    async with aiosqlite.connect(get_db_path()) as db:
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
    async with aiosqlite.connect(get_db_path()) as db:
        async with db.execute(
            "SELECT is_allowed FROM users WHERE telegram_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return bool(row and row[0])


async def add_allowed_user(telegram_id: int, username: Optional[str], first_name: Optional[str]) -> None:
    """Grant access to a user (admin /allow command). Persists to DB."""
    async with aiosqlite.connect(get_db_path()) as db:
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
    logger.info(f"Granted access to user {telegram_id} (@{username})")


async def remove_allowed_user(telegram_id: int) -> bool:
    """Revoke access from a user (admin /revoke command). Returns True if user existed."""
    async with aiosqlite.connect(get_db_path()) as db:
        cursor = await db.execute(
            "UPDATE users SET is_allowed = 0 WHERE telegram_id = ?", (telegram_id,)
        )
        await db.commit()
        affected = cursor.rowcount

    logger.info(f"Revoked access from user {telegram_id}")
    return affected > 0


async def list_allowed_users() -> list[dict]:
    """Return all users with is_allowed = 1 (DB only, not static env list)."""
    async with aiosqlite.connect(get_db_path()) as db:
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

async def add_translation(user_id: int, word: str, translation: str) -> None:
    """
    Save a translation to history and enforce the per-user history cap.
    Oldest entries are deleted if the cap is exceeded.
    """
    async with aiosqlite.connect(get_db_path()) as db:
        # Insert new entry
        await db.execute(
            "INSERT INTO translation_history (user_id, word, translation) VALUES (?, ?, ?)",
            (user_id, word, translation),
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
    async with aiosqlite.connect(get_db_path()) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT word, translation, created_at
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
    async with aiosqlite.connect(get_db_path()) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM translation_history WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


async def clear_history(user_id: int) -> int:
    """Delete all translation history for a user. Returns number of rows deleted."""
    async with aiosqlite.connect(get_db_path()) as db:
        cursor = await db.execute(
            "DELETE FROM translation_history WHERE user_id = ?", (user_id,)
        )
        await db.commit()
        return cursor.rowcount
