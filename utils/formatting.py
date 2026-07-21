"""
utils/formatting.py — Telegram message formatting helpers.
"""

import html
from datetime import datetime
from utils.constants import (
    EMOJI_BOOK,
    EMOJI_HISTORY,
    EMOJI_ARROW,
    EMOJI_WARNING,
    EMOJI_FLAG_KZ,
)


def escape_html(text: str) -> str:
    """Escape special HTML characters for use in Telegram HTML parse mode."""
    return html.escape(text)


def format_translation(word: str, data: dict) -> str:
    """
    Format the JSON translation dictionary for Telegram display.
    """
    safe_word = escape_html(word.lower())
    
    if "error" in data:
        return f"{EMOJI_WARNING} <b>{safe_word}</b>: {escape_html(data['error'])}"

    lines = [f"{EMOJI_BOOK} <b>{safe_word}</b>", f"{'─' * 30}"]
    
    if data.get("pronunciation"):
        lines.append(f"🗣️ Pronunciation: {escape_html(data['pronunciation'])}")
        
    lines.append("\n🔤 Translations:")
    for t in data.get("translations", []):
        lines.append(f"• {escape_html(t.get('russian', ''))} — {escape_html(t.get('meaning', ''))}")
        
    if data.get("kazakh"):
        lines.append(f"\n{EMOJI_FLAG_KZ} Kazakh: {escape_html(data['kazakh'])}")
        
    if data.get("part_of_speech"):
        lines.append(f"📝 Part of speech: {escape_html(data['part_of_speech'])}")
        
    if data.get("examples"):
        lines.append("\n💬 Examples:")
        for i, ex in enumerate(data["examples"], start=1):
            lines.append(f"{i}. 🇬🇧 {escape_html(ex.get('english', ''))}\n   🇷🇺 {escape_html(ex.get('russian', ''))}")
            
    if data.get("collocations"):
        lines.append("\n🔗 Collocations:")
        for c in data["collocations"]:
            lines.append(f"• {escape_html(c.get('english', ''))} — {escape_html(c.get('russian', ''))}")

    return "\n".join(lines)


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

        import json
        try:
            translation_data = json.loads(entry["translation"])
            if "translations" in translation_data and translation_data["translations"]:
                first_line = escape_html(translation_data["translations"][0].get("russian", "…"))
            elif "error" in translation_data:
                first_line = "Error"
            else:
                first_line = "…"
        except json.JSONDecodeError:
            # Fallback for old history entries
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
        return dt.strftime("%b %d").replace(" 0", " ")  # e.g. "Jul 3" (cross-platform)
    except Exception:
        return created_at[:10]  # fallback to YYYY-MM-DD
