"""
utils/constants.py — Static text, emoji constants, and menu layouts.
"""

# ─── Emojis ────────────────────────────────────────────────────────────────────
EMOJI_BOOK = "📚"
EMOJI_TRANSLATE = "🔤"
EMOJI_EXAMPLES = "💬"
EMOJI_SPEECH = "📝"
EMOJI_LINK = "🔗"
EMOJI_FLAG_GB = "🇬🇧"
EMOJI_FLAG_RU = "🇷🇺"
EMOJI_HISTORY = "📖"
EMOJI_SUCCESS = "✅"
EMOJI_WARNING = "⚠️"
EMOJI_ERROR = "❌"
EMOJI_LOCK = "🔒"
EMOJI_KEY = "🔑"
EMOJI_USERS = "👥"
EMOJI_ROBOT = "🤖"
EMOJI_WAVE = "👋"
EMOJI_ARROW = "→"
EMOJI_FLAG_KZ = "🇰🇿"
EMOJI_TARGET = "🎯"

# ─── Bot messages ──────────────────────────────────────────────────────────────

WELCOME_MESSAGE = (
    f"{EMOJI_WAVE} <b>Hello, {{name}}! Welcome to Aidos.</b>\n\n"
    "I'm your personal English → Russian vocabulary assistant.\n\n"
    f"<b>What I can do:</b>\n"
    f"• {EMOJI_TRANSLATE} Translate English words to Russian & Kazakh\n"
    f"• {EMOJI_BOOK} Generate advanced vocabulary by topic (/words)\n"
    f"• {EMOJI_TARGET} Send a daily idiom (if subscribed)\n"
    f"• {EMOJI_HISTORY} Keep your translation history\n\n"
    f"Type /translate to start a translation session.\n"
    f"Type /help to see all commands."
)

HELP_MESSAGE = (
    f"{EMOJI_ROBOT} <b>Aidos — Command Reference</b>\n\n"
    "<b>Translation</b>\n"
    "  /translate — Enter translate mode\n"
    "  /stop — Exit translate mode\n\n"
    "<b>Vocabulary & Idioms</b>\n"
    "  /words [topic] — Generate advanced words & expressions\n"
    "  /subscribe — Get a daily idiom\n"
    "  /unsubscribe — Stop daily idioms\n\n"
    "<b>History</b>\n"
    "  /history — View your last 20 translations\n"
    "  /history clear — Clear your history\n\n"
    "<b>General</b>\n"
    "  /start — Welcome message\n"
    "  /help — Show this message\n"
    "  /menu — Interactive menu\n\n"
    "<b>Admin only</b>\n"
    "  /allow &lt;user_id&gt; — Grant access to a user\n"
    "  /revoke &lt;user_id&gt; — Revoke a user's access\n"
    "  /users — List all allowed users"
)

TRANSLATE_MODE_START = (
    f"{EMOJI_TRANSLATE} <b>Translate mode activated!</b>\n\n"
    "Send me any English word and I'll translate it to Russian.\n"
    f"Type /stop when you're done."
)

TRANSLATE_MODE_END = (
    f"{EMOJI_SUCCESS} <b>Translate mode deactivated.</b>\n\n"
    "Your session is saved to /history. See you next time!"
)

TRANSLATE_MULTI_WORD_ERROR = (
    f"{EMOJI_WARNING} Please send <b>one word at a time</b>.\n\n"
    "I only translate single English words right now."
)

TRANSLATE_EMPTY_ERROR = f"{EMOJI_WARNING} Please send a word to translate."

ACCESS_DENIED = (
    f"{EMOJI_LOCK} <b>Access denied.</b>\n\n"
    "This bot is private. Contact the admin to request access."
)

ADMIN_ONLY = f"{EMOJI_LOCK} This command is for admins only."

ERROR_GENERIC = f"{EMOJI_ERROR} Something went wrong. Please try again in a moment."

HISTORY_EMPTY = (
    f"{EMOJI_HISTORY} You haven't translated any words yet.\n\n"
    "Use /translate to start a session!"
)

HISTORY_CLEARED = f"{EMOJI_SUCCESS} Your translation history has been cleared."

WORDS_GENERATING = f"{EMOJI_BOOK} <b>Generating vocabulary...</b>"
SUBSCRIBE_SUCCESS = f"{EMOJI_SUCCESS} You're subscribed to the daily idiom! You'll receive one every day at 14:00 UTC."
SUBSCRIBE_ALREADY = f"{EMOJI_TARGET} You are already subscribed to the daily idiom."
UNSUBSCRIBE_SUCCESS = f"{EMOJI_SUCCESS} You've been unsubscribed from the daily idiom."
UNSUBSCRIBE_NOT_FOUND = f"{EMOJI_WARNING} You weren't subscribed to the daily idiom."
