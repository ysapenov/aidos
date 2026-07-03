"""
handlers/history.py — Translation history commands.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from database.models import get_history, get_history_count, clear_history
from utils.decorators import restricted
from utils.formatting import format_history
from utils.constants import HISTORY_EMPTY, HISTORY_CLEARED

logger = logging.getLogger(__name__)


@restricted
async def history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /history — show the user's last 20 translations."""
    user = update.effective_user

    # Handle /history clear
    if context.args and context.args[0].lower() == "clear":
        await _handle_clear_history(update, user.id)
        return

    # Fetch history
    entries = await get_history(user.id, limit=20)
    total_count = await get_history_count(user.id)

    if not entries:
        await update.message.reply_text(HISTORY_EMPTY, parse_mode="HTML")
        return

    message = format_history(entries, total_count)
    await update.message.reply_text(message, parse_mode="HTML")


async def _handle_clear_history(update: Update, user_id: int) -> None:
    """Helper to clear history and notify the user."""
    deleted_count = await clear_history(user_id)
    logger.info(f"Cleared {deleted_count} history entries for user {user_id}")
    await update.message.reply_text(HISTORY_CLEARED, parse_mode="HTML")
