import pytest
from utils.formatting import format_journal_card, format_journal_list


def test_format_journal_card():
    entry = {
        "id": 1,
        "title": "Build voice journaling",
        "category": "Work",
        "summary": "Implement voice note processing using Gemini 3.8 Flash.",
        "key_points": ["Capture voice messages", "Export as CSV"],
        "action_items": ["Write unit tests", "Deploy to container"],
        "raw_transcript": "I want to add voice journaling to the bot.",
        "tags": ["feature", "gemini"],
        "language": "en",
        "duration_seconds": 45,
        "created_at": "2026-09-18T12:00:00",
    }
    card = format_journal_card(entry)
    assert "💼 <b>Build voice journaling</b>" in card
    assert "Work" in card
    assert "45s" in card
    assert "Capture voice messages" in card
    assert "☑ Write unit tests" in card
    assert "#feature #gemini" in card
    assert "I want to add voice journaling" in card


def test_format_journal_card_minimal():
    entry = {
        "title": "Quick thought",
        "category": "Ideas",
        "summary": "A brief idea",
        "created_at": "2026-09-18T12:00:00",
    }
    card = format_journal_card(entry)
    assert "💡 <b>Quick thought</b>" in card
    assert "Ideas" in card
    assert "A brief idea" in card


def test_format_journal_list():
    entries = [
        {
            "id": 1,
            "title": "Thought One",
            "category": "Ideas",
            "created_at": "2026-09-18T12:00:00",
        },
        {
            "id": 2,
            "title": "Thought Two",
            "category": "Personal",
            "created_at": "2026-09-18T12:30:00",
        },
    ]
    formatted = format_journal_list(entries)
    assert "Thought One" in formatted
    assert "Thought Two" in formatted
    assert "#1" in formatted
    assert "#2" in formatted


def test_format_journal_list_empty():
    assert "No notes found" in format_journal_list([])
