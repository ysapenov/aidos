"""
utils/formatting.py — Telegram message formatting helpers.
"""

import html
from datetime import datetime
from utils.constants import (
    EMOJI_BOOK,
    EMOJI_HISTORY,
    EMOJI_ARROW,
)


def escape_html(text: str) -> str:
    """Escape special HTML characters for use in Telegram HTML parse mode."""
    return html.escape(text)


def format_translation(word: str, translation_text: str) -> str:
    """
    Wrap the Gemini translation response with a header for Telegram display.

    The translation_text is already formatted by Gemini using our prompt.
    We add a styled header on top.
    """
    safe_word = escape_html(word.lower())
    return f"{EMOJI_BOOK} <b>{safe_word}</b>\n" f"{'─' * 30}\n" f"{translation_text}"


def format_history(entries: list[dict], total: int) -> str:
    """
    Format the translation history list for Telegram display.

    entries: list of dicts with keys: word, translation, created_at
    total:   total number of translations saved
    """
    if not entries:
        return ""

    lines = [f"{EMOJI_HISTORY} <b>Your Translation History</b>\n"]

    for i, entry in enumerate(entries, start=1):
        word = escape_html(entry["word"])

        # Extract just the first Russian translation line from the full response
        # (the full Gemini response is stored; we show a short summary in history)
        first_line = _extract_first_translation(entry["translation"])
        date_str = _format_date(entry["created_at"])

        kazakh = ""
        if entry.get("kazakh_translation"):
            kazakh = f" = {escape_html(entry['kazakh_translation'])}"

        lines.append(
            f"{i}. <b>{word}</b> {EMOJI_ARROW} {first_line}{kazakh} <i>({date_str})</i>"
        )

    lines.append(f"\n<i>Total: {total} word(s) translated</i>")
    return "\n".join(lines)


def format_users_list(users: list[dict], static_ids: set[int]) -> str:
    """Format the list of allowed users for the /users admin command."""
    lines = ["👥 <b>Allowed Users</b>\n"]

    # Static users from .env
    if static_ids:
        lines.append("<i>From .env (ALLOWED_USER_IDS):</i>")
        for uid in sorted(static_ids):
            lines.append(f"  • <code>{uid}</code>")
        lines.append("")

    # DB users
    if users:
        lines.append("<i>Added via /allow:</i>")
        for i, u in enumerate(users, start=1):
            username = f"@{u['username']}" if u.get("username") else "no username"
            name = escape_html(u.get("first_name") or "")
            lines.append(f"  {i}. <code>{u['telegram_id']}</code> — {username} {name}")
    elif not static_ids:
        lines.append("<i>No users found.</i>")

    return "\n".join(lines)


# ─── Private helpers ──────────────────────────────────────────────────────────


def _extract_first_translation(full_response: str) -> str:
    """
    Pull the first meaningful translation word/phrase from the Gemini response.
    Falls back to "…" if parsing fails.
    """
    for line in full_response.splitlines():
        line = line.strip()
        if line.startswith(("•", "-", "*")):
            # A typical line: "• устойчивость — stability, resistance"
            line = line.lstrip("*•-#").strip()
            # Extract just the Russian word before the definition
            primary_word = line.split(" (")[0].split(" — ")[0].split(" - ")[0].strip()
            if primary_word:
                return escape_html(primary_word)

    # Fallback: return the first non-header line that looks short enough
    for line in full_response.splitlines():
        line = line.strip()
        if line and not line.startswith("🔤") and len(line) < 60:
            return escape_html(line.lstrip("*•-#").strip())

    return "…"


def _format_date(created_at: str) -> str:
    """Format a SQLite timestamp string to a human-readable short date."""
    try:
        dt = datetime.fromisoformat(created_at)
        return dt.strftime("%b %-d")  # e.g. "Jul 3"
    except Exception:
        return created_at[:10]  # fallback to YYYY-MM-DD
