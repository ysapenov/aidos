import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from database.db import init_db
from database.models import (
    upsert_user,
    add_action_items,
    get_action_items,
    toggle_action_item,
    delete_action_item,
    clear_completed_action_items,
)
from handlers.actions import actions_command, actions_callback
from config import settings


@pytest_asyncio.fixture
async def temp_db(tmp_path):
    db_path = tmp_path / "test_actions.db"
    with patch.object(settings, "database_path", str(db_path)):
        await init_db()
        yield


@pytest.fixture(autouse=True)
def allow_test_users():
    with patch.object(settings, "allowed_user_ids", {99901, 99902, 99903}):
        yield



@pytest.mark.asyncio
async def test_action_items_db_crud(temp_db):
    user_id = 99901
    await upsert_user(user_id, "tester", "Tester")

    # 1. Add action items
    ids = await add_action_items(user_id, ["Buy groceries", "Send report", "Call client"])
    assert len(ids) == 3

    # 2. Get pending items
    pending = await get_action_items(user_id, include_completed=False)
    assert len(pending) == 3
    assert pending[0]["task_text"] in ["Buy groceries", "Send report", "Call client"]

    # 3. Toggle first item to completed
    item_id = ids[0]
    new_state = await toggle_action_item(item_id, user_id)
    assert new_state is True

    # Now pending should be 2, all should be 3
    pending_now = await get_action_items(user_id, include_completed=False)
    assert len(pending_now) == 2
    all_now = await get_action_items(user_id, include_completed=True)
    assert len(all_now) == 3

    # Toggle back to uncompleted
    toggled_back = await toggle_action_item(item_id, user_id)
    assert toggled_back is False
    assert len(await get_action_items(user_id, include_completed=False)) == 3

    # Toggle to completed again and clear
    await toggle_action_item(item_id, user_id)
    cleared = await clear_completed_action_items(user_id)
    assert cleared == 1
    assert len(await get_action_items(user_id, include_completed=True)) == 2

    # Delete single item
    del_ok = await delete_action_item(ids[1], user_id)
    assert del_ok is True
    assert len(await get_action_items(user_id, include_completed=True)) == 1


@pytest.mark.asyncio
async def test_actions_command_flow(temp_db):
    user_id = 99902
    await upsert_user(user_id, "tester2", "Tester2")
    await add_action_items(user_id, ["Finish unit tests"])

    update = MagicMock()
    update.effective_user.id = user_id
    update.effective_message.reply_text = AsyncMock()
    context = MagicMock()
    context.args = []
    context.bot.send_chat_action = AsyncMock()

    with patch("handlers.actions.restricted", lambda f: f):
        await actions_command(update, context)

    update.effective_message.reply_text.assert_called_once()
    call_args = update.effective_message.reply_text.call_args
    assert "Finish unit tests" in call_args[0][0]
    assert call_args[1]["reply_markup"] is not None


@pytest.mark.asyncio
async def test_actions_callback_toggle(temp_db):
    user_id = 99903
    await upsert_user(user_id, "tester3", "Tester3")
    ids = await add_action_items(user_id, ["Prepare slides"])

    update = MagicMock()
    update.effective_user.id = user_id
    update.callback_query.data = f"act_toggle_{ids[0]}_0"
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    context = MagicMock()

    await actions_callback(update, context)

    update.callback_query.answer.assert_called_once()
    update.callback_query.edit_message_text.assert_called_once()
    # Should show empty because it was toggled to completed and filter is show_completed=False
    call_text = update.callback_query.edit_message_text.call_args[0][0]
    assert "No pending action items" in call_text
