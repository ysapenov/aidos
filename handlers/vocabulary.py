"""
handlers/vocabulary.py — Vocabulary command handler.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from utils.decorators import restricted, send_typing
from utils.constants import ERROR_GENERIC, WORDS_GENERATING
from database.models import get_vocabulary_words, save_vocabulary_entry
from services.vocabulary_service import generate_vocabulary, format_vocabulary_response

logger = logging.getLogger(__name__)


@restricted
@send_typing
async def words(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /words command — generate advanced vocabulary."""
    user = update.effective_user

    # Check if called from inline keyboard or with args
    if update.callback_query:
        await update.callback_query.answer()
        topic = None
    else:
        topic = " ".join(context.args) if context.args else None

    # Send processing message
    processing_msg = await update.effective_message.reply_text(
        WORDS_GENERATING, parse_mode="HTML"
    )

    try:
        # Fetch history for exclusion
        exclude_words = await get_vocabulary_words(user.id)

        # Generate vocabulary
        vocab_data = generate_vocabulary(topic, exclude_words)

        # Save to history
        for w in vocab_data.get("words", []):
            await save_vocabulary_entry(
                user_id=user.id,
                entry_type="word",
                english_text=w.get("english", ""),
                russian_text=w.get("russian"),
                kazakh_text=w.get("kazakh"),
                topic=vocab_data.get("topic"),
            )

        for pv in vocab_data.get("phrasal_verbs", []):
            await save_vocabulary_entry(
                user_id=user.id,
                entry_type="phrasal_verb",
                english_text=pv.get("english", ""),
                russian_text=pv.get("russian"),
                kazakh_text=pv.get("kazakh"),
                topic=vocab_data.get("topic"),
            )

        for ex in vocab_data.get("expressions", []):
            await save_vocabulary_entry(
                user_id=user.id,
                entry_type="expression",
                english_text=ex.get("english", ""),
                russian_text=ex.get("russian"),
                kazakh_text=ex.get("kazakh"),
                topic=vocab_data.get("topic"),
            )

        # Format and send response
        response_text = format_vocabulary_response(vocab_data)
        await processing_msg.edit_text(response_text, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Error generating vocabulary for user {user.id}: {e}")
        await processing_msg.edit_text(ERROR_GENERIC, parse_mode="HTML")
