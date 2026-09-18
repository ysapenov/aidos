import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from database.db import init_db
from database.models import (
    upsert_user,
    add_journal_entry,
    get_journal_entry_by_id,
    update_journal_category,
)
from handlers.journal import notes_callback
from services.journal_service import process_audio_thought, generate_notes_csv
from utils.formatting import format_journal_card
from config import settings


@pytest_asyncio.fixture
async def temp_db(tmp_path):
    db_path = tmp_path / "test_cat_mood.db"
    with patch.object(settings, "database_path", str(db_path)):
        await init_db()
        yield


@pytest.mark.asyncio
async def test_category_update_and_callback(temp_db):
    user_id = 99701
    await upsert_user(user_id, "user_cat", "UserCat")

    entry_id = await add_journal_entry(
        user_id=user_id,
        title="Initial Thought",
        category="Ideas",
        summary="A concept to explore.",
        key_points=[],
        action_items=[],
        raw_transcript="Initial voice note.",
        tags=[],
        mood="calm",
        energy_level="low",
    )

    # 1. DB Model test
    updated = await update_journal_category(entry_id, user_id, "Work")
    assert updated is True

    entry = await get_journal_entry_by_id(entry_id, user_id)
    assert entry["category"] == "Work"

    # 2. Category selection callback test: note_setcat_<id>_<category>
    update = MagicMock()
    update.effective_user.id = user_id
    update.callback_query.data = f"note_setcat_{entry_id}_Learning"
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    context = MagicMock()

    await notes_callback(update, context)

    update.callback_query.answer.assert_called_once()
    update.callback_query.edit_message_text.assert_called_once()
    assert "Learning" in update.callback_query.edit_message_text.call_args[0][0]

    # Verify updated in DB
    entry_after = await get_journal_entry_by_id(entry_id, user_id)
    assert entry_after["category"] == "Learning"


@pytest.mark.asyncio
async def test_mood_energy_in_service_and_csv():
    mock_response = MagicMock()
    mock_response.text = """
    {
      "title": "Strategy Session",
      "category": "Work",
      "summary": "Reviewed quarterly OKRs.",
      "key_points": ["Achieved goal 1"],
      "action_items": ["Plan Q3"],
      "clean_transcript": "Reviewed the goals today.",
      "tags": ["strategy"],
      "language": "en",
      "mood": "focused",
      "energy_level": "high"
    }
    """
    with patch("services.gemini_service._client") as mock_client:
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
        data = await process_audio_thought(b"fake_bytes", "audio/ogg")

    assert data["mood"] == "focused"
    assert data["energy_level"] == "high"

    # Test CSV output
    entries = [{
        "id": 10,
        "created_at": "2026-09-18 10:00:00",
        "category": "Work",
        "title": "Strategy Session",
        "summary": "Reviewed OKRs",
        "mood": "focused",
        "energy_level": "high",
        "key_points": ["Achieved goal 1"],
        "action_items": ["Plan Q3"],
        "tags": ["strategy"],
        "language": "en",
        "raw_transcript": "Reviewed goals",
        "duration_seconds": 45,
    }]
    csv_str = generate_notes_csv(entries)
    assert "Mood" in csv_str
    assert "Energy Level" in csv_str
    assert "focused" in csv_str
    assert "high" in csv_str


def test_format_journal_card_with_mood():
    entry = {
        "id": 1,
        "title": "Morning Thought",
        "category": "Ideas",
        "summary": "Inventing things",
        "mood": "inspired",
        "energy_level": "high",
        "created_at": "2026-09-18T10:00:00",
    }
    card = format_journal_card(entry)
    assert "Inspired" in card
    assert "High energy" in card
