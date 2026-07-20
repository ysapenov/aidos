import pytest
import os
from unittest.mock import patch
from database.db import init_db
from database.models import upsert_user, is_user_allowed, add_allowed_user
from config import settings

@pytest.fixture
async def temp_db(tmp_path):
    db_path = tmp_path / "test.db"
    with patch.object(settings, "database_path", str(db_path)):
        await init_db()
        yield

@pytest.mark.asyncio
async def test_upsert_and_allow_user(temp_db):
    # Ensure it's not in static list
    with patch.object(settings, "allowed_user_ids", set()):
        await upsert_user(999, "testuser", "Test")
        assert not await is_user_allowed(999)
        
        await add_allowed_user(999, "testuser", "Test")
        assert await is_user_allowed(999)
