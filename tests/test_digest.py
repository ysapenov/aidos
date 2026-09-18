import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from database.db import init_db
from database.models import (
    upsert_user,
    add_journal_entry,
    get_journal_entries_in_range,
)
from handlers.journal import digest_command, send_weekly_digest
from services.journal_service import generate_journal_digest
from utils.formatting import format_digest
from config import settings


@pytest_asyncio.fixture
async def temp_db(tmp_path):
    db_path = tmp_path / "test_digest.db"
    with patch.object(settings, "database_path", str(db_path)):
        await init_db()
        yield


@pytest.fixture(autouse=True)
def allow_test_users():
    with patch.object(settings, "allowed_user_ids", {99801, 99802, 99803}):
        yield



@pytest.mark.asyncio
async def test_digest_db_and_service(temp_db):
    user_id = 99801
    await upsert_user(user_id, "digest_user", "DigestUser")

    await add_journal_entry(
        user_id=user_id,
        title="Weekly Win",
        category="Work",
        summary="Launched the new product version.",
        key_points=["Shipped v2.0", "Zero downtime"],
        action_items=["Write announcement"],
        raw_transcript="Everything went smoothly.",
        tags=["launch", "v2"],
        mood="excited",
        energy_level="high",
    )

    # 1. Test get_journal_entries_in_range
    entries = await get_journal_entries_in_range(user_id, "2020-01-01T00:00:00")
    assert len(entries) == 1
    assert entries[0]["title"] == "Weekly Win"
    assert entries[0]["mood"] == "excited"
    assert entries[0]["energy_level"] == "high"

    # 2. Test generate_journal_digest with mock Gemini response
    mock_response = MagicMock()
    mock_response.text = """
    {
      "summary": "High momentum week focused on release.",
      "mood_trend": "Excited with sustained high energy.",
      "key_insights": ["Product launch succeeded without incidents"],
      "action_items": ["Write announcement"],
      "recommendations": ["Prepare customer onboarding sequence"]
    }
    """
    with patch("services.gemini_service._client") as mock_client:
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
        digest = await generate_journal_digest(entries, "Weekly Digest")

    assert digest["total_notes"] == 1
    assert "High momentum" in digest["summary"]
    assert "Excited" in digest["mood_trend"]
    assert len(digest["key_insights"]) == 1

    # 3. Test format_digest
    formatted = format_digest(digest, "Weekly Digest")
    assert "Weekly Digest" in formatted
    assert "High momentum" in formatted
    assert "Shipped v2.0" not in formatted  # It's an executive synthesis
    assert "Write announcement" in formatted


@pytest.mark.asyncio
async def test_digest_command_empty(temp_db):
    user_id = 99802
    await upsert_user(user_id, "digest_user2", "DigestUser2")

    update = MagicMock()
    update.effective_user.id = user_id
    update.effective_message.reply_text = AsyncMock()
    context = MagicMock()
    context.args = []
    context.bot.send_chat_action = AsyncMock()

    with patch("handlers.journal.restricted", lambda f: f):
        await digest_command(update, context)

    update.effective_message.reply_text.assert_called_once()
    assert "No thoughts found" in update.effective_message.reply_text.call_args[0][0]


@pytest.mark.asyncio
async def test_send_weekly_digest_scheduled_job(temp_db):
    user_id = 99803
    await upsert_user(user_id, "digest_user3", "DigestUser3")

    await add_journal_entry(
        user_id=user_id,
        title="Reflective Walk",
        category="Reflection",
        summary="Thinking about quarterly priorities.",
        key_points=["Focus on health"],
        action_items=[],
        raw_transcript="Walked in the park.",
        tags=["walk"],
        mood="calm",
        energy_level="medium",
    )

    mock_response = MagicMock()
    mock_response.text = '{"summary": "Calm reflection.", "mood_trend": "Peaceful.", "key_insights": [], "action_items": [], "recommendations": []}'

    context = MagicMock()
    context.bot.send_message = AsyncMock()

    with patch("services.gemini_service._client") as mock_client:
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
        await send_weekly_digest(context)

    context.bot.send_message.assert_called_once()
    assert context.bot.send_message.call_args[1]["chat_id"] == user_id
