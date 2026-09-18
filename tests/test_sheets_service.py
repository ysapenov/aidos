import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from services.sheets_service import (
    is_sheets_configured,
    sync_note_to_sheets,
    sync_all_notes_to_sheets,
    _format_entry_row,
    SHEET_HEADERS,
)
from handlers.journal import sync_sheets_command
from config import settings


import services.sheets_service as sheets_module


@pytest.fixture(autouse=True)
def reset_sheets_globals():
    sheets_module._gc = None
    sheets_module._spreadsheet = None
    yield
    sheets_module._gc = None
    sheets_module._spreadsheet = None


def test_is_sheets_configured_default():
    with patch.object(settings, "google_sheet_id", ""), patch.object(settings, "google_sheets_credentials_file", ""), patch.object(settings, "google_sheets_credentials_json", ""):
        assert is_sheets_configured() is False


def test_is_sheets_configured_with_json():
    with patch.object(settings, "google_sheet_id", "sheet_123"), patch.object(settings, "google_sheets_credentials_json", '{"type": "service_account"}'):
        assert is_sheets_configured() is True



def test_format_entry_row():
    entry = {
        "id": 42,
        "created_at": "2026-09-18 12:00:00",
        "category": "Ideas",
        "title": "New System",
        "summary": "Building automated bots.",
        "mood": "focused",
        "energy_level": "high",
        "key_points": ["Point 1", "Point 2"],
        "action_items": ["Deploy"],
        "tags": ["tech", "ai"],
        "language": "en",
        "raw_transcript": "Raw text here.",
        "duration_seconds": 25,
    }
    row = _format_entry_row(entry)
    assert len(row) == len(SHEET_HEADERS)
    assert row[0] == 42
    assert row[2] == "Ideas"
    assert row[5] == "focused"
    assert row[6] == "high"
    assert "• Point 1" in row[7]
    assert "Deploy" in row[8]
    assert "tech, ai" in row[9]


@pytest.mark.asyncio
async def test_sync_note_to_sheets_mock():
    mock_worksheet = MagicMock()
    mock_worksheet.row_values.return_value = ["ID"]  # Headers already exist
    mock_worksheet.append_row.return_value = None

    mock_spreadsheet = MagicMock()
    mock_spreadsheet.worksheet.return_value = mock_worksheet
    mock_gc = MagicMock()
    mock_gc.open_by_key.return_value = mock_spreadsheet

    with patch("services.sheets_service.is_sheets_configured", return_value=True), \
         patch("gspread.service_account", return_value=mock_gc):
        success = await sync_note_to_sheets({"id": 1, "title": "Test"})
        assert success is True
        mock_worksheet.append_row.assert_called_once()


@pytest.mark.asyncio
async def test_sync_all_notes_to_sheets_mock():
    mock_worksheet = MagicMock()
    mock_worksheet.row_values.return_value = ["ID"]
    mock_worksheet.append_rows.return_value = None

    mock_spreadsheet = MagicMock()
    mock_spreadsheet.worksheet.return_value = mock_worksheet
    mock_gc = MagicMock()
    mock_gc.open_by_key.return_value = mock_spreadsheet

    with patch("services.sheets_service.is_sheets_configured", return_value=True), \
         patch("gspread.service_account", return_value=mock_gc):
        count = await sync_all_notes_to_sheets([{"id": 1}, {"id": 2}])
        assert count == 2
        mock_worksheet.append_rows.assert_called_once()


@pytest.mark.asyncio
async def test_sync_sheets_command_unconfigured():
    update = MagicMock()
    update.effective_message.reply_text = AsyncMock()
    context = MagicMock()

    with patch("services.sheets_service.is_sheets_configured", return_value=False):
        await sync_sheets_command(update, context)

    update.effective_message.reply_text.assert_called_once()
    assert "Google Sheets is not configured" in update.effective_message.reply_text.call_args[0][0]
