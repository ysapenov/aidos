"""
utils/constants.py — Static text, emoji constants, and menu layouts.
"""

# ─── Emojis ────────────────────────────────────────────────────────────────────
EMOJI_BOOK = "📚"
EMOJI_TRANSLATE = "🔤"
EMOJI_EXAMPLES = "💬"
EMOJI_LINK = "🔗"
EMOJI_FLAG_RU = "🇷🇺"
EMOJI_HISTORY = "📖"
EMOJI_SUCCESS = "✅"
EMOJI_WARNING = "⚠️"
EMOJI_ERROR = "❌"
EMOJI_LOCK = "🔒"

EMOJI_ROBOT = "🤖"
EMOJI_WAVE = "👋"
EMOJI_ARROW = "→"
EMOJI_FLAG_KZ = "🇰🇿"
EMOJI_TARGET = "🎯"
EMOJI_MIC = "🎙"
EMOJI_NOTE = "📝"
EMOJI_IDEA = "💡"
EMOJI_TAG = "🏷"
EMOJI_CHECK = "✅"
EMOJI_UNCHECK = "⬜"
EMOJI_CALENDAR = "📅"
EMOJI_CHART = "📊"
EMOJI_ENERGY = "⚡"
EMOJI_MOOD = "🎭"

# ─── Bot messages ──────────────────────────────────────────────────────────────

WELCOME_MESSAGE = (
    f"{EMOJI_WAVE} <b>Hello, {{name}}! Welcome to Aidos.</b>\n\n"
    "I'm your personal AI assistant for language learning and audio thought journaling.\n\n"
    f"<b>What I can do:</b>\n"
    f"• {EMOJI_MIC} <b>Voice Journal:</b> Send any voice thought (< 1 min) anytime — I'll clean, categorize, track mood & extract tasks!\n"
    f"• {EMOJI_NOTE} /notes — Browse thoughts, filter categories, or export as CSV\n"
    f"• {EMOJI_CHECK} /actions — View and manage action items extracted from your thoughts\n"
    f"• {EMOJI_CHART} /digest — Get an AI-powered weekly/monthly reflection and momentum digest\n"
    f"• {EMOJI_TRANSLATE} Translate English words to Russian & Kazakh (/translate)\n"
    f"• {EMOJI_BOOK} Generate advanced vocabulary by topic (/words)\n"
    f"• {EMOJI_TARGET} Send a daily idiom (if subscribed)\n\n"
    f"Type /help to see all commands."
)

HELP_MESSAGE = (
    f"{EMOJI_ROBOT} <b>Aidos — Command Reference</b>\n\n"
    "<b>Thought Journal</b>\n"
    "  🎙 <i>Send voice or audio</i> — Auto-clean, structure, track mood & tasks (< 1 min)\n"
    "  /notes — View recent thoughts with interactive actions\n"
    "  /notes &lt;id&gt; — View full details of a specific note\n"
    "  /notes export — Download all notes as a CSV file\n"
    "  /notes sync — Sync all notes to Google Sheets\n"
    "  /actions — View and check off pending action items\n"
    "  /actions all — View all action items (including completed)\n"
    "  /digest — Weekly reflection digest of your thoughts\n"
    "  /digest monthly — Monthly reflection digest\n\n"
    "<b>Translation</b>\n"
    "  /translate — Enter translate mode\n"
    "  /stop — Exit translate mode\n\n"
    "<b>Vocabulary & Idioms</b>\n"
    "  /words [topic] — Generate advanced words & expressions\n"
    "  /subscribe — Get a daily idiom\n"
    "  /unsubscribe — Stop daily idioms\n\n"
    "<b>History</b>\n"
    "  /history — View your last 20 translations\n"
    "  /history_words — View generated vocabulary history\n"
    "  /history_idioms — View daily idioms history\n"
    "  /history clear — Clear your history\n\n"
    "<b>General</b>\n"
    "  /start — Welcome message\n"
    "  /help — Show this message\n"
    "  /menu — Interactive menu\n\n"
    "<b>Admin only</b>\n"
    "  /allow &lt;user_id&gt; — Grant access to a user\n"
    "  /revoke &lt;user_id&gt; — Revoke a user's access\n"
    "  /users — List all allowed users\n"
    "  /test_idiom — Preview idiom generation (admin only)\n"
    "  /send_idiom — Broadcast daily idiom immediately"
)


TRANSLATE_MODE_START = (
    f"{EMOJI_TRANSLATE} <b>Translate mode activated!</b>\n\n"
    "Send me any English word and I'll translate it to Russian and Kazakh.\n"
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

AUDIO_TOO_LONG_ERROR = (
    f"{EMOJI_WARNING} <b>Audio is too long.</b>\n\n"
    "Please send short thoughts under <b>1 minute</b> (received: {duration}s)."
)
AUDIO_PROCESSING = f"{EMOJI_MIC} <i>Listening and organizing your thoughts...</i>"
AUDIO_TRANSCRIBE_ERROR = (
    f"{EMOJI_ERROR} <b>Could not process audio.</b>\n\n"
    "No clear speech was recognized or an error occurred. Please try recording with clearer sound."
)
NOTES_EMPTY = (
    f"{EMOJI_NOTE} <b>No notes found.</b>\n\n"
    "Send any voice or audio message (< 1 min) anytime to start recording your thoughts!"
)

ACTIONS_EMPTY = (
    f"{EMOJI_CHECK} <b>No pending action items!</b>\n\n"
    "When you mention tasks or next steps in your voice thoughts, they will appear here automatically."
)

DIGEST_GENERATING = f"{EMOJI_CHART} <b>Analyzing your thoughts and synthesizing digest...</b>"
DIGEST_EMPTY = (
    f"{EMOJI_CHART} <b>No thoughts found for this period.</b>\n\n"
    "Record some voice notes first to generate a weekly or monthly digest!"
)

SHEETS_NOT_CONFIGURED = (
    f"{EMOJI_WARNING} <b>Google Sheets is not configured yet.</b>\n\n"
    "To enable cloud sync:\n"
    "1. Set <code>GOOGLE_SHEET_ID</code> in your <code>.env</code> file.\n"
    "2. Place your service account JSON file at <code>GOOGLE_SHEETS_CREDENTIALS_FILE</code>.\n"
    "3. Share your Google Sheet with the service account email as Editor."
)


