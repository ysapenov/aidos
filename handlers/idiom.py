"""
handlers/idiom.py — Daily idiom scheduler and subscription commands.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from utils.decorators import restricted
from utils.constants import (
    SUBSCRIBE_SUCCESS,
    SUBSCRIBE_ALREADY,
    UNSUBSCRIBE_SUCCESS,
    UNSUBSCRIBE_NOT_FOUND,
)
from database.models import (
    subscribe_user,
    unsubscribe_user,
    is_subscribed,
    get_sent_idioms,
    save_idiom,
    get_subscribed_user_ids,
)
from services.idiom_service import generate_idiom, format_idiom_response

logger = logging.getLogger(__name__)


@restricted
async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /subscribe command."""
    user = update.effective_user

    # Check if called from inline keyboard
    if update.callback_query:
        await update.callback_query.answer()

    if await is_subscribed(user.id):
        await update.effective_message.reply_text(SUBSCRIBE_ALREADY, parse_mode="HTML")
    else:
        await subscribe_user(user.id)
        await update.effective_message.reply_text(SUBSCRIBE_SUCCESS, parse_mode="HTML")
        logger.info(f"User {user.id} subscribed to daily idioms.")


@restricted
async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /unsubscribe command."""
    user = update.effective_user

    was_subscribed = await unsubscribe_user(user.id)
    if was_subscribed:
        await update.effective_message.reply_text(
            UNSUBSCRIBE_SUCCESS, parse_mode="HTML"
        )
        logger.info(f"User {user.id} unsubscribed from daily idioms.")
    else:
        await update.effective_message.reply_text(
            UNSUBSCRIBE_NOT_FOUND, parse_mode="HTML"
        )


async def send_daily_idiom(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Scheduled job to generate and send a daily idiom to all subscribed users.
    Called by the JobQueue.
    """
    logger.info("Starting daily idiom generation and broadcast...")

    try:
        # Fetch history for exclusion
        exclude_idioms = await get_sent_idioms()

        # Generate idiom
        idiom_data = await generate_idiom(exclude_idioms)

        # Save to history
        await save_idiom(
            idiom=idiom_data.get("idiom", ""),
            russian_equivalent=idiom_data.get("russian_equivalent"),
            kazakh_equivalent=idiom_data.get("kazakh_equivalent"),
        )

        # Format response
        response_text = format_idiom_response(idiom_data)

        # Fetch subscribers and broadcast
        subscribers = await get_subscribed_user_ids()
        success_count = 0

        for user_id in subscribers:
            try:
                await context.bot.send_message(
                    chat_id=user_id, text=response_text, parse_mode="HTML"
                )
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to send idiom to user {user_id}: {e}")

        logger.info(
            f"Daily idiom broadcast complete. Sent to {success_count}/{len(subscribers)} users."
        )

    except Exception as e:
        logger.error(f"Error during daily idiom generation/broadcast: {e}")
