import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from utils.decorators import restricted
from utils.constants import ACCESS_DENIED

@pytest.mark.asyncio
async def test_restricted_decorator_denied():
    # Setup mock update and context
    update = MagicMock()
    update.effective_user.id = 123
    update.effective_user.username = "baduser"
    update.effective_message.reply_text = AsyncMock()
    
    context = MagicMock()
    
    # Dummy handler
    handler_called = False
    async def dummy_handler(u, c):
        nonlocal handler_called
        handler_called = True
    
    decorated_handler = restricted(dummy_handler)
    
    with patch("utils.decorators.is_user_allowed", new_callable=AsyncMock) as mock_is_allowed:
        mock_is_allowed.return_value = False
        
        await decorated_handler(update, context)
        
        assert not handler_called
        update.effective_message.reply_text.assert_called_once_with(ACCESS_DENIED, parse_mode="HTML")

@pytest.mark.asyncio
async def test_restricted_decorator_allowed():
    update = MagicMock()
    update.effective_user.id = 999
    
    context = MagicMock()
    
    handler_called = False
    async def dummy_handler(u, c):
        nonlocal handler_called
        handler_called = True
    
    decorated_handler = restricted(dummy_handler)
    
    with patch("utils.decorators.is_user_allowed", new_callable=AsyncMock) as mock_is_allowed:
        mock_is_allowed.return_value = True
        
        await decorated_handler(update, context)
        
        assert handler_called
