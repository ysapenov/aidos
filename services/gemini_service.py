"""
services/gemini_service.py — Google Gemini AI wrapper.

Uses the new `google-genai` SDK (google-generativeai is EOL since Nov 2025).
Provides translate_word() for EN→RU translation with examples.
"""

import json
import re
import logging
from google import genai
from config import settings
from prompts.translation import TRANSLATION_PROMPT

logger = logging.getLogger(__name__)

# ─── Gemini client (module-level singleton) ────────────────────────────────────
_client = None

def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


async def translate_word(word: str) -> dict:
    """
    Translate a single English word to Russian/Kazakh using Gemini 2.5 Flash.

    Returns a parsed JSON dictionary containing the translation data.
    Raises an exception on API failure (caller handles it).
    """
    word = word.strip().lower()
    prompt = TRANSLATION_PROMPT.format(word=word)

    logger.info("Translating word: '%s'", word)

    response = await _get_client().aio.models.generate_content(
        model=settings.gemini_model,
        contents=prompt,
    )

    result = response.text.strip()
    logger.debug("Gemini response for '%s': %s...", word, result[:100])

    return parse_json_response(result)


async def generate_content(prompt: str) -> str:
    """
    Generic wrapper to generate content using Gemini 2.5 Flash.
    Returns the raw text response.
    """
    response = await _get_client().aio.models.generate_content(
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
    # Robust stripping of any markdown code fence (```json, ```, ```python, etc.)
    cleaned = re.sub(r'^```\w*\n?', '', cleaned)
    cleaned = re.sub(r'\n?```$', '', cleaned)
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse JSON from Gemini response: %s", cleaned)
        raise ValueError(f"Invalid JSON response from Gemini: {e}")
