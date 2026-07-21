"""
handlers/core.py — Core commands: /start, /help, /menu.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database.models import upsert_user, is_subscribed
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
    logger.info("User %s (@%s) started the bot.", user.id, user.username)


@restricted
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help — show all available commands."""
    await update.effective_message.reply_text(HELP_MESSAGE, parse_mode="HTML")


@restricted
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /menu — show an inline keyboard with quick-access buttons."""
    user = update.effective_user
    subscribed = await is_subscribed(user.id)
    
    keyboard = [
        [
            InlineKeyboardButton("🔤 Translate", callback_data="translate"),
            InlineKeyboardButton("📚 Words", callback_data="words"),
        ],
        [
            InlineKeyboardButton("📖 History", callback_data="history"),
            InlineKeyboardButton("📖 History Words", callback_data="history_words"),
        ],
        [
            InlineKeyboardButton("📖 History Idioms", callback_data="history_idioms"),
            InlineKeyboardButton("🎯 Unsubscribe" if subscribed else "🎯 Subscribe", callback_data="unsubscribe" if subscribed else "subscribe"),
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
    elif query.data == "history_words":
        from handlers.history import history
        context.args = ["words"]
        await history(update, context)
    elif query.data == "history_idioms":
        from handlers.history import history
        context.args = ["idioms"]
        await history(update, context)
    elif query.data == "words":
        from handlers.vocabulary import words
        await words(update, context)
    elif query.data == "subscribe":
        from handlers.idiom import subscribe
        await subscribe(update, context)
    elif query.data == "unsubscribe":
        from handlers.idiom import unsubscribe
        await unsubscribe(update, context)
