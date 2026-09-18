import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from services.journal_service import process_audio_thought, generate_notes_csv


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
