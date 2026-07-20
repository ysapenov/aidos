"""
services/gemini_service.py — Google Gemini AI wrapper.

Uses the new `google-genai` SDK (google-generativeai is EOL since Nov 2025).
Provides translate_word() for EN→RU translation with examples.
"""

import json
import logging
from google import genai
from config import settings
from prompts.translation import TRANSLATION_PROMPT

logger = logging.getLogger(__name__)

# ─── Gemini client (module-level singleton) ────────────────────────────────────
_client = genai.Client(api_key=settings.gemini_api_key)


async def translate_word(word: str) -> str:
    """
    Translate a single English word to Russian/Kazakh using Gemini 2.5 Flash.

    Returns the formatted response string ready for Telegram display.
    Raises an exception on API failure (caller handles it).
    """
    word = word.strip().lower()
    prompt = TRANSLATION_PROMPT.format(word=word)

    logger.info(f"Translating word: '{word}'")

    response = _client.models.generate_content(
        model=settings.gemini_model,
        contents=prompt,
    )

    result = response.text.strip()
    logger.debug(f"Gemini response for '{word}': {result[:100]}...")
    return result


def generate_content(prompt: str) -> str:
    """
    Generic wrapper to generate content using Gemini 2.5 Flash.
    Returns the raw text response.
    """
    response = _client.models.generate_content(
        model=settings.gemini_model,
        contents=prompt,
    )
    return response.text.strip()


def parse_json_response(text: str) -> dict:
    """
    Cleans markdown code blocks (```json ... ```) from Gemini output and parses JSON.
    Raises ValueError on parse failure.
    """
    cleaned = text.strip()
    if cleaned.startswith("```"):
        # Split off the first line (e.g. "```json")
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from Gemini response: {cleaned}")
        raise ValueError(f"Invalid JSON response from Gemini: {e}")
