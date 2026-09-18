"""
services/journal_service.py — Audio thought processing and journal export service.

Uses Google Gemini (with configurable settings.journal_model) to transcribe,
filter noise, structure thoughts into categories, and export notes as CSV.
"""

import csv
import io
import json
import logging
from typing import Any
from google.genai import types
from config import settings
from services.gemini_service import _get_client, parse_json_response
from prompts.journal import JOURNAL_STRUCTURING_PROMPT

logger = logging.getLogger(__name__)


async def process_audio_thought(audio_bytes: bytes, mime_type: str = "audio/ogg") -> dict[str, Any]:
    """
    Transcribe and structure an audio recording using the dedicated Gemini journal model.

    Args:
        audio_bytes: Raw audio byte content.
        mime_type: MIME type of the audio (e.g. 'audio/ogg', 'audio/mpeg', 'audio/wav').

    Returns:
        A dictionary matching the thought structure:
        {
            "title": str,
            "category": str,
            "summary": str,
            "key_points": list[str],
            "action_items": list[str],
            "clean_transcript": str,
            "tags": list[str],
            "language": str,
        }

    Raises:
        ValueError: If speech cannot be detected or JSON is invalid.
    """
    client = _get_client()

    audio_part = types.Part.from_bytes(
        data=audio_bytes,
        mime_type=mime_type,
    )

    logger.info(
        "Processing audio thought with model '%s' (bytes=%d, mime=%s)",
        settings.journal_model,
        len(audio_bytes),
        mime_type,
    )

    response = await client.aio.models.generate_content(
        model=settings.journal_model,
        contents=[audio_part, JOURNAL_STRUCTURING_PROMPT],
    )

    raw_text = response.text.strip() if response.text else ""
    if not raw_text:
        raise ValueError("Received empty response from Gemini model.")

    logger.debug("Raw Gemini response: %s", raw_text[:200])

    data = parse_json_response(raw_text)

    # Check for inaudible / error flags
    if "error" in data:
        raise ValueError(data["error"])

    # Normalise fields to ensure robust structure
    title = str(data.get("title", "Untitled Thought")).strip()
    category = str(data.get("category", "Other")).strip()
    summary = str(data.get("summary", "")).strip()

    key_points = data.get("key_points", [])
    if isinstance(key_points, str):
        key_points = [key_points] if key_points else []

    action_items = data.get("action_items", [])
    if isinstance(action_items, str):
        action_items = [action_items] if action_items else []

    clean_transcript = str(data.get("clean_transcript", "")).strip()

    tags = data.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]

    language = str(data.get("language", "auto")).strip().lower()
    mood = str(data.get("mood", "neutral")).strip().lower()
    energy_level = str(data.get("energy_level", "medium")).strip().lower()

    return {
        "title": title or "Untitled Thought",
        "category": category or "Other",
        "summary": summary,
        "key_points": key_points,
        "action_items": action_items,
        "clean_transcript": clean_transcript,
        "tags": tags,
        "language": language,
        "mood": mood or "neutral",
        "energy_level": energy_level or "medium",
    }


def generate_notes_csv(entries: list[dict]) -> str:
    """
    Format a list of journal entries into a clean CSV string.
    Includes UTF-8 BOM (\\ufeff) for compatibility with Microsoft Excel on Windows.
    """
    output = io.StringIO()
    # Write UTF-8 BOM
    output.write("\ufeff")

    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    writer.writerow([
        "ID",
        "Date & Time (UTC)",
        "Category",
        "Title",
        "Summary",
        "Key Points",
        "Action Items",
        "Tags",
        "Language",
        "Mood",
        "Energy Level",
        "Clean Transcript",
        "Duration (s)",
    ])

    for entry in entries:
        key_points_str = _to_bullet_string(entry.get("key_points"))
        action_items_str = _to_bullet_string(entry.get("action_items"))
        tags_str = _to_tag_string(entry.get("tags"))

        writer.writerow([
            entry.get("id", ""),
            entry.get("created_at", ""),
            entry.get("category", ""),
            entry.get("title", ""),
            entry.get("summary", ""),
            key_points_str,
            action_items_str,
            tags_str,
            entry.get("language", ""),
            entry.get("mood", ""),
            entry.get("energy_level", ""),
            entry.get("raw_transcript", ""),
            entry.get("duration_seconds", ""),
        ])

    return output.getvalue()


async def generate_journal_digest(entries: list[dict], period_name: str = "Last 7 Days") -> dict[str, Any]:
    """
    Synthesize multiple journal entries into an executive digest using Gemini.

    Args:
        entries: List of journal entry dictionaries.
        period_name: Descriptive name for the time span (e.g. "Weekly Digest", "Monthly Digest").

    Returns:
        Structured digest dictionary with summary, mood_trend, key_insights, action_items, recommendations.
    """
    if not entries:
        return {
            "period": period_name,
            "total_notes": 0,
            "summary": "No thoughts were recorded during this period.",
            "mood_trend": "No data available.",
            "key_insights": [],
            "action_items": [],
            "recommendations": ["Record your thoughts regularly with voice notes to generate insights."],
        }

    # Prepare compact representation for prompt
    condensed_entries = []
    for e in entries:
        condensed_entries.append({
            "id": e.get("id"),
            "date": e.get("created_at", "")[:16],
            "category": e.get("category"),
            "title": e.get("title"),
            "summary": e.get("summary"),
            "key_points": e.get("key_points"),
            "action_items": e.get("action_items"),
            "mood": e.get("mood", "neutral"),
            "energy_level": e.get("energy_level", "medium"),
        })

    entries_json = json.dumps(condensed_entries, ensure_ascii=False, indent=2)
    from prompts.journal import JOURNAL_DIGEST_PROMPT
    prompt = (
        JOURNAL_DIGEST_PROMPT.replace("{period_name}", period_name)
        .replace("{entries_json}", entries_json)
    )


    client = _get_client()
    logger.info("Generating %s with model '%s' (%d notes)", period_name, settings.journal_model, len(entries))

    response = await client.aio.models.generate_content(
        model=settings.journal_model,
        contents=[prompt],
    )

    raw_text = response.text.strip() if response.text else ""
    if not raw_text:
        raise ValueError("Received empty digest response from Gemini model.")

    data = parse_json_response(raw_text)

    return {
        "period": period_name,
        "total_notes": len(entries),
        "summary": str(data.get("summary", "")).strip(),
        "mood_trend": str(data.get("mood_trend", "")).strip(),
        "key_insights": data.get("key_insights", []) if isinstance(data.get("key_insights"), list) else [],
        "action_items": data.get("action_items", []) if isinstance(data.get("action_items"), list) else [],
        "recommendations": data.get("recommendations", []) if isinstance(data.get("recommendations"), list) else [],
    }


def _to_bullet_string(val: Any) -> str:
    """Convert a JSON-encoded list or plain string into a bullet-point string."""
    if isinstance(val, str):
        try:
            val = json.loads(val)
        except Exception:
            return val
    if isinstance(val, list):
        return "\n".join(f"• {item}" for item in val)
    return str(val) if val else ""


def _to_tag_string(val: Any) -> str:
    """Convert a JSON-encoded list or plain string into a comma-separated tag string."""
    if isinstance(val, str):
        try:
            val = json.loads(val)
        except Exception:
            return val
    if isinstance(val, list):
        return ", ".join(val)
    return str(val) if val else ""


