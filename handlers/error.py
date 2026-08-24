"""
handlers/error.py — Global error handler.

Catches all unhandled exceptions, logs the full traceback,
and sends a user-friendly message to the chat.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from utils.constants import EMOJI_ERROR

logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors and notify the user gracefully."""
    logger.error("Unhandled exception:", exc_info=context.error)

    # Try to notify the user
    if isinstance(update, Update) and update.effective_message:
        try:
            error_text = f"{EMOJI_ERROR} Error: {context.error}"
            await update.effective_message.reply_text(error_text, parse_mode=None)
        except Exception:
            pass  # Don't raise inside an error handler
