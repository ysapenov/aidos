"""
handlers/idiom.py — Daily idiom scheduler and subscription commands.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from config import settings
from utils.decorators import restricted, admin_only
from utils.formatting import escape_html
from utils.constants import (
    SUBSCRIBE_SUCCESS,
    SUBSCRIBE_ALREADY,
    UNSUBSCRIBE_SUCCESS,
    UNSUBSCRIBE_NOT_FOUND,
    EMOJI_SUCCESS,
    EMOJI_ERROR,
    EMOJI_WARNING,
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
        logger.info("User %s subscribed to daily idioms.", user.id)


@restricted
async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /unsubscribe command."""
    user = update.effective_user

    was_subscribed = await unsubscribe_user(user.id)
    if was_subscribed:
        await update.effective_message.reply_text(
            UNSUBSCRIBE_SUCCESS, parse_mode="HTML"
        )
        logger.info("User %s unsubscribed from daily idioms.", user.id)
    else:
        await update.effective_message.reply_text(
            UNSUBSCRIBE_NOT_FOUND, parse_mode="HTML"
        )


async def broadcast_daily_idiom(bot) -> tuple[int, int, str]:
    """
    Generate an idiom, save it to history, and broadcast to all subscribers.
    Returns (success_count, total_subscribers, response_text).
    """
    exclude_idioms = await get_sent_idioms()
    idiom_data = await generate_idiom(exclude_idioms)

    await save_idiom(
        idiom=idiom_data.get("idiom", ""),
        russian_equivalent=idiom_data.get("russian_equivalent"),
        kazakh_equivalent=idiom_data.get("kazakh_equivalent"),
    )

    response_text = format_idiom_response(idiom_data)
    subscribers = await get_subscribed_user_ids()
    success_count = 0

    for user_id in subscribers:
        try:
            await bot.send_message(
                chat_id=user_id, text=response_text, parse_mode="HTML"
            )
            success_count += 1
        except Exception as e:
            logger.error("Failed to send idiom to user %s: %s", user_id, e)

    return success_count, len(subscribers), response_text


async def send_daily_idiom(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Scheduled job to generate and send a daily idiom to all subscribed users.
    Called by the JobQueue.
    """
    logger.info("Starting scheduled daily idiom broadcast...")

    try:
        success_count, total_subs, _ = await broadcast_daily_idiom(context.bot)
        logger.info(
            f"Daily idiom broadcast complete. Sent to {success_count}/{total_subs} users."
        )
    except Exception as e:
        logger.error("Error during scheduled daily idiom broadcast: %s", e)
        # Notify admins of failure
        alert_text = (
            f"{EMOJI_ERROR} <b>[Aidos Alert]</b> Scheduled daily idiom broadcast failed:\n"
            f"<code>{escape_html(str(e))}</code>"
        )
        for admin_id in settings.admin_user_ids:
            try:
                await context.bot.send_message(
                    chat_id=admin_id, text=alert_text, parse_mode="HTML"
                )
            except Exception as admin_err:
                logger.error("Failed to notify admin %s of idiom error: %s", admin_id, admin_err)


@admin_only
async def test_idiom(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /test_idiom — generate an idiom preview for the admin only."""
    status_msg = await update.effective_message.reply_text(
        "🎯 Generating test idiom preview...", parse_mode="HTML"
    )

    try:
        exclude_idioms = await get_sent_idioms()
        idiom_data = await generate_idiom(exclude_idioms)
        response_text = format_idiom_response(idiom_data)
        preview_text = f"🧪 <b>[Admin Preview — Not Broadcasted]</b>\n\n{response_text}"
        await status_msg.edit_text(preview_text, parse_mode="HTML")
    except Exception as e:
        logger.error("Error generating test idiom: %s", e)
        await status_msg.edit_text(
            f"{EMOJI_ERROR} Failed to generate test idiom:\n<code>{escape_html(str(e))}</code>",
            parse_mode="HTML",
        )

# Prevent pytest from treating handler as a test case
test_idiom.__test__ = False


@admin_only
async def send_idiom(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /send_idiom — manually trigger a daily idiom broadcast to all subscribers."""
    subscribers = await get_subscribed_user_ids()
    if not subscribers:
        await update.effective_message.reply_text(
            f"{EMOJI_WARNING} No users are currently subscribed to daily idioms.",
            parse_mode="HTML",
        )
        return

    status_msg = await update.effective_message.reply_text(
        f"🎯 Generating idiom and broadcasting to {len(subscribers)} subscriber(s)...",
        parse_mode="HTML",
    )

    try:
        success_count, total_subs, _ = await broadcast_daily_idiom(context.bot)
        await status_msg.edit_text(
            f"{EMOJI_SUCCESS} Daily idiom broadcast complete!\n"
            f"Sent to <b>{success_count}/{total_subs}</b> subscriber(s).",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error("Error during manual idiom broadcast: %s", e)
        await status_msg.edit_text(
            f"{EMOJI_ERROR} Manual idiom broadcast failed:\n<code>{escape_html(str(e))}</code>",
            parse_mode="HTML",
        )
