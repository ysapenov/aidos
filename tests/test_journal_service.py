import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from services.journal_service import (
    process_audio_thought,
    generate_notes_csv,
    generate_journal_digest,
)


@pytest.mark.asyncio
async def test_process_audio_thought_success():
    mock_json = {
        "title": "Оптимизация базы данных",
        "category": "Work",
        "summary": "Нужно добавить индекс в таблицу заметок.",
        "key_points": ["Добавить индекс", "Проверить скорость"],
        "action_items": ["Создать миграцию"],
        "clean_transcript": "Сегодня я подумал что нужно добавить индекс в таблицу.",
        "tags": ["db", "performance"],
        "language": "ru",
    }

    mock_response = MagicMock()
    mock_response.text = f"```json\n{json.dumps(mock_json, ensure_ascii=False)}\n```"

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    with patch("services.journal_service._get_client", return_value=mock_client):
        result = await process_audio_thought(b"fake_ogg_bytes", "audio/ogg")

    assert result["title"] == "Оптимизация базы данных"
    assert result["category"] == "Work"
    assert result["language"] == "ru"
    assert len(result["key_points"]) == 2
    assert len(result["action_items"]) == 1


@pytest.mark.asyncio
async def test_process_audio_thought_speech_error():
    mock_json = {"error": "No clear speech detected"}
    mock_response = MagicMock()
    mock_response.text = json.dumps(mock_json)

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    with patch("services.journal_service._get_client", return_value=mock_client):
        with pytest.raises(ValueError, match="No clear speech detected"):
            await process_audio_thought(b"noise_bytes", "audio/ogg")


def test_generate_notes_csv():
    entries = [
        {
            "id": 1,
            "created_at": "2026-09-18 12:00:00",
            "category": "Ideas",
            "title": "Новая идея для бота",
            "summary": "Добавить голосовые заметки",
            "key_points": '["Быстро", "Удобно"]',
            "action_items": '["Протестировать"]',
            "tags": '["ai", "audio"]',
            "language": "ru",
            "raw_transcript": "Хочу отправлять аудио до 1 минуты.",
            "duration_seconds": 45,
        }
    ]

    csv_output = generate_notes_csv(entries)
    # Check UTF-8 BOM
    assert csv_output.startswith("\ufeff")
    # Check headers
    assert "Date & Time (UTC)" in csv_output
    assert "Clean Transcript" in csv_output
    # Check row data
    assert "Новая идея для бота" in csv_output
    assert "Быстро" in csv_output
    assert "45" in csv_output


class DummyAPIError(Exception):
    def __init__(self, message: str, code: int | None = None):
        super().__init__(message)
        self.code = code


@pytest.mark.asyncio
async def test_process_audio_thought_with_fallback():
    mock_json = {
        "title": "Fallback Success",
        "category": "Ideas",
        "summary": "Processed via backup model",
        "key_points": ["Point 1"],
        "action_items": [],
        "clean_transcript": "Testing fallback",
        "tags": ["test"],
        "language": "en",
    }
    mock_response = MagicMock()
    mock_response.text = json.dumps(mock_json)

    error_model = DummyAPIError("Model gemini-3.8-flash failed", code=400)

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(side_effect=[error_model, mock_response])

    with patch("services.journal_service._get_client", return_value=mock_client):
        result = await process_audio_thought(b"audio_bytes", "audio/ogg")

    assert result["title"] == "Fallback Success"
    assert mock_client.aio.models.generate_content.call_count == 2
    assert mock_client.aio.models.generate_content.call_args_list[0].kwargs["model"] == "gemini-3.8-flash"
    assert mock_client.aio.models.generate_content.call_args_list[1].kwargs["model"] == "gemini-3.6-flash"


@pytest.mark.asyncio
async def test_generate_journal_digest_with_fallback():
    mock_json = {
        "summary": "Weekly summary",
        "mood_trend": "positive",
        "key_insights": ["Insight 1"],
        "action_items": ["Action 1"],
    }
    mock_response = MagicMock()
    mock_response.text = json.dumps(mock_json)

    error_model = DummyAPIError("Model gemini-3.8-flash failed", code=400)

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(side_effect=[error_model, mock_response])

    entries = [
        {"category": "Work", "title": "Note 1", "summary": "Done", "tags": "[]", "created_at": "2026-11-20"}
    ]

    with patch("services.journal_service._get_client", return_value=mock_client):
        result = await generate_journal_digest(entries, "Weekly Digest")

    assert result["summary"] == "Weekly summary"
    assert mock_client.aio.models.generate_content.call_count == 2
    assert mock_client.aio.models.generate_content.call_args_list[0].kwargs["model"] == "gemini-3.8-flash"
    assert mock_client.aio.models.generate_content.call_args_list[1].kwargs["model"] == "gemini-3.6-flash"
