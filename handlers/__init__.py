"""
handlers/__init__.py — Central handler registration.

Call register_handlers(app) from main.py to wire everything up.
"""

from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from handlers.core import start, help_command, menu, menu_callback
from handlers.translation import build_translation_conversation
from handlers.history import history, history_words_command, history_idioms_command
from handlers.admin import allow_user, revoke_user, list_users
from handlers.error import error_handler
from handlers.vocabulary import words
from handlers.idiom import subscribe, unsubscribe, test_idiom, send_idiom
from handlers.journal import handle_audio_thought, notes_command, notes_callback, digest_command
from handlers.actions import actions_command, actions_callback


def register_handlers(app: Application) -> None:
    """Register all handlers with the application."""

    # ── Voice / Audio Journaling (captures voice & audio messages) ────────────
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_audio_thought))

    # ── Translation ConversationHandler (captures plain text in translate mode) ──
    app.add_handler(build_translation_conversation())

    # ── Core commands ──────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("menu", menu))
    # Note: The 'translate' callback is captured by the ConversationHandler above,
    # so it does not need to be included in this regex pattern.
    app.add_handler(
        CallbackQueryHandler(menu_callback, pattern="^(help|history|history_words|history_idioms|words|subscribe|unsubscribe|notes|actions|digest)$")
    )

    # ── Thought Journal & Notes ───────────────────────────────────────────────
    app.add_handler(CommandHandler("notes", notes_command))
    app.add_handler(CommandHandler("digest", digest_command))
    app.add_handler(
        CallbackQueryHandler(
            notes_callback,
            pattern=r"^(notes_export_csv|notes_sync_sheets|notes_list|note_del_\d+|note_cat_\d+|note_setcat_\d+_.+|note_view_\d+)$",
        )
    )

    # ── Action Items ──────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("actions", actions_command))
    app.add_handler(
        CallbackQueryHandler(
            actions_callback,
            pattern=r"^(act_toggle_\d+_\d+|act_view_all|act_view_pending|act_clear_done)$",
        )
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
    app.add_handler(CommandHandler("test_idiom", test_idiom))
    app.add_handler(CommandHandler("send_idiom", send_idiom))

    # ── Global error handler ──────────────────────────────────────────────────
    app.add_error_handler(error_handler)
