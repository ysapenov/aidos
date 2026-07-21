"""
handlers/history.py — Translation history commands.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from database.models import (
    get_history,
    get_history_count,
    clear_history,
    get_vocabulary_history,
    get_idiom_history,
)
from utils.decorators import restricted
from utils.formatting import (
    format_history,
    format_vocabulary_history,
    format_idiom_history,
)
from utils.constants import HISTORY_EMPTY, HISTORY_CLEARED

logger = logging.getLogger(__name__)


@restricted
async def history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /history — show the user's last 20 translations or sub-histories."""
    user = update.effective_user

    # Handle sub-commands
    if context.args:
        arg = context.args[0].lower()
        if arg == "clear":
            await _handle_clear_history(update, user.id)
            return
        elif arg == "words":
            entries = await get_vocabulary_history(user.id, limit=20)
            message = format_vocabulary_history(entries)
            await update.effective_message.reply_text(message, parse_mode="HTML")
            return
        elif arg == "idioms":
            entries = await get_idiom_history(limit=20)
            message = format_idiom_history(entries)
            await update.effective_message.reply_text(message, parse_mode="HTML")
            return

    # Fetch translation history
    entries = await get_history(user.id, limit=20)
    total_count = await get_history_count(user.id)

    if not entries:
        await update.effective_message.reply_text(HISTORY_EMPTY, parse_mode="HTML")
        return

    message = format_history(entries, total_count)
    await update.effective_message.reply_text(message, parse_mode="HTML")


async def _handle_clear_history(update: Update, user_id: int) -> None:
    """Helper to clear history and notify the user."""
    deleted_count = await clear_history(user_id)
    logger.info("Cleared %s history entries for user %s", deleted_count, user_id)
    await update.effective_message.reply_text(HISTORY_CLEARED, parse_mode="HTML")

@restricted
async def history_words_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.args = ["words"]
    await history(update, context)

@restricted
async def history_idioms_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.args = ["idioms"]
    await history(update, context)
