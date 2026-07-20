"""
utils/decorators.py — Reusable handler decorators.

@restricted      — blocks non-whitelisted users
@admin_only      — blocks non-admin users
@send_typing     — shows "typing..." while the handler runs
"""

import logging
import functools
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from database.models import is_user_allowed
from config import settings
from utils.constants import ACCESS_DENIED, ADMIN_ONLY

logger = logging.getLogger(__name__)


def restricted(func):
    """
    Decorator that blocks users not on the whitelist.
    Works for both CommandHandlers and ConversationHandler entry points.
    """

    @functools.wraps(func)
    async def wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ):
        user = update.effective_user
        if not user:
            return

        allowed = await is_user_allowed(user.id)
        if not allowed:
            logger.warning(
                f"Unauthorised access attempt by user {user.id} (@{user.username})"
            )
            await update.effective_message.reply_text(ACCESS_DENIED, parse_mode="HTML")
            return  # Return None — stops ConversationHandler entry too

        return await func(update, context, *args, **kwargs)

    return wrapper


def admin_only(func):
    """
    Decorator that blocks users not in ADMIN_USER_IDS.
    """

    @functools.wraps(func)
    async def wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ):
        user = update.effective_user
        if not user or user.id not in settings.admin_user_ids:
            await update.effective_message.reply_text(ADMIN_ONLY, parse_mode="HTML")
            return

        return await func(update, context, *args, **kwargs)

    return wrapper


def send_typing(func):
    """
    Decorator that sends a "typing..." chat action before the handler runs.
    Makes the bot feel responsive during API calls.
    """

    @functools.wraps(func)
    async def wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ):
        if update.effective_chat:
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id,
                action=ChatAction.TYPING,
            )
        return await func(update, context, *args, **kwargs)

    return wrapper


import time

_user_last_request: dict[int, float] = {}

def rate_limit(limit_seconds: float = 3.0, default_return=None):
    """
    Decorator that limits how often a user can trigger a handler.
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(
            update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
        ):
            user = update.effective_user
            if not user:
                return await func(update, context, *args, **kwargs)
                
            now = time.time()
            last_req = _user_last_request.get(user.id, 0.0)
            
            if now - last_req < limit_seconds:
                logger.warning(f"User {user.id} rate limited.")
                if update.effective_message:
                    await update.effective_message.reply_text(
                        "⚠️ Please wait a few seconds before requesting again."
                    )
                return default_return
                
            _user_last_request[user.id] = now
            return await func(update, context, *args, **kwargs)
            
        return wrapper
    return decorator
