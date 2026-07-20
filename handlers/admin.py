"""
handlers/admin.py — Admin commands for user management.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from database.models import (
    add_allowed_user,
    remove_allowed_user,
    list_allowed_users,
)
from utils.decorators import admin_only
from utils.formatting import format_users_list
from config import settings
from utils.constants import EMOJI_SUCCESS, EMOJI_WARNING, EMOJI_ERROR

logger = logging.getLogger(__name__)


@admin_only
async def allow_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /allow <user_id> — grant access to a user."""
    if not context.args:
        await update.message.reply_text(
            f"{EMOJI_WARNING} Please provide a User ID. Example: <code>/allow 123456789</code>",
            parse_mode="HTML",
        )
        return

    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            f"{EMOJI_ERROR} Invalid User ID. Must be a number.",
            parse_mode="HTML",
        )
        return

    # Add to DB (we don't have their username yet, it will update on their first /start)
    await add_allowed_user(user_id, username=None, first_name=None)

    await update.message.reply_text(
        f"{EMOJI_SUCCESS} User <code>{user_id}</code> has been granted access.",
        parse_mode="HTML",
    )


@admin_only
async def revoke_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /revoke <user_id> — revoke access from a user."""
    if not context.args:
        await update.message.reply_text(
            f"{EMOJI_WARNING} Please provide a User ID. Example: <code>/revoke 123456789</code>",
            parse_mode="HTML",
        )
        return

    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            f"{EMOJI_ERROR} Invalid User ID. Must be a number.",
            parse_mode="HTML",
        )
        return

    if user_id in settings.allowed_user_ids:
        await update.message.reply_text(
            f"{EMOJI_WARNING} Cannot revoke user <code>{user_id}</code> because they are listed in the ALLOWED_USER_IDS environment variable. Remove them from .env first.",
            parse_mode="HTML",
        )
        return

    removed = await remove_allowed_user(user_id)
    if removed:
        await update.message.reply_text(
            f"{EMOJI_SUCCESS} Access revoked for user <code>{user_id}</code>.",
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text(
            f"{EMOJI_WARNING} User <code>{user_id}</code> is not in the allowed list.",
            parse_mode="HTML",
        )


@admin_only
async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /users — list all allowed users."""
    db_users = await list_allowed_users()
    static_users = settings.allowed_user_ids

    message = format_users_list(db_users, static_users)
    await update.message.reply_text(message, parse_mode="HTML")
