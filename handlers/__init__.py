"""
handlers/__init__.py — Central handler registration.

Call register_handlers(app) from main.py to wire everything up.
"""

from telegram.ext import Application, CommandHandler, MessageHandler, filters
from handlers.core import start, help_command, menu
from handlers.translation import build_translation_conversation
from handlers.history import history
from handlers.admin import allow_user, revoke_user, list_users
from handlers.error import error_handler


def register_handlers(app: Application) -> None:
    """Register all handlers with the application."""

    # ── Translation ConversationHandler (must be first — captures plain text) ──
    app.add_handler(build_translation_conversation())

    # ── Core commands ──────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("menu", menu))

    # ── History ───────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("history", history))

    # ── Admin commands ────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("allow", allow_user))
    app.add_handler(CommandHandler("revoke", revoke_user))
    app.add_handler(CommandHandler("users", list_users))

    # ── Global error handler ──────────────────────────────────────────────────
    app.add_error_handler(error_handler)
