"""
handlers/error.py — Global error handler.

Catches all unhandled exceptions, logs the full traceback,
and sends a user-friendly message to the chat.
"""

import logging
import traceback
from telegram import Update
from telegram.ext import ContextTypes
from utils.constants import ERROR_GENERIC

logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors and notify the user gracefully."""
    logger.error("Unhandled exception:", exc_info=context.error)

    # Try to notify the user
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                ERROR_GENERIC, parse_mode="HTML"
            )
        except Exception:
            pass  # Don't raise inside an error handler
