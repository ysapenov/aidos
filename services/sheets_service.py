"""
services/sheets_service.py — Google Sheets sync service for Aidos thoughts journal.

Uses gspread with Google Cloud service account authentication to append notes
to a configured Google Sheet. Non-blocking via asyncio.to_thread.
"""

import asyncio
import json
import logging
import os
from typing import Any, Optional
import gspread
from config import settings

logger = logging.getLogger(__name__)

_gc: Optional[gspread.Client] = None
_spreadsheet: Optional[gspread.Spreadsheet] = None

SHEET_HEADERS = [
    "ID",
    "Date & Time (UTC)",
    "Category",
    "Title",
    "Summary",
    "Mood",
    "Energy Level",
    "Key Points",
    "Action Items",
    "Tags",
    "Language",
    "Clean Transcript",
    "Duration (s)",
]


def is_sheets_configured() -> bool:
    """Return True if both Google Sheet ID and credentials (file or JSON string) are configured."""
    if not settings.google_sheet_id:
        return False
    if settings.google_sheets_credentials_json:
        return True
    if settings.google_sheets_credentials_file:
        return os.path.isfile(settings.google_sheets_credentials_file)
    return False


def _get_worksheet(title: str = "Notes") -> Optional[gspread.Worksheet]:
    """Internal helper to get or create the target worksheet tab."""
    global _gc, _spreadsheet

    if not is_sheets_configured():
        return None

    try:
        if _gc is None:
            if settings.google_sheets_credentials_json:
                creds_data = json.loads(settings.google_sheets_credentials_json)
                _gc = gspread.service_account_from_dict(creds_data)
            else:
                _gc = gspread.service_account(filename=settings.google_sheets_credentials_file)
            _spreadsheet = _gc.open_by_key(settings.google_sheet_id)
            logger.info("Connected to Google Spreadsheet: '%s'", _spreadsheet.title)


        try:
            worksheet = _spreadsheet.worksheet(title)
        except gspread.WorksheetNotFound:
            worksheet = _spreadsheet.add_worksheet(title=title, rows=1000, cols=len(SHEET_HEADERS))
            logger.info("Created new worksheet tab '%s'", title)

        # Ensure headers exist on row 1
        first_row = worksheet.row_values(1)
        if not first_row:
            worksheet.append_row(SHEET_HEADERS, value_input_option="USER_ENTERED")
            logger.info("Initialized header row on worksheet '%s'", title)

        return worksheet
    except Exception as e:
        logger.error("Error accessing Google Sheets: %s", e)
        _gc = None
        _spreadsheet = None
        return None



def _format_entry_row(entry: dict) -> list[Any]:
    """Convert an entry dictionary into a row list for Google Sheets."""
    def _to_bullet(val: Any) -> str:
        if isinstance(val, str):
            try:
                val = json.loads(val)
            except Exception:
                return val
        if isinstance(val, list):
            return "\n".join(f"• {item}" for item in val)
        return str(val) if val else ""

    def _to_tags(val: Any) -> str:
        if isinstance(val, str):
            try:
                val = json.loads(val)
            except Exception:
                return val
        if isinstance(val, list):
            return ", ".join(val)
        return str(val) if val else ""

    return [
        entry.get("id", ""),
        entry.get("created_at", ""),
        entry.get("category", ""),
        entry.get("title", ""),
        entry.get("summary", ""),
        entry.get("mood", ""),
        entry.get("energy_level", ""),
        _to_bullet(entry.get("key_points")),
        _to_bullet(entry.get("action_items")),
        _to_tags(entry.get("tags")),
        entry.get("language", ""),
        entry.get("raw_transcript") or entry.get("clean_transcript", ""),
        entry.get("duration_seconds", ""),
    ]


def _sync_single_row_sync(entry: dict) -> bool:
    worksheet = _get_worksheet()
    if not worksheet:
        return False
    row = _format_entry_row(entry)
    worksheet.append_row(row, value_input_option="USER_ENTERED")
    logger.info("Appended note #%s to Google Sheets", entry.get("id"))
    return True


def _sync_batch_rows_sync(entries: list[dict]) -> int:
    worksheet = _get_worksheet()
    if not worksheet or not entries:
        return 0

    rows = [_format_entry_row(e) for e in entries]
    worksheet.append_rows(rows, value_input_option="USER_ENTERED")
    logger.info("Appended %d notes to Google Sheets in batch", len(rows))
    return len(rows)


async def sync_note_to_sheets(entry: dict) -> bool:
    """Asynchronously append a single thought note to Google Sheets."""
    if not is_sheets_configured():
        return False
    try:
        return await asyncio.to_thread(_sync_single_row_sync, entry)
    except Exception as e:
        logger.error("Failed to sync note to Google Sheets: %s", e)
        return False


async def sync_all_notes_to_sheets(entries: list[dict]) -> int:
    """Asynchronously append multiple thought notes to Google Sheets."""
    if not is_sheets_configured():
        return 0
    try:
        return await asyncio.to_thread(_sync_batch_rows_sync, entries)
    except Exception as e:
        logger.error("Failed to sync batch notes to Google Sheets: %s", e)
        return 0
