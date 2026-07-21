import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from handlers.core import start, help_command, menu
from utils.constants import WELCOME_MESSAGE, HELP_MESSAGE

@pytest.mark.asyncio
@patch('utils.decorators.is_user_allowed', new_callable=AsyncMock, return_value=True)
async def test_start_command(mock_is_user_allowed):
    update = MagicMock()
    update.effective_user.first_name = "User"
    update.effective_message.reply_text = AsyncMock()
    context = MagicMock()
    
    await start(update, context)
    
    update.effective_message.reply_text.assert_called_once()
    args, kwargs = update.effective_message.reply_text.call_args
    assert "User" in args[0]
    assert kwargs.get("parse_mode") == "HTML"

@pytest.mark.asyncio
@patch('utils.decorators.is_user_allowed', new_callable=AsyncMock, return_value=True)
async def test_help_command(mock_is_user_allowed):
    update = MagicMock()
    update.effective_message.reply_text = AsyncMock()
    context = MagicMock()
    
    await help_command(update, context)
    
    update.effective_message.reply_text.assert_called_once()
    args, kwargs = update.effective_message.reply_text.call_args
    assert args[0] == HELP_MESSAGE
    assert kwargs.get("parse_mode") == "HTML"

@pytest.mark.asyncio
@patch('utils.decorators.is_user_allowed', new_callable=AsyncMock, return_value=True)
async def test_menu_command(mock_is_user_allowed):
    update = MagicMock()
    update.effective_message.reply_text = AsyncMock()
    context = MagicMock()
    
    await menu(update, context)
    
    update.effective_message.reply_text.assert_called_once()
