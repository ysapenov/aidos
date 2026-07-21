"""
utils/decorators.py — Reusable handler decorators.

@restricted      — blocks non-whitelisted users
@admin_only      — blocks non-admin users
@send_typing     — shows "typing..." while the handler runs
"""

import logging
import functools
import time
from typing import Callable, Any
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from database.models import is_user_allowed
from config import settings
from utils.constants import ACCESS_DENIED, ADMIN_ONLY

logger = logging.getLogger(__name__)

# Maximum number of user entries to keep in the rate-limit tracker
_RATE_LIMIT_MAX_USERS = 1000


def restricted(func: Callable) -> Callable:
    """
    Decorator that restricts access to the bot.
    Only users in the static ALLOWED_USER_IDS or the database whitelist can use the command.
    """

    @functools.wraps(func)
    async def wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args: Any, **kwargs: Any
    ) -> Any:
        user = update.effective_user
        if not user:
            return

        is_allowed = await is_user_allowed(user.id)

        if not is_allowed:
            logger.warning(
                "Unauthorized access attempt by %s (@%s)", user.id, user.username
            )
            await update.effective_message.reply_text(ACCESS_DENIED, parse_mode="HTML")
            return  # Return None — stops ConversationHandler entry too

        return await func(update, context, *args, **kwargs)

    return wrapper


def admin_only(func: Callable) -> Callable:
    """
    Decorator that restricts access to admin users only.
    Admins are defined statically in the ADMIN_USER_IDS config.
    """

    @functools.wraps(func)
    async def wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args: Any, **kwargs: Any
    ) -> Any:
        user = update.effective_user
        if not user or user.id not in settings.admin_user_ids:
            logger.warning(
                "Unauthorized admin access attempt by %s (@%s)",
                user.id if user else "Unknown",
                user.username if user else "Unknown",
            )
            await update.effective_message.reply_text(ADMIN_ONLY, parse_mode="HTML")
            return

        return await func(update, context, *args, **kwargs)

    return wrapper


def send_typing(func: Callable) -> Callable:
    """
    Decorator that sends a "typing..." chat action before the handler runs.
    Makes the bot feel responsive during API calls.
    """

    @functools.wraps(func)
    async def wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args: Any, **kwargs: Any
    ) -> Any:
        if update.effective_chat:
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id,
                action=ChatAction.TYPING,
            )
        return await func(update, context, *args, **kwargs)

    return wrapper


_user_last_request: dict[int, float] = {}


def rate_limit(limit_seconds: float = 3.0, default_return: Any = None) -> Callable:
    """
    Decorator that limits how often a user can trigger a handler.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(
            update: Update, context: ContextTypes.DEFAULT_TYPE, *args: Any, **kwargs: Any
        ) -> Any:
            user = update.effective_user
            if not user:
                return await func(update, context, *args, **kwargs)

            now = time.time()
            last_req = _user_last_request.get(user.id, 0.0)

            if now - last_req < limit_seconds:
                logger.warning("User %s rate limited.", user.id)
                if update.effective_message:
                    await update.effective_message.reply_text(
                        "⚠️ Please wait a few seconds before requesting again."
                    )
                return default_return

            _user_last_request[user.id] = now

            # Periodically prune stale entries to prevent unbounded growth
            if len(_user_last_request) > _RATE_LIMIT_MAX_USERS:
                cutoff = now - limit_seconds
                stale = [
                    uid for uid, ts in _user_last_request.items() if ts < cutoff
                ]
                for uid in stale:
                    del _user_last_request[uid]

            return await func(update, context, *args, **kwargs)

        return wrapper
    return decorator
