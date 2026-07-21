"""
main.py — Entry point for the Aidos Telegram Bot.

Initialises the database, registers handlers, and starts polling.
"""

import logging
from datetime import time, timezone
from telegram.ext import Application
from config import settings
from database.db import init_db
from handlers import register_handlers
from handlers.idiom import send_daily_idiom

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=getattr(logging, settings.log_level, logging.INFO),
)
logger = logging.getLogger(__name__)


async def on_startup(app: Application) -> None:
    """Run tasks on bot startup."""
    logger.info("Initialising database...")
    await init_db()
    logger.info("Database initialised.")

    from telegram import BotCommand
    commands = [
        BotCommand("start", "Welcome message"),
        BotCommand("help", "Show all commands"),
        BotCommand("menu", "Interactive menu"),
        BotCommand("translate", "Enter translate mode"),
        BotCommand("stop", "Exit translate mode"),
        BotCommand("words", "Generate advanced words"),
        BotCommand("subscribe", "Get a daily idiom"),
        BotCommand("unsubscribe", "Stop daily idioms"),
        BotCommand("history", "View last 20 translations"),
        BotCommand("history_words", "View vocabulary history"),
        BotCommand("history_idioms", "View idiom history"),
        BotCommand("history_clear", "Clear history")
    ]
    await app.bot.set_my_commands(commands)
    logger.info("Bot commands updated.")

    # Schedule daily idiom at 14:00 UTC
    app.job_queue.run_daily(
        send_daily_idiom,
        time=time(hour=14, minute=0, tzinfo=timezone.utc),
        name="daily_idiom",
    )
    logger.info("Daily idiom scheduled for 14:00 UTC.")


def main() -> None:
    """Start the bot."""
    # Validate configuration (raises ValueError if required env vars are missing)
    settings.validate()

    logger.info("Starting Aidos Bot...")

    # Build the application
    app = Application.builder().token(settings.telegram_token).build()

    # Register post-init startup tasks
    app.post_init = on_startup

    # Register all handlers
    register_handlers(app)

    # Start polling
    logger.info("Bot is polling for updates...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
