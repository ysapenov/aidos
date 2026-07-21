"""
handlers/__init__.py — Central handler registration.

Call register_handlers(app) from main.py to wire everything up.
"""

from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from handlers.core import start, help_command, menu, menu_callback
from handlers.translation import build_translation_conversation
from handlers.history import history, history_words_command, history_idioms_command
from handlers.admin import allow_user, revoke_user, list_users
from handlers.error import error_handler
from handlers.vocabulary import words
from handlers.idiom import subscribe, unsubscribe


def register_handlers(app: Application) -> None:
    """Register all handlers with the application."""

    # ── Translation ConversationHandler (must be first — captures plain text) ──
    app.add_handler(build_translation_conversation())

    # ── Core commands ──────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("menu", menu))
    # Note: The 'translate' callback is captured by the ConversationHandler above,
    # so it does not need to be included in this regex pattern.
    app.add_handler(
        CallbackQueryHandler(menu_callback, pattern="^(help|history|history_words|history_idioms|words|subscribe|unsubscribe)$")
    )

    # ── History & Vocabulary & Idioms ─────────────────────────────────────────
    app.add_handler(CommandHandler("history", history))
    app.add_handler(CommandHandler("history_words", history_words_command))
    app.add_handler(CommandHandler("history_idioms", history_idioms_command))
    app.add_handler(CommandHandler("words", words))
    app.add_handler(CommandHandler("subscribe", subscribe))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe))

    # ── Admin commands ────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("allow", allow_user))
    app.add_handler(CommandHandler("revoke", revoke_user))
    app.add_handler(CommandHandler("users", list_users))

    # ── Global error handler ──────────────────────────────────────────────────
    app.add_error_handler(error_handler)
