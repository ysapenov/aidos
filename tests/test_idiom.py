import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.idiom_service import format_idiom_response
from handlers.idiom import (
    broadcast_daily_idiom,
    send_daily_idiom,
    test_idiom as run_test_idiom,
    send_idiom as run_send_idiom,
)


def test_format_idiom_response():

    data = {
        "idiom": "Break the ice",
        "literal_meaning": "Break frozen water.",
        "actual_meaning": "Start a conversation.",
        "russian_equivalent": "Растопить лёд",
        "kazakh_equivalent": "Мұзды бұзу",
        "example": "Break the ice.",
        "used_when": "People meet for the first time.",
        "similar_idioms": ["Get the ball rolling"],
    }

    result = format_idiom_response(data)

    assert "🎯 <b>Daily Idiom</b>" in result
    assert "<b>Break the ice</b>" in result
    assert "Meaning: <b>Start a conversation.</b>" in result
    assert "🇰🇿 Kazakh: Мұзды бұзу" in result
    assert "• Get the ball rolling" in result


def test_format_idiom_response_string_similar():
    data = {
        "idiom": "Hit the sack",
        "literal_meaning": "Hit a bag.",
        "actual_meaning": "Go to sleep.",
        "similar_idioms": "Hit the hay, Turn in",
    }

    result = format_idiom_response(data)
    assert "<b>Hit the sack</b>" in result
    assert "• Hit the hay" in result
    assert "• Turn in" in result


def test_format_idiom_response_empty_and_missing_fields():
    data = {
        "idiom": "Bite the bullet",
    }
    result = format_idiom_response(data)
    assert "<b>Bite the bullet</b>" in result
    assert "🎯 <b>Daily Idiom</b>" in result


@pytest.mark.asyncio
@patch("handlers.idiom.get_subscribed_user_ids", new_callable=AsyncMock, return_value=[111, 222])
@patch("handlers.idiom.save_idiom", new_callable=AsyncMock)
@patch("handlers.idiom.generate_idiom", new_callable=AsyncMock, return_value={"idiom": "Piece of cake", "actual_meaning": "Very easy"})
@patch("handlers.idiom.get_sent_idioms", new_callable=AsyncMock, return_value=["Break the ice"])
async def test_broadcast_daily_idiom(mock_get_sent, mock_generate, mock_save, mock_get_subs):
    bot = MagicMock()
    bot.send_message = AsyncMock()

    success_count, total_subs, text = await broadcast_daily_idiom(bot)

    assert success_count == 2
    assert total_subs == 2
    assert "Piece of cake" in text
    assert bot.send_message.call_count == 2
    mock_save.assert_called_once()


@pytest.mark.asyncio
@patch("handlers.idiom.broadcast_daily_idiom", new_callable=AsyncMock, side_effect=RuntimeError("API timeout"))
@patch("handlers.idiom.settings")
async def test_send_daily_idiom_alerts_admin_on_failure(mock_settings, mock_broadcast):
    mock_settings.admin_user_ids = {999}
    context = MagicMock()
    context.bot.send_message = AsyncMock()

    await send_daily_idiom(context)

    context.bot.send_message.assert_called_once()
    call_kwargs = context.bot.send_message.call_args[1]
    assert call_kwargs["chat_id"] == 999
    assert "[Aidos Alert]" in call_kwargs["text"]
    assert "API timeout" in call_kwargs["text"]


@pytest.mark.asyncio
@patch("utils.decorators.settings")
@patch("handlers.idiom.generate_idiom", new_callable=AsyncMock, return_value={"idiom": "Under the weather"})
@patch("handlers.idiom.get_sent_idioms", new_callable=AsyncMock, return_value=[])
async def test_test_idiom_admin_command(mock_get_sent, mock_generate, mock_settings):
    mock_settings.admin_user_ids = {999}
    update = MagicMock()
    update.effective_user.id = 999
    status_msg = MagicMock()
    status_msg.edit_text = AsyncMock()
    update.effective_message.reply_text = AsyncMock(return_value=status_msg)
    context = MagicMock()

    await run_test_idiom(update, context)

    update.effective_message.reply_text.assert_called_once()
    status_msg.edit_text.assert_called_once()
    assert "[Admin Preview — Not Broadcasted]" in status_msg.edit_text.call_args[0][0]
    assert "Under the weather" in status_msg.edit_text.call_args[0][0]


@pytest.mark.asyncio
@patch("utils.decorators.settings")
@patch("handlers.idiom.broadcast_daily_idiom", new_callable=AsyncMock, return_value=(2, 2, "response"))
@patch("handlers.idiom.get_subscribed_user_ids", new_callable=AsyncMock, return_value=[111, 222])
async def test_send_idiom_admin_command(mock_get_subs, mock_broadcast, mock_settings):
    mock_settings.admin_user_ids = {999}
    update = MagicMock()
    update.effective_user.id = 999
    status_msg = MagicMock()
    status_msg.edit_text = AsyncMock()
    update.effective_message.reply_text = AsyncMock(return_value=status_msg)
    context = MagicMock()

    await run_send_idiom(update, context)

    update.effective_message.reply_text.assert_called_once()
    status_msg.edit_text.assert_called_once()
    assert "Daily idiom broadcast complete!" in status_msg.edit_text.call_args[0][0]
