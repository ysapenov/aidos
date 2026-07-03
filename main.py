"""
main.py — Entry point for the Aidos Telegram Bot.

Initialises the database, registers handlers, and starts polling.
"""

import logging
from telegram.ext import Application
from config import settings
from database.db import init_db
from handlers import register_handlers

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
