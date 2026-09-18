import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from handlers.core import start, help_command, menu
from utils.constants import WELCOME_MESSAGE, HELP_MESSAGE

@pytest.mark.asyncio
@patch('utils.decorators.is_user_allowed', new_callable=AsyncMock, return_value=True)
@patch('handlers.core.upsert_user', new_callable=AsyncMock)
async def test_start_command(mock_upsert_user, mock_is_user_allowed):
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
@patch('handlers.core.is_subscribed', new_callable=AsyncMock, return_value=False)
@patch('utils.decorators.is_user_allowed', new_callable=AsyncMock, return_value=True)
async def test_menu_command(mock_is_user_allowed, mock_is_subscribed):
    update = MagicMock()
    update.effective_message.reply_text = AsyncMock()
    context = MagicMock()
    
    await menu(update, context)
    
    update.effective_message.reply_text.assert_called_once()


def test_html_constants_validity():
    """Ensure bot message constants do not contain unescaped angle brackets or invalid tags."""
    import re
    from utils.constants import NOTES_EMPTY, ACTIONS_EMPTY
    
    allowed_tag_pattern = re.compile(r"</?(?:b|i|u|s|code|pre|a|blockquote)[^>]*>")
    
    for msg_template in [WELCOME_MESSAGE.format(name="Test"), HELP_MESSAGE, NOTES_EMPTY, ACTIONS_EMPTY]:
        cleaned = allowed_tag_pattern.sub("", msg_template)
        # Verify no unescaped < or > remain (which cause Telegram BadRequest entity errors)
        assert "<" not in cleaned, f"Unescaped '<' found in: {cleaned}"
        # Also ensure & is either part of an entity or safe
        raw_ampersands = re.findall(r"&(?!(?:lt|gt|amp|quot);)", cleaned)
        assert not raw_ampersands, f"Unescaped '&' found in: {cleaned}"

