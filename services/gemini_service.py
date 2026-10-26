"""
services/gemini_service.py — Google Gemini AI wrapper.

Uses the new `google-genai` SDK (google-generativeai is EOL since Nov 2025).
Provides translate_word() for EN→RU translation with examples.
"""

import asyncio
import json
import logging
import random
import re
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


def is_transient_error(e: Exception) -> bool:
    """
    Determine if an exception represents a transient Gemini API or network failure
    that should be retried.
    """
    # 1. Check google-genai / HTTP error code if available
    code = getattr(e, "code", None)
    if code is not None:
        try:
            code_int = int(code)
            if code_int in (429, 500, 502, 503, 504):
                return True
            if 400 <= code_int < 500:
                # Permanent client errors (400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found)
                return False
        except (ValueError, TypeError):
            pass

    # 2. Check status string (e.g. 'UNAVAILABLE', 'RESOURCE_EXHAUSTED')
    status = getattr(e, "status", None)
    if isinstance(status, str):
        status_upper = status.upper()
        if any(s in status_upper for s in ("UNAVAILABLE", "RESOURCE_EXHAUSTED", "DEADLINE_EXCEEDED", "INTERNAL")):
            return True

    # 3. Transient network and asyncio timeouts
    if isinstance(e, (asyncio.TimeoutError, TimeoutError, ConnectionResetError, ConnectionError, BrokenPipeError)):
        return True

    # 4. Check error message / string representation for transient keywords
    msg = str(e).lower()
    transient_keywords = (
        "503",
        "unavailable",
        "high demand",
        "spikes in demand",
        "please try again later",
        "429",
        "resource exhausted",
        "rate limit",
        "temporarily unavailable",
        "server error",
        "internal server error",
        "timeout",
        "timed out",
    )
    if any(keyword in msg for keyword in transient_keywords):
        non_transient_keywords = ("400 bad request", "invalid argument", "api_key not valid", "permission denied")
        if not any(nt in msg for nt in non_transient_keywords):
            return True

    return False


async def call_with_retry(
    async_func,
    *args,
    max_retries: int | None = None,
    initial_delay: float | None = None,
    backoff_factor: float = 2.0,
    max_delay: float = 10.0,
    **kwargs,
):
    """
    Executes an async Gemini API call with exponential backoff and jitter for transient errors.

    Args:
        async_func: Async callable to execute (e.g. client.aio.models.generate_content).
        *args: Positional arguments for async_func.
        max_retries: Max retry attempts (defaults to settings.gemini_max_retries).
        initial_delay: Initial delay in seconds (defaults to settings.gemini_initial_retry_delay).
        backoff_factor: Multiplier for subsequent retry delays (default: 2.0).
        max_delay: Cap on maximum sleep duration per retry (default: 10.0s).
        **kwargs: Keyword arguments for async_func.

    Returns:
        The result of async_func(*args, **kwargs).

    Raises:
        The last caught exception if non-transient or retries are exhausted.
    """
    retries = max_retries if max_retries is not None else settings.gemini_max_retries
    delay = initial_delay if initial_delay is not None else settings.gemini_initial_retry_delay
    last_exception = None

    for attempt in range(1, retries + 2):
        try:
            return await async_func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt <= retries and is_transient_error(e):
                jitter = random.uniform(0.1, 0.5)
                actual_delay = min(delay + jitter, max_delay)
                logger.warning(
                    "Gemini API transient failure: %s (attempt %d/%d). Retrying in %.2fs...",
                    e,
                    attempt,
                    retries + 1,
                    actual_delay,
                )
                await asyncio.sleep(actual_delay)
                delay *= backoff_factor
            else:
                if attempt > retries and is_transient_error(e):
                    logger.error(
                        "Gemini API transient failure exceeded %d retries: %s",
                        retries,
                        e,
                    )
                else:
                    logger.error(
                        "Gemini API non-transient error (attempt %d/%d): %s",
                        attempt,
                        retries + 1,
                        e,
                    )
                raise last_exception


async def translate_word(word: str) -> dict:
    """
    Translate a single English word to Russian/Kazakh using Gemini 2.5 Flash.

    Returns a parsed JSON dictionary containing the translation data.
    Raises an exception on API failure (caller handles it).
    """
    word = word.strip().lower()
    prompt = TRANSLATION_PROMPT.format(word=word)

    logger.info("Translating word: '%s'", word)

    client = _get_client()
    response = await call_with_retry(
        client.aio.models.generate_content,
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
    client = _get_client()
    response = await call_with_retry(
        client.aio.models.generate_content,
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
