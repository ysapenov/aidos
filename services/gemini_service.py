"""
services/gemini_service.py — Google Gemini AI wrapper.

Uses the new `google-genai` SDK (google-generativeai is EOL since Nov 2025).
Provides translate_word() for EN→RU translation with examples.
"""

import logging
from google import genai
from config import settings

logger = logging.getLogger(__name__)

# ─── Gemini client (module-level singleton) ────────────────────────────────────
_client = genai.Client(api_key=settings.gemini_api_key)

_TRANSLATION_PROMPT = """You are a professional English-Russian translator and language tutor. \
Your task is to translate a single English word into Russian and provide learning material.

Given the English word: "{word}"

Respond ONLY in the following format (use plain text with these exact emoji and labels):

🗣️ Pronunciation: [insert phonetic transcription here]

🔤 Translations:
• [Russian word] — [brief meaning in English]
• [alternative translation if exists] — [brief meaning]

📝 Part of speech: [noun / verb / adjective / adverb / etc.]

💬 Examples:
1. 🇬🇧 [Example sentence in English using the word]
   🇷🇺 [Russian translation of the sentence]

2. 🇬🇧 [Another example sentence]
   🇷🇺 [Russian translation]

3. 🇬🇧 [Another example sentence]
   🇷🇺 [Russian translation]

🔗 Collocations:
• [common phrase with the word] — [Russian equivalent]
• [another phrase] — [Russian equivalent]

Important rules:
- Always include the English phonetic transcription
- Provide 1-3 Russian translations (most common first)
- Provide exactly 3 example sentences
- Provide 2-3 collocations
- If the word does not exist in English, reply only with: ❌ Unknown word: "{word}"
- Do not add any extra text outside this format
"""


async def translate_word(word: str) -> str:
    """
    Translate a single English word to Russian using Gemini 2.5 Flash.

    Returns the formatted response string ready for Telegram display.
    Raises an exception on API failure (caller handles it).
    """
    word = word.strip().lower()
    prompt = _TRANSLATION_PROMPT.format(word=word)

    logger.info(f"Translating word: '{word}'")

    response = _client.models.generate_content(
        model=settings.gemini_model,
        contents=prompt,
    )

    result = response.text.strip()
    logger.debug(f"Gemini response for '{word}': {result[:100]}...")
    return result
