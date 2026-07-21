"""
handlers/translation.py — Translation mode via ConversationHandler.

Flow:
    /translate  →  TRANSLATING state  →  user sends words  →  /stop
"""

import logging
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from services.gemini_service import translate_word as gemini_translate
from database.models import add_translation
from utils.decorators import restricted, send_typing, rate_limit
from utils.formatting import format_translation
from utils.constants import (
    TRANSLATE_MODE_START,
    TRANSLATE_MODE_END,
    TRANSLATE_MULTI_WORD_ERROR,
    TRANSLATE_EMPTY_ERROR,
    ERROR_GENERIC,
)

logger = logging.getLogger(__name__)

# ConversationHandler state
TRANSLATING = 0


@restricted
async def start_translate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point: /translate — activate translate mode."""
    user = update.effective_user
    if update.callback_query:
        await update.callback_query.answer()
    logger.info("User %s entered translate mode.", user.id)
    await update.effective_message.reply_text(TRANSLATE_MODE_START, parse_mode="HTML")
    return TRANSLATING


@send_typing
@rate_limit(3.0, default_return=TRANSLATING)
async def handle_word(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Process a word sent by the user while in TRANSLATING state.
    Translates it and saves to history. Stays in TRANSLATING state.
    """
    user = update.effective_user
    text = (update.message.text or "").strip()

    # Guard: empty input
    if not text:
        await update.effective_message.reply_text(
            TRANSLATE_EMPTY_ERROR, parse_mode="HTML"
        )
        return TRANSLATING

    # Guard: multiple words
    if len(text.split()) > 1:
        await update.effective_message.reply_text(
            TRANSLATE_MULTI_WORD_ERROR, parse_mode="HTML"
        )
        return TRANSLATING

    word = text.lower()
    logger.info("User %s translating: '%s'", user.id, word)

    try:
        translation_data = await gemini_translate(word)
    except Exception as e:
        logger.error("Gemini API error for word '%s': %s", word, e)
        await update.effective_message.reply_text(ERROR_GENERIC, parse_mode="HTML")
        return TRANSLATING  # Stay in mode — let user try again

    # Format and send translation
    message = format_translation(word, translation_data)
    await update.effective_message.reply_text(message, parse_mode="HTML")

    # Extract Kazakh translation for DB storage
    kazakh = translation_data.get("kazakh")

    # Persist to history (best-effort — don't crash if DB fails)
    import json
    try:
        await add_translation(
            user_id=user.id,
            word=word,
            translation=json.dumps(translation_data, ensure_ascii=False),
            kazakh_translation=kazakh,
        )
    except Exception as e:
        logger.error("Failed to save translation to history: %s", e)

    return TRANSLATING


async def end_translate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Exit point: /stop or /cancel — deactivate translate mode."""
    user = update.effective_user
    logger.info("User %s exited translate mode.", user.id)
    await update.effective_message.reply_text(TRANSLATE_MODE_END, parse_mode="HTML")
    return ConversationHandler.END


def build_translation_conversation() -> ConversationHandler:
    """Build and return the ConversationHandler for translate mode."""
    return ConversationHandler(
        entry_points=[
            CommandHandler("translate", start_translate),
            CallbackQueryHandler(start_translate, pattern="^translate$"),
        ],
        states={
            TRANSLATING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_word),
            ],
        },
        fallbacks=[
            CommandHandler("stop", end_translate),
            CommandHandler("cancel", end_translate),
        ],
        # Allow the conversation to run per-user (default behaviour)
        name="translate_conversation",
        persistent=False,
    )
