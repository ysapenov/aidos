"""
services/vocabulary_service.py — Vocabulary generation and formatting.
"""

import logging
from typing import Optional
from prompts.vocabulary import VOCABULARY_PROMPT
from services.gemini_service import generate_content, parse_json_response
from utils.formatting import escape_html
from utils.constants import (
    EMOJI_BOOK,
    EMOJI_LINK,
    EMOJI_EXAMPLES,
    EMOJI_FLAG_RU,
    EMOJI_FLAG_KZ,
)

logger = logging.getLogger(__name__)


def generate_vocabulary(topic: Optional[str], exclude_words: list[str]) -> dict:
    """
    Generate vocabulary using Gemini.
    """
    if topic:
        topic_instruction = f"Topic to focus on: {topic}"
    else:
        topic_instruction = "Choose a random useful topic."

    exclude_str = ", ".join(exclude_words) if exclude_words else "none"

    prompt = VOCABULARY_PROMPT.format(
        topic_instruction=topic_instruction, exclude_words=exclude_str
    )

    logger.info(
        f"Generating vocabulary. Topic: {topic or 'random'}, Excluded words: {len(exclude_words)}"
    )
    raw_response = generate_content(prompt)
    return parse_json_response(raw_response)


def format_vocabulary_response(data: dict) -> str:
    """
    Format the generated vocabulary JSON into Telegram HTML.
    """
    topic = escape_html(data.get("topic", "General"))
    lines = [f"🎯 <b>Topic:</b> {topic}\n"]

    # 1. Words
    words = data.get("words", [])
    if words:
        lines.append(f"{EMOJI_BOOK} <b>Advanced Words</b>\n")
        for w in words:
            word_eng = escape_html(w.get("english", ""))
            ipa = escape_html(w.get("ipa", ""))
            pos = escape_html(w.get("part_of_speech", ""))
            level = escape_html(w.get("cefr_level", ""))

            lines.append(f"<b>{word_eng}</b> {ipa} <i>({pos}, {level})</i>")

            # Definition
            if w.get("definition"):
                lines.append(f"📖 {escape_html(w['definition'])}")

            # Translations
            if w.get("russian"):
                lines.append(f"{EMOJI_FLAG_RU} Russian: {escape_html(w['russian'])}")
            if w.get("kazakh"):
                lines.append(f"{EMOJI_FLAG_KZ} Kazakh: {escape_html(w['kazakh'])}")

            # Example
            if w.get("example"):
                lines.append(f"💡 Example: <i>{escape_html(w['example'])}</i>")

            # Collocations
            collocs = w.get("collocations", [])
            if collocs:
                safe_collocs = [escape_html(c) for c in collocs]
                lines.append(f"🔗 Collocations: {', '.join(safe_collocs)}")

            # Synonyms
            syns = w.get("synonyms", [])
            if syns:
                safe_syns = [escape_html(s) for s in syns]
                lines.append(f"🔄 Synonyms: {', '.join(safe_syns)}")

            lines.append("")

    # 2. Phrasal Verbs
    phrasal_verbs = data.get("phrasal_verbs", [])
    if phrasal_verbs:
        lines.append(f"{EMOJI_LINK} <b>Phrasal Verbs</b>\n")
        for pv in phrasal_verbs:
            pv_eng = escape_html(pv.get("english", ""))
            lines.append(f"<b>{pv_eng}</b>")

            if pv.get("meaning"):
                lines.append(f"📖 Meaning: {escape_html(pv['meaning'])}")

            if pv.get("russian"):
                lines.append(f"{EMOJI_FLAG_RU} Russian: {escape_html(pv['russian'])}")
            if pv.get("kazakh"):
                lines.append(f"{EMOJI_FLAG_KZ} Kazakh: {escape_html(pv['kazakh'])}")

            if pv.get("example"):
                lines.append(f"💡 Example: <i>{escape_html(pv['example'])}</i>")

            used_in = pv.get("used_in", [])
            if used_in:
                lines.append(
                    f"📌 Used in: {', '.join([escape_html(u) for u in used_in])}"
                )

            related = pv.get("related", [])
            if related:
                lines.append(
                    f"🔄 Related: {', '.join([escape_html(r) for r in related])}"
                )

            lines.append("")

    # 3. Expressions
    expressions = data.get("expressions", [])
    if expressions:
        lines.append(f"{EMOJI_EXAMPLES} <b>Natural Expressions</b>\n")
        for expr in expressions:
            expr_eng = escape_html(expr.get("english", ""))
            lines.append(f"<b>{expr_eng}</b>")

            if expr.get("meaning"):
                lines.append(f"📖 Meaning: {escape_html(expr['meaning'])}")

            if expr.get("russian"):
                lines.append(f"{EMOJI_FLAG_RU} Russian: {escape_html(expr['russian'])}")
            if expr.get("kazakh"):
                lines.append(f"{EMOJI_FLAG_KZ} Kazakh: {escape_html(expr['kazakh'])}")

            if expr.get("example"):
                lines.append(f"💡 Example: <i>{escape_html(expr['example'])}</i>")

            if expr.get("used_when"):
                lines.append(f"🤔 Used when: {escape_html(expr['used_when'])}")

            if expr.get("formality"):
                lines.append(f"👔 Formality: {escape_html(expr['formality'])}")

            similar = expr.get("similar", [])
            if similar:
                lines.append(
                    f"🔄 Similar: {', '.join([escape_html(s) for s in similar])}"
                )

            lines.append("")

    return "\n".join(lines).strip()
