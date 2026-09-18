import io
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from handlers.journal import handle_audio_thought, notes_command, notes_callback
from config import settings


@pytest.fixture(autouse=True)
def allow_test_user():
    with patch.object(settings, "allowed_user_ids", {12345}):
        yield


@pytest.fixture
def mock_context():
    context = MagicMock()
    context.bot.send_chat_action = AsyncMock()
    context.bot.send_document = AsyncMock()
    context.bot.get_file = AsyncMock()
    context.args = []
    return context


@pytest.mark.asyncio
async def test_handle_audio_thought_too_long(mock_context):
    update = MagicMock()
    update.effective_user.id = 12345
    update.effective_chat.id = 12345
    update.effective_message.voice.duration = 75  # > 60s
    update.effective_message.audio = None
    update.effective_message.reply_text = AsyncMock()

    await handle_audio_thought(update, mock_context)

    update.effective_message.reply_text.assert_called_once()
    args, kwargs = update.effective_message.reply_text.call_args
    assert "Audio is too long" in args[0]
    assert "75s" in args[0]


@pytest.mark.asyncio
async def test_handle_audio_thought_success(mock_context):
    update = MagicMock()
    update.effective_user.id = 12345
    update.effective_chat.id = 12345
    update.effective_message.voice.duration = 30
    update.effective_message.voice.file_id = "test_file_id"
    update.effective_message.voice.mime_type = "audio/ogg"
    update.effective_message.audio = None
    update.effective_message.reply_text = AsyncMock()

    # Mock tg_file download
    mock_file = MagicMock()
    mock_file.download_as_bytearray = AsyncMock(return_value=bytearray(b"ogg_audio_bytes"))
    mock_context.bot.get_file = AsyncMock(return_value=mock_file)

    mock_thought_data = {
        "title": "Cleaned Thought",
        "category": "Ideas",
        "summary": "This is a clean summary.",
        "key_points": ["Point 1"],
        "action_items": [],
        "clean_transcript": "This is the transcript.",
        "tags": ["testing"],
        "language": "en",
    }

    with patch("handlers.journal.process_audio_thought", AsyncMock(return_value=mock_thought_data)), \
         patch("handlers.journal.add_journal_entry", AsyncMock(return_value=42)):
        await handle_audio_thought(update, mock_context)

    update.effective_message.reply_text.assert_called_once()
    call_args = update.effective_message.reply_text.call_args
    sent_text = call_args[0][0]
    assert "💡 <b>Cleaned Thought</b>" in sent_text
    assert "Ideas" in sent_text
    assert "reply_markup" in call_args[1]


@pytest.mark.asyncio
async def test_notes_command_empty(mock_context):
    update = MagicMock()
    update.effective_user.id = 12345
    update.effective_chat.id = 12345
    update.effective_message.reply_text = AsyncMock()

    with patch("handlers.journal.get_journal_entries", AsyncMock(return_value=[])):
        await notes_command(update, mock_context)

    update.effective_message.reply_text.assert_called_once()
    assert "No notes found" in update.effective_message.reply_text.call_args[0][0]


@pytest.mark.asyncio
async def test_notes_command_export(mock_context):
    update = MagicMock()
    update.effective_user.id = 12345
    update.effective_chat.id = 99999
    update.effective_message.reply_text = AsyncMock()
    mock_context.args = ["export"]

    entries = [
        {
            "id": 1,
            "created_at": "2026-09-18 12:00:00",
            "category": "Ideas",
            "title": "Test Idea",
            "summary": "Summary",
            "key_points": [],
            "action_items": [],
            "tags": [],
            "language": "en",
            "raw_transcript": "Transcript",
            "duration_seconds": 20,
        }
    ]

    with patch("handlers.journal.get_all_journal_entries", AsyncMock(return_value=entries)):
        await notes_command(update, mock_context)

    mock_context.bot.send_document.assert_called_once()
    kwargs = mock_context.bot.send_document.call_args[1]
    assert kwargs["filename"].startswith("notes_")
    assert kwargs["filename"].endswith(".csv")
    assert "Exported" in kwargs["caption"]


@pytest.mark.asyncio
async def test_notes_callback_delete(mock_context):
    query = MagicMock()
    query.data = "note_del_42"
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()

    update = MagicMock()
    update.callback_query = query
    update.effective_user.id = 12345

    with patch("handlers.journal.delete_journal_entry", AsyncMock(return_value=True)):
        await notes_callback(update, mock_context)

    query.edit_message_text.assert_called_once()
    assert "Note <b>#42</b> has been deleted" in query.edit_message_text.call_args[0][0]
