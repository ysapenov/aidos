import pytest
import os
from unittest.mock import patch
from config import Settings

def test_settings_validation():
    with patch.dict(os.environ, {
        "TELEGRAM_BOT_TOKEN": "123:test",
        "GEMINI_API_KEY": "test_key",
        "ALLOWED_USER_IDS": "111,222",
        "ADMIN_USER_IDS": "111",
        "DATABASE_PATH": "data/test.db",
        "GEMINI_MODEL": "test-model",
        "HISTORY_CAP": "50"
    }, clear=True):
        settings = Settings()
        assert settings.telegram_bot_token == "123:test"
        assert settings.gemini_api_key == "test_key"
        assert settings.allowed_user_ids == {111, 222}
        assert settings.admin_user_ids == {111}
        assert settings.database_path == "data/test.db"
        assert settings.gemini_model == "test-model"
        assert settings.history_cap == 50

def test_settings_missing_token():
    with patch.dict(os.environ, {}, clear=True):
        settings = Settings()
        with pytest.raises(ValueError):
            settings.validate()
