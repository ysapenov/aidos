import pytest
import pytest_asyncio
from unittest.mock import patch
from database.db import init_db
from database.models import (
    add_journal_entry,
    get_journal_entries,
    get_journal_entry_by_id,
    delete_journal_entry,
    get_all_journal_entries,
    upsert_user,
)
from config import settings


@pytest_asyncio.fixture
async def temp_db(tmp_path):
    db_path = tmp_path / "test_journal.db"
    with patch.object(settings, "database_path", str(db_path)):
        await init_db()
        yield


@pytest.mark.asyncio
async def test_journal_crud(temp_db):
    user_id = 12345
    await upsert_user(user_id, "testuser", "Tester")

    # 1. Add journal entries
    entry_id_1 = await add_journal_entry(
        user_id=user_id,
        title="First Thought",
        category="Ideas",
        summary="A great idea about AI.",
        key_points=["Point A", "Point B"],
        action_items=["Task 1"],
        raw_transcript="This is my raw voice note.",
        tags=["ai", "ideas"],
        language="en",
        duration_seconds=30,
        telegram_file_id="tg_file_abc",
    )
    assert entry_id_1 > 0

    entry_id_2 = await add_journal_entry(
        user_id=user_id,
        title="Work Meeting",
        category="Work",
        summary="Review sprint backlog.",
        key_points=["Point 1"],
        action_items=["Follow up"],
        raw_transcript="Meeting summary note.",
        tags=["work"],
        language="ru",
        duration_seconds=55,
        telegram_file_id="tg_file_def",
    )
    assert entry_id_2 > entry_id_1

    # 2. Get entries (all and filtered)
    all_recent = await get_journal_entries(user_id, limit=10)
    assert len(all_recent) == 2
    assert all_recent[0]["title"] == "Work Meeting"  # DESC order

    work_only = await get_journal_entries(user_id, category="Work")
    assert len(work_only) == 1
    assert work_only[0]["title"] == "Work Meeting"

    # 3. Get entry by ID
    single = await get_journal_entry_by_id(entry_id_1, user_id)
    assert single is not None
    assert single["title"] == "First Thought"
    assert single["category"] == "Ideas"

    # Non-existent or other user
    assert await get_journal_entry_by_id(9999, user_id) is None
    assert await get_journal_entry_by_id(entry_id_1, 99999) is None

    # 4. Get all entries for export
    all_export = await get_all_journal_entries(user_id)
    assert len(all_export) == 2
    assert all_export[0]["title"] == "First Thought"  # ASC order for export

    # 5. Delete entry
    deleted = await delete_journal_entry(entry_id_1, user_id)
    assert deleted is True
    assert await get_journal_entry_by_id(entry_id_1, user_id) is None

    # Deleting again returns False
    assert await delete_journal_entry(entry_id_1, user_id) is False
