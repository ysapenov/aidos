"""
handlers/core.py — Core commands: /start, /help, /menu.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from database.models import upsert_user
from utils.decorators import restricted
from utils.constants import WELCOME_MESSAGE, HELP_MESSAGE

logger = logging.getLogger(__name__)


@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start — welcome the user and upsert their record."""
    user = update.effective_user

    # Save/update user in DB
    await upsert_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
    )

    name = user.first_name or user.username or "there"
    await update.effective_message.reply_text(
        WELCOME_MESSAGE.format(name=name),
        parse_mode="HTML",
    )
    logger.info(f"User {user.id} (@{user.username}) started the bot.")


@restricted
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help — show all available commands."""
    await update.effective_message.reply_text(HELP_MESSAGE, parse_mode="HTML")


@restricted
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /menu — show an inline keyboard with quick-access buttons."""
    keyboard = [
        [
            InlineKeyboardButton("🔤 Translate", callback_data="translate"),
            InlineKeyboardButton("📖 History", callback_data="history"),
        ],
        [
            InlineKeyboardButton("❓ Help", callback_data="help"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.effective_message.reply_text(
        "🤖 <b>Aidos Menu</b>\n\nChoose an option:",
        parse_mode="HTML",
        reply_markup=reply_markup,
    )

@restricted
async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries from the /menu inline keyboard."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "help":
        await help_command(update, context)
    elif query.data == "history":
        from handlers.history import history
        await history(update, context)
