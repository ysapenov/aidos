"""
database/models.py — Data access functions (CRUD) for users and translation history.

All functions are async and use aiosqlite.
"""

import json
import logging
from typing import Optional, Union
import aiosqlite
from database.db import get_db_context
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

async def get_vocabulary_history(user_id: int, limit: int = 20) -> list[dict]:
    """Return the most recent vocabulary generations for a user."""
    async with get_db_context() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT entry_type, english_text, russian_text, kazakh_text, topic, created_at
            FROM vocabulary_history
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


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

async def get_idiom_history(limit: int = 20) -> list[dict]:
    """Return the most recent broadcasted idioms."""
    async with get_db_context() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT idiom, russian_equivalent, kazakh_equivalent, sent_at
            FROM idiom_history
            ORDER BY sent_at DESC
            LIMIT ?
            """,
            (limit,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


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


# ─── Journal Entries ──────────────────────────────────────────────────────────


async def add_journal_entry(
    user_id: int,
    title: str,
    category: str,
    summary: str,
    key_points: Union[list[str], str],
    action_items: Union[list[str], str],
    raw_transcript: str,
    tags: Union[list[str], str],
    language: Optional[str] = None,
    mood: Optional[str] = None,
    energy_level: Optional[str] = None,
    duration_seconds: Optional[int] = None,
    telegram_file_id: Optional[str] = None,
) -> int:
    """Save a processed voice note/thought to journal_entries. Returns the new entry ID."""
    if isinstance(key_points, list):
        key_points = json.dumps(key_points, ensure_ascii=False)
    if isinstance(action_items, list):
        action_items = json.dumps(action_items, ensure_ascii=False)
    if isinstance(tags, list):
        tags = json.dumps(tags, ensure_ascii=False)

    async with get_db_context() as db:
        cursor = await db.execute(
            """
            INSERT INTO journal_entries
            (user_id, title, category, summary, key_points, action_items, raw_transcript, tags, language, mood, energy_level, duration_seconds, telegram_file_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                title,
                category,
                summary,
                key_points,
                action_items,
                raw_transcript,
                tags,
                language,
                mood,
                energy_level,
                duration_seconds,
                telegram_file_id,
            ),
        )
        await db.commit()
        return cursor.lastrowid


async def update_journal_category(entry_id: int, user_id: int, new_category: str) -> bool:
    """Update the category for a specific journal entry."""
    async with get_db_context() as db:
        cursor = await db.execute(
            "UPDATE journal_entries SET category = ? WHERE id = ? AND user_id = ?",
            (new_category, entry_id, user_id),
        )
        await db.commit()
        return cursor.rowcount > 0


async def get_journal_entries(
    user_id: int, limit: int = 10, offset: int = 0, category: Optional[str] = None
) -> list[dict]:
    """Return recent journal entries for a user, optionally filtered by category."""
    query = "SELECT * FROM journal_entries WHERE user_id = ?"
    params = [user_id]
    if category:
        query += " AND LOWER(category) = LOWER(?)"
        params.append(category)
    query += " ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    async with get_db_context() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_journal_entry_by_id(entry_id: int, user_id: int) -> Optional[dict]:
    """Retrieve a single journal entry by ID for a user."""
    async with get_db_context() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM journal_entries WHERE id = ? AND user_id = ?",
            (entry_id, user_id),
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def delete_journal_entry(entry_id: int, user_id: int) -> bool:
    """Delete a journal entry by ID. Returns True if deleted."""
    async with get_db_context() as db:
        cursor = await db.execute(
            "DELETE FROM journal_entries WHERE id = ? AND user_id = ?",
            (entry_id, user_id),
        )
        await db.commit()
        return cursor.rowcount > 0


async def get_all_journal_entries(user_id: int) -> list[dict]:
    """Return all journal entries for a user ordered by date, used for CSV export."""
    async with get_db_context() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM journal_entries WHERE user_id = ? ORDER BY created_at ASC, id ASC",
            (user_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_journal_entries_in_range(user_id: int, since_iso: str) -> list[dict]:
    """Retrieve journal entries created since a given timestamp (e.g. for weekly/monthly digests)."""
    async with get_db_context() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM journal_entries WHERE user_id = ? AND created_at >= ? ORDER BY created_at ASC, id ASC",
            (user_id, since_iso),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


# ─── Action Items ─────────────────────────────────────────────────────────────


async def add_action_items(
    user_id: int, items: list[str], journal_id: Optional[int] = None
) -> list[int]:
    """Insert multiple action items extracted from thoughts into the action_items table."""
    if not items:
        return []

    inserted_ids = []
    async with get_db_context() as db:
        for item in items:
            clean_text = item.strip()
            if not clean_text:
                continue
            cursor = await db.execute(
                """
                INSERT INTO action_items (user_id, journal_id, task_text)
                VALUES (?, ?, ?)
                """,
                (user_id, journal_id, clean_text),
            )
            inserted_ids.append(cursor.lastrowid)
        await db.commit()
    return inserted_ids


async def get_action_items(
    user_id: int, include_completed: bool = False, limit: int = 50
) -> list[dict]:
    """Retrieve action items for a user."""
    query = "SELECT * FROM action_items WHERE user_id = ?"
    params = [user_id]
    if not include_completed:
        query += " AND is_completed = 0"
    query += " ORDER BY is_completed ASC, created_at DESC LIMIT ?"
    params.append(limit)

    async with get_db_context() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def toggle_action_item(item_id: int, user_id: int) -> Optional[bool]:
    """
    Toggle completion status of an action item.
    Returns the new is_completed bool, or None if item does not exist.
    """
    async with get_db_context() as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT is_completed FROM action_items WHERE id = ? AND user_id = ?",
            (item_id, user_id),
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            current_status = row["is_completed"]

        new_status = 0 if current_status else 1
        if new_status == 1:
            await db.execute(
                "UPDATE action_items SET is_completed = 1, completed_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
                (item_id, user_id),
            )
        else:
            await db.execute(
                "UPDATE action_items SET is_completed = 0, completed_at = NULL WHERE id = ? AND user_id = ?",
                (item_id, user_id),
            )
        await db.commit()
        return bool(new_status)


async def delete_action_item(item_id: int, user_id: int) -> bool:
    """Delete an action item by ID."""
    async with get_db_context() as db:
        cursor = await db.execute(
            "DELETE FROM action_items WHERE id = ? AND user_id = ?",
            (item_id, user_id),
        )
        await db.commit()
        return cursor.rowcount > 0


async def clear_completed_action_items(user_id: int) -> int:
    """Delete all completed action items for a user. Returns count of deleted items."""
    async with get_db_context() as db:
        cursor = await db.execute(
            "DELETE FROM action_items WHERE user_id = ? AND is_completed = 1",
            (user_id,),
        )
        await db.commit()
        return cursor.rowcount



