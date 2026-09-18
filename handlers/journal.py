"""
handlers/journal.py — Audio thought recording, /notes management, /digest, and Google Sheets sync.

Flow:
    - User sends voice/audio (< 1 min) -> transcribed, structured, categorized, mood & action items saved.
    - /notes         -> browse recent notes with inline action buttons.
    - /notes <id>    -> view full details of a specific note.
    - /notes export  -> downloads all notes as UTF-8 CSV.
    - /notes sync    -> syncs all notes to Google Sheets.
    - /digest        -> weekly reflection digest (or /digest monthly).
"""

import asyncio
import html as _html
import io
import logging
from datetime import datetime, timezone, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from utils.decorators import restricted, send_typing
from utils.constants import (
    AUDIO_TOO_LONG_ERROR,
    AUDIO_TRANSCRIBE_ERROR,
    NOTES_EMPTY,
    DIGEST_EMPTY,
    DIGEST_GENERATING,
    SHEETS_NOT_CONFIGURED,
    EMOJI_SUCCESS,
    EMOJI_ERROR,
    EMOJI_CHART,
)
from utils.formatting import format_journal_card, format_journal_list, format_digest
from services.journal_service import (
    process_audio_thought,
    generate_notes_csv,
    generate_journal_digest,
)
from services.sheets_service import (
    sync_note_to_sheets,
    sync_all_notes_to_sheets,
    is_sheets_configured,
)
from database.models import (
    add_journal_entry,
    get_journal_entries,
    get_journal_entry_by_id,
    delete_journal_entry,
    get_all_journal_entries,
    update_journal_category,
    add_action_items,
    get_journal_entries_in_range,
)

logger = logging.getLogger(__name__)

STANDARD_CATEGORIES = [
    ("💡 Ideas", "Ideas"),
    ("💼 Work", "Work"),
    ("👤 Personal", "Personal"),
    ("📚 Learning", "Learning"),
    ("🏃 Health", "Health"),
    ("📋 To-Do", "To-Do"),
    ("🪞 Reflection", "Reflection"),
    ("📝 Other", "Other"),
]


_background_tasks: set[asyncio.Task] = set()


def _build_note_keyboard(entry_id: int) -> InlineKeyboardMarkup:

    """Standard note action keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("🗑 Delete", callback_data=f"note_del_{entry_id}"),
            InlineKeyboardButton("🏷 Category", callback_data=f"note_cat_{entry_id}"),
        ],
        [
            InlineKeyboardButton("📥 Export CSV", callback_data="notes_export_csv"),
            InlineKeyboardButton("📋 All Notes", callback_data="notes_list"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def _build_category_keyboard(entry_id: int) -> InlineKeyboardMarkup:
    """Category selection keyboard."""
    keyboard = []
    row = []
    for label, cat_name in STANDARD_CATEGORIES:
        row.append(InlineKeyboardButton(label, callback_data=f"note_setcat_{entry_id}_{cat_name}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("« Cancel", callback_data=f"note_view_{entry_id}")])
    return InlineKeyboardMarkup(keyboard)


@restricted
@send_typing
async def handle_audio_thought(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Catch any voice or audio message without requiring a starting command.
    Checks duration (< 60s), transcribes, structures, saves to DB, extracts action items,
    and replies with an interactive card.
    """
    user = update.effective_user
    message = update.effective_message

    # Identify audio source and duration
    if message.voice:
        duration = message.voice.duration or 0
        file_id = message.voice.file_id
        mime_type = message.voice.mime_type or "audio/ogg"
    elif message.audio:
        duration = message.audio.duration or 0
        file_id = message.audio.file_id
        mime_type = message.audio.mime_type or "audio/mpeg"
    else:
        return

    # Strictly enforce 60-second limit
    if duration > 60:
        logger.info("User %s sent audio exceeding limit: %ss", user.id, duration)
        await message.reply_text(
            AUDIO_TOO_LONG_ERROR.format(duration=duration),
            parse_mode="HTML",
        )
        return

    logger.info("User %s sent audio thought (%ss, mime=%s)", user.id, duration, mime_type)

    # Download audio directly in-memory
    try:
        tg_file = await context.bot.get_file(file_id)
        audio_bytes = bytes(await tg_file.download_as_bytearray())
    except Exception as e:
        logger.error("Failed to download audio file from Telegram: %s", e)
        await message.reply_text(AUDIO_TRANSCRIBE_ERROR, parse_mode="HTML")
        return

    # Process and structure using Gemini
    try:
        data = await process_audio_thought(audio_bytes=audio_bytes, mime_type=mime_type)
    except Exception as e:
        logger.error("Error transcribing audio thought: %s", e)
        safe_detail = _html.escape(str(e))
        await message.reply_text(f"{AUDIO_TRANSCRIBE_ERROR}\n\n<i>Detail: {safe_detail}</i>", parse_mode="HTML")
        return

    # Persist in SQLite
    try:
        entry_id = await add_journal_entry(
            user_id=user.id,
            title=data["title"],
            category=data["category"],
            summary=data["summary"],
            key_points=data["key_points"],
            action_items=data["action_items"],
            raw_transcript=data["clean_transcript"],
            tags=data["tags"],
            language=data["language"],
            mood=data.get("mood"),
            energy_level=data.get("energy_level"),
            duration_seconds=duration,
            telegram_file_id=file_id,
        )
    except Exception as e:
        logger.error("Failed to save journal entry to database: %s", e)
        safe_detail = _html.escape(str(e))
        await message.reply_text(
            f"{EMOJI_ERROR} Thought processed but failed to save in database: {safe_detail}",
            parse_mode="HTML",
        )
        return

    # Save extracted action items to action_items table
    action_items_list = data.get("action_items", [])
    if action_items_list:
        try:
            await add_action_items(user.id, action_items_list, journal_id=entry_id)
            logger.info("Saved %d action items for note #%d", len(action_items_list), entry_id)
        except Exception as e:
            logger.error("Failed to save action items: %s", e)

    # Build entry dictionary for formatting
    entry_dict = {
        "id": entry_id,
        "title": data["title"],
        "category": data["category"],
        "summary": data["summary"],
        "key_points": data["key_points"],
        "action_items": data["action_items"],
        "clean_transcript": data["clean_transcript"],
        "tags": data["tags"],
        "language": data["language"],
        "mood": data.get("mood"),
        "energy_level": data.get("energy_level"),
        "duration_seconds": duration,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
    }

    # Background sync to Google Sheets if configured
    if is_sheets_configured():
        task = asyncio.create_task(sync_note_to_sheets(entry_dict))
        _background_tasks.add(task)
        task.add_done_callback(_background_tasks.discard)


    card_text = format_journal_card(entry_dict)
    reply_markup = _build_note_keyboard(entry_id)
    await message.reply_text(card_text, parse_mode="HTML", reply_markup=reply_markup)


@restricted
@send_typing
async def notes_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /notes command:
    - /notes         -> list last 10 notes with action buttons
    - /notes <id>    -> view detailed note card
    - /notes export  -> download notes CSV
    - /notes sync    -> sync all notes to Google Sheets
    """
    user = update.effective_user
    args = context.args or []

    # Subcommand: /notes export
    if args and args[0].lower() == "export":
        await send_csv_export(update, context)
        return

    # Subcommand: /notes sync
    if args and args[0].lower() == "sync":
        await sync_sheets_command(update, context)
        return

    # Subcommand: /notes <id>
    if args and args[0].isdigit():
        entry_id = int(args[0])
        entry = await get_journal_entry_by_id(entry_id, user.id)
        if not entry:
            await update.effective_message.reply_text(
                f"{EMOJI_ERROR} Note <b>#{entry_id}</b> not found.",
                parse_mode="HTML",
            )
            return

        card_text = format_journal_card(entry)
        reply_markup = _build_note_keyboard(entry_id)
        await update.effective_message.reply_text(
            card_text,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )
        return

    # Default: list recent notes
    entries = await get_journal_entries(user.id, limit=10)
    if not entries:
        await update.effective_message.reply_text(NOTES_EMPTY, parse_mode="HTML")
        return

    list_text = format_journal_list(entries)
    keyboard = [
        [
            InlineKeyboardButton("📥 Export CSV", callback_data="notes_export_csv"),
            InlineKeyboardButton("🔄 Sync Sheets", callback_data="notes_sync_sheets"),
        ]
    ]
    await update.effective_message.reply_text(
        list_text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def send_csv_export(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Export all journal entries for the current user as a CSV document."""
    user = update.effective_user
    chat_id = update.effective_chat.id

    entries = await get_all_journal_entries(user.id)
    if not entries:
        await update.effective_message.reply_text(NOTES_EMPTY, parse_mode="HTML")
        return

    csv_text = generate_notes_csv(entries)
    csv_bytes = io.BytesIO(csv_text.encode("utf-8"))
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filename = f"notes_{today}.csv"

    await context.bot.send_document(
        chat_id=chat_id,
        document=csv_bytes,
        filename=filename,
        caption=f"📝 Exported <b>{len(entries)}</b> thought note(s) as CSV.",
        parse_mode="HTML",
    )


async def sync_sheets_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sync all thoughts to Google Sheets."""
    user = update.effective_user
    if not is_sheets_configured():
        await update.effective_message.reply_text(SHEETS_NOT_CONFIGURED, parse_mode="HTML")
        return

    entries = await get_all_journal_entries(user.id)
    if not entries:
        await update.effective_message.reply_text(NOTES_EMPTY, parse_mode="HTML")
        return

    msg = await update.effective_message.reply_text("🔄 Syncing notes with Google Sheets...", parse_mode="HTML")
    count = await sync_all_notes_to_sheets(entries)
    if count > 0:
        await msg.edit_text(
            f"{EMOJI_SUCCESS} Successfully synced <b>{count}</b> note(s) to Google Sheets!",
            parse_mode="HTML",
        )
    else:
        await msg.edit_text(
            f"{EMOJI_ERROR} Could not sync notes to Google Sheets. Check logs for details.",
            parse_mode="HTML",
        )


@restricted
@send_typing
async def digest_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /digest command:
    - /digest         -> weekly digest of thoughts from last 7 days
    - /digest monthly -> monthly digest from last 30 days
    """
    user = update.effective_user
    args = context.args or []

    period_type = args[0].lower() if args else "weekly"
    days = 30 if period_type == "monthly" else 7
    period_title = "Monthly Digest" if period_type == "monthly" else "Weekly Digest"

    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    entries = await get_journal_entries_in_range(user.id, cutoff)

    if not entries:
        await update.effective_message.reply_text(DIGEST_EMPTY, parse_mode="HTML")
        return

    status_msg = await update.effective_message.reply_text(DIGEST_GENERATING, parse_mode="HTML")

    try:
        digest_data = await generate_journal_digest(entries, period_name=period_title)
        formatted_text = format_digest(digest_data, period_name=period_title)
        await status_msg.edit_text(formatted_text, parse_mode="HTML")
    except Exception as e:
        logger.error("Failed to generate digest: %s", e)
        safe_e = _html.escape(str(e))
        await status_msg.edit_text(
            f"{EMOJI_ERROR} Failed to generate digest: {safe_e}",
            parse_mode="HTML",
        )


async def send_weekly_digest(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Scheduled job: Send weekly digest every Sunday to users with recent entries."""
    logger.info("Running scheduled weekly digest job...")
    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")


    from database.db import get_db_context
    async with get_db_context() as db:
        async with db.execute(
            "SELECT DISTINCT user_id FROM journal_entries WHERE created_at >= ?",
            (cutoff,),
        ) as cursor:
            rows = await cursor.fetchall()
            active_users = [row["user_id"] for row in rows]

    logger.info("Found %d active journal users for weekly digest", len(active_users))

    for user_id in active_users:
        try:
            entries = await get_journal_entries_in_range(user_id, cutoff)
            if not entries:
                continue
            digest_data = await generate_journal_digest(entries, period_name="Weekly Digest")
            text = format_digest(digest_data, period_name="Weekly Digest")
            await context.bot.send_message(chat_id=user_id, text=text, parse_mode="HTML")
            logger.info("Sent weekly digest to user %d", user_id)
        except Exception as e:
            logger.error("Failed to send scheduled digest to user %d: %s", user_id, e)


async def notes_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline button clicks for journal notes."""
    query = update.callback_query
    if not query:
        return

    await query.answer()
    data = query.data
    user = update.effective_user

    if data == "notes_export_csv":
        await send_csv_export(update, context)
        return

    if data == "notes_sync_sheets":
        await sync_sheets_command(update, context)
        return

    if data == "notes_list":
        entries = await get_journal_entries(user.id, limit=10)
        if not entries:
            await query.edit_message_text(NOTES_EMPTY, parse_mode="HTML")
            return
        list_text = format_journal_list(entries)
        keyboard = [
            [
                InlineKeyboardButton("📥 Export CSV", callback_data="notes_export_csv"),
                InlineKeyboardButton("🔄 Sync Sheets", callback_data="notes_sync_sheets"),
            ]
        ]
        await query.edit_message_text(
            list_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    # Delete Note: note_del_<id>
    if data.startswith("note_del_"):
        try:
            entry_id = int(data.split("_")[-1])
        except ValueError:
            return

        success = await delete_journal_entry(entry_id, user.id)
        if success:
            await query.edit_message_text(
                f"{EMOJI_SUCCESS} Note <b>#{entry_id}</b> has been deleted.",
                parse_mode="HTML",
            )
        else:
            await query.edit_message_text(
                f"{EMOJI_ERROR} Could not delete note #{entry_id} (it may already be deleted).",
                parse_mode="HTML",
            )
        return

    # Category Picker Menu: note_cat_<id>
    if data.startswith("note_cat_"):
        try:
            entry_id = int(data.split("_")[-1])
        except ValueError:
            return

        entry = await get_journal_entry_by_id(entry_id, user.id)
        if not entry:
            await query.edit_message_text(f"{EMOJI_ERROR} Note not found.", parse_mode="HTML")
            return

        cat_keyboard = _build_category_keyboard(entry_id)
        await query.edit_message_reply_markup(reply_markup=cat_keyboard)
        return

    # Select Category: note_setcat_<id>_<category>
    if data.startswith("note_setcat_"):
        parts = data.split("_", 3)
        try:
            entry_id = int(parts[2])
            new_cat = parts[3]
        except (IndexError, ValueError):
            return

        await update_journal_category(entry_id, user.id, new_cat)
        entry = await get_journal_entry_by_id(entry_id, user.id)
        if not entry:
            return

        card_text = format_journal_card(entry)
        reply_markup = _build_note_keyboard(entry_id)
        await query.edit_message_text(card_text, parse_mode="HTML", reply_markup=reply_markup)
        return

    # View note (e.g. from cancel): note_view_<id>
    if data.startswith("note_view_"):
        try:
            entry_id = int(data.split("_")[-1])
        except ValueError:
            return

        entry = await get_journal_entry_by_id(entry_id, user.id)
        if not entry:
            return

        card_text = format_journal_card(entry)
        reply_markup = _build_note_keyboard(entry_id)
        await query.edit_message_text(card_text, parse_mode="HTML", reply_markup=reply_markup)
        return
