"""
services/idiom_service.py — Idiom generation and formatting.
"""

import logging
from prompts.idiom import IDIOM_PROMPT
from services.gemini_service import generate_content, parse_json_response
from utils.formatting import escape_html
from utils.constants import EMOJI_FLAG_RU, EMOJI_FLAG_KZ

logger = logging.getLogger(__name__)


async def generate_idiom(exclude_idioms: list[str]) -> dict:
    """
    Generate a daily idiom using Gemini.
    """
    # Cap exclusion list to the most recent 50 entries to avoid prompt bloating
    recent_excludes = exclude_idioms[-50:] if len(exclude_idioms) > 50 else exclude_idioms
    exclude_str = ", ".join(recent_excludes) if recent_excludes else "none"

    prompt = IDIOM_PROMPT.format(exclude_idioms=exclude_str)

    logger.info("Generating idiom. Excluded idioms: %s", len(recent_excludes))
    raw_response = await generate_content(prompt)
    return parse_json_response(raw_response)


def format_idiom_response(data: dict) -> str:
    """
    Format the generated idiom JSON into Telegram HTML.
    """
    idiom = escape_html(str(data.get("idiom", "")))

    lines = ["🎯 <b>Daily Idiom</b>\n", f"<b>{idiom}</b>\n"]

    if data.get("literal_meaning"):
        lines.append(f"Literal: <i>{escape_html(str(data['literal_meaning']))}</i>")
    if data.get("actual_meaning"):
        lines.append(f"Meaning: <b>{escape_html(str(data['actual_meaning']))}</b>\n")

    if data.get("russian_equivalent"):
        lines.append(
            f"{EMOJI_FLAG_RU} Russian: {escape_html(str(data['russian_equivalent']))}"
        )
    if data.get("kazakh_equivalent"):
        lines.append(
            f"{EMOJI_FLAG_KZ} Kazakh: {escape_html(str(data['kazakh_equivalent']))}\n"
        )

    if data.get("example"):
        lines.append(f"💡 Example: <i>{escape_html(str(data['example']))}</i>\n")

    if data.get("used_when"):
        lines.append(f"🤔 Used when: {escape_html(str(data['used_when']))}\n")

    similar = data.get("similar_idioms", [])
    if isinstance(similar, str):
        similar = [s.strip() for s in similar.split(",") if s.strip()]
    if isinstance(similar, list) and similar:
        lines.append("🔄 Similar:")
        for s in similar:
            lines.append(f"• {escape_html(str(s))}")

    return "\n".join(lines).strip()
