"""
prompts/__init__.py — English learning prompt templates for Gemini.
"""

from prompts.translation import TRANSLATION_PROMPT
from prompts.vocabulary import VOCABULARY_PROMPT
from prompts.idiom import IDIOM_PROMPT

__all__ = [
    "TRANSLATION_PROMPT",
    "VOCABULARY_PROMPT",
    "IDIOM_PROMPT",
]
