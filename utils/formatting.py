"""
utils/formatting.py — Telegram message formatting helpers.
"""

import html
import json
from datetime import datetime
from utils.constants import (
    EMOJI_BOOK,
    EMOJI_HISTORY,
    EMOJI_ARROW,
    EMOJI_WARNING,
    EMOJI_FLAG_KZ,
    EMOJI_TARGET,
    EMOJI_MIC,
    EMOJI_NOTE,
    EMOJI_IDEA,
    EMOJI_TAG,
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


def format_vocabulary_history(entries: list[dict]) -> str:
    """Format the vocabulary history list for Telegram display."""
    if not entries:
        return f"{EMOJI_HISTORY} You haven't generated any vocabulary yet."

    lines = [f"{EMOJI_BOOK} <b>Your Vocabulary History</b>\n"]
    for i, entry in enumerate(entries, start=1):
        word = escape_html(entry["english_text"])
        rus = escape_html(entry.get("russian_text") or "…")
        kaz = escape_html(entry.get("kazakh_text") or "")
        kaz_str = f" = {kaz}" if kaz else ""
        date_str = _format_date(entry["created_at"])
        lines.append(f"{i}. <b>{word}</b> — {rus}{kaz_str} <i>({date_str})</i>")

    return "\n".join(lines)


def format_idiom_history(entries: list[dict]) -> str:
    """Format the idiom history list for Telegram display."""
    if not entries:
        return f"{EMOJI_HISTORY} No idioms have been sent yet."

    lines = [f"{EMOJI_TARGET} <b>Recent Daily Idioms</b>\n"]
    for i, entry in enumerate(entries, start=1):
        idiom = escape_html(entry["idiom"])
        rus = escape_html(entry.get("russian_equivalent") or "…")
        kaz = escape_html(entry.get("kazakh_equivalent") or "")
        kaz_str = f" = {kaz}" if kaz else ""
        date_str = _format_date(entry["sent_at"])
        lines.append(f"{i}. <b>{idiom}</b> — {rus}{kaz_str} <i>({date_str})</i>")

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
        return dt.strftime("%b %d %H:%M").replace(" 0", " ")  # e.g. "Jul 3 14:30"
    except Exception:
        return created_at[:16] if len(created_at) >= 16 else created_at


CATEGORY_ICONS = {
    "ideas": "💡",
    "work": "💼",
    "personal": "👤",
    "learning": "📚",
    "health": "🏃",
    "to-do": "📋",
    "todo": "📋",
    "reflection": "🪞",
    "other": "📝",
}


def format_journal_card(entry: dict) -> str:
    """Format a saved journal entry for Telegram display."""
    category = entry.get("category", "Other")
    cat_lower = str(category).lower()
    icon = CATEGORY_ICONS.get(cat_lower, "📝")

    title = escape_html(entry.get("title") or "Untitled Thought")
    created_at = entry.get("created_at", "")
    date_str = _format_date(created_at) if created_at else "Just now"

    duration = entry.get("duration_seconds")
    duration_str = f" • ⏱️ {duration}s" if duration else ""

    lines = [
        f"{icon} <b>{title}</b>",
        f"🏷 <i>{escape_html(category)}</i> • 📅 <i>{date_str}{duration_str}</i>",
    ]

    mood = entry.get("mood")
    energy = entry.get("energy_level")
    if mood or energy:
        mood_str = f"🎭 <i>{escape_html(str(mood).capitalize())}</i>" if mood else ""
        energy_str = f"⚡ <i>{escape_html(str(energy).capitalize())} energy</i>" if energy else ""
        combined = " • ".join(filter(None, [mood_str, energy_str]))
        lines.append(combined)

    lines.append(f"{'─' * 28}")

    summary = entry.get("summary")
    if summary:
        lines.append(f"\n<b>Summary:</b>\n{escape_html(summary)}")


    # Key points
    key_points = entry.get("key_points")
    if isinstance(key_points, str):
        try:
            key_points = json.loads(key_points)
        except Exception:
            key_points = [key_points] if key_points else []
    if key_points and isinstance(key_points, list):
        lines.append("\n<b>Key Points:</b>")
        for point in key_points:
            lines.append(f"• {escape_html(str(point))}")

    # Action items
    action_items = entry.get("action_items")
    if isinstance(action_items, str):
        try:
            action_items = json.loads(action_items)
        except Exception:
            action_items = [action_items] if action_items else []
    if action_items and isinstance(action_items, list):
        lines.append("\n<b>Action Items:</b>")
        for item in action_items:
            lines.append(f"☑ {escape_html(str(item))}")

    # Tags
    tags = entry.get("tags")
    if isinstance(tags, str):
        try:
            tags = json.loads(tags)
        except Exception:
            tags = [t.strip() for t in tags.split(",") if t.strip()]
    if tags and isinstance(tags, list):
        tag_line = " ".join(f"#{escape_html(str(t).lstrip('#'))}" for t in tags if t)
        if tag_line:
            lines.append(f"\n🏷 {tag_line}")

    # Transcript
    raw_transcript = entry.get("raw_transcript") or entry.get("clean_transcript")
    if raw_transcript:
        lines.append(f"\n💬 <i>Clean transcript:</i>\n\"{escape_html(raw_transcript)}\"")

    return "\n".join(lines)


def format_journal_list(entries: list[dict]) -> str:
    """Format list of recent journal entries."""
    if not entries:
        return "<i>No notes found.</i>"

    lines = [f"{EMOJI_NOTE} <b>Your Recent Thoughts</b>", f"{'─' * 28}"]
    for entry in entries:
        entry_id = entry.get("id", "")
        category = entry.get("category", "Other")
        icon = CATEGORY_ICONS.get(str(category).lower(), "📝")
        title = escape_html(entry.get("title") or "Untitled Thought")
        created_at = entry.get("created_at", "")
        date_str = _format_date(created_at) if created_at else ""

        lines.append(f"{icon} <b>#{entry_id}</b> — {title}")
        lines.append(f"   🏷 <i>{escape_html(category)}</i> • <i>{date_str}</i>\n")

    lines.append("<i>Type /notes &lt;id&gt; to view details or use the buttons below.</i>")
    return "\n".join(lines)


def format_action_items_list(items: list[dict], show_completed: bool = False) -> str:
    """Format action items list for /actions command."""
    if not items:
        return "<i>No action items found.</i>"

    header = "📋 <b>All Action Items</b>" if show_completed else "📋 <b>Pending Action Items</b>"
    lines = [header, f"{'─' * 28}"]

    for item in items:
        is_done = bool(item.get("is_completed"))
        icon = "✅" if is_done else "⬜"
        item_id = item.get("id")
        text = escape_html(item.get("task_text", ""))
        if is_done:
            text = f"<s>{text}</s>"
        lines.append(f"{icon} <b>#{item_id}</b> {text}")

    if not show_completed:
        lines.append("\n<i>Tap a button below to check off or delete an action item.</i>")
    return "\n".join(lines)


def format_digest(digest: dict, period_name: str = "Weekly Digest") -> str:
    """Format AI synthesized reflection digest."""
    total = digest.get("total_notes", 0)
    lines = [
        f"📊 <b>{escape_html(period_name)}</b>",
        f"<i>Thoughts analyzed: {total}</i>",
        f"{'─' * 28}",
    ]

    if digest.get("summary"):
        lines.append(f"\n<b>Executive Summary:</b>\n{escape_html(digest['summary'])}")

    if digest.get("mood_trend"):
        lines.append(f"\n🎭 <b>Mood & Momentum:</b>\n{escape_html(digest['mood_trend'])}")

    if digest.get("key_insights"):
        lines.append("\n🌟 <b>Standout Insights:</b>")
        for ins in digest["key_insights"]:
            lines.append(f"• {escape_html(str(ins))}")

    if digest.get("action_items"):
        lines.append("\n🎯 <b>Key Action Items:</b>")
        for act in digest["action_items"]:
            lines.append(f"☑ {escape_html(str(act))}")

    if digest.get("recommendations"):
        lines.append("\n💡 <b>Recommended Focus:</b>")
        for rec in digest["recommendations"]:
            lines.append(f"→ {escape_html(str(rec))}")

    return "\n".join(lines)


