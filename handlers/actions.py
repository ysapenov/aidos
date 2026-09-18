"""
handlers/actions.py — Action items / tasks management extracted from voice journal.

Provides:
- /actions         -> List pending action items with inline toggle buttons
- /actions all     -> List all action items (including completed)
- /actions clear   -> Remove completed action items
- Callbacks for toggling task state, switching filters, and clearing done items.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.decorators import restricted, send_typing
from utils.constants import (
    ACTIONS_EMPTY,
    EMOJI_SUCCESS,
    EMOJI_ERROR,
    EMOJI_CHECK,
)
from utils.formatting import format_action_items_list
from database.models import (
    get_action_items,
    toggle_action_item,
    clear_completed_action_items,
)

logger = logging.getLogger(__name__)


def _build_action_keyboard(items: list[dict], show_completed: bool = False) -> InlineKeyboardMarkup:
    """Build inline keyboard for action items with toggle buttons."""
    keyboard = []

    # Add toggle buttons for active or displayed items (up to 10 for clean UI)
    row = []
    for item in items[:10]:
        item_id = item["id"]
        is_done = bool(item.get("is_completed"))
        btn_text = f"↩ #{item_id}" if is_done else f"✓ #{item_id}"
        row.append(InlineKeyboardButton(btn_text, callback_data=f"act_toggle_{item_id}_{int(show_completed)}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    # Filter toggle & clear done buttons
    control_row = []
    if show_completed:
        control_row.append(InlineKeyboardButton("📋 Show Pending Only", callback_data="act_view_pending"))
    else:
        control_row.append(InlineKeyboardButton("📋 Show All", callback_data="act_view_all"))
    control_row.append(InlineKeyboardButton("🧹 Clear Done", callback_data="act_clear_done"))

    keyboard.append(control_row)
    return InlineKeyboardMarkup(keyboard)


@restricted
@send_typing
async def actions_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /actions command."""
    user = update.effective_user
    args = context.args or []

    # Subcommand: /actions clear
    if args and args[0].lower() == "clear":
        cleared_count = await clear_completed_action_items(user.id)
        await update.effective_message.reply_text(
            f"{EMOJI_SUCCESS} Cleared <b>{cleared_count}</b> completed action item(s).",
            parse_mode="HTML",
        )
        return

    # Subcommand: /actions all
    show_all = bool(args and args[0].lower() == "all")

    items = await get_action_items(user.id, include_completed=show_all)
    if not items:
        await update.effective_message.reply_text(ACTIONS_EMPTY, parse_mode="HTML")
        return

    text = format_action_items_list(items, show_completed=show_all)
    reply_markup = _build_action_keyboard(items, show_completed=show_all)
    await update.effective_message.reply_text(text, parse_mode="HTML", reply_markup=reply_markup)


async def actions_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline button clicks for action items."""
    query = update.callback_query
    if not query:
        return

    await query.answer()
    data = query.data
    user = update.effective_user

    if data.startswith("act_toggle_"):
        # Format: act_toggle_<item_id>_<show_completed>
        parts = data.split("_")
        item_id = int(parts[2])
        show_completed = bool(int(parts[3])) if len(parts) > 3 else False

        await toggle_action_item(item_id, user.id)

        items = await get_action_items(user.id, include_completed=show_completed)
        if not items:
            await query.edit_message_text(ACTIONS_EMPTY, parse_mode="HTML")
            return

        text = format_action_items_list(items, show_completed=show_completed)
        reply_markup = _build_action_keyboard(items, show_completed=show_completed)
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=reply_markup)
        return

    if data == "act_view_all":
        items = await get_action_items(user.id, include_completed=True)
        if not items:
            await query.edit_message_text(ACTIONS_EMPTY, parse_mode="HTML")
            return
        text = format_action_items_list(items, show_completed=True)
        reply_markup = _build_action_keyboard(items, show_completed=True)
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=reply_markup)
        return

    if data == "act_view_pending":
        items = await get_action_items(user.id, include_completed=False)
        if not items:
            await query.edit_message_text(ACTIONS_EMPTY, parse_mode="HTML")
            return
        text = format_action_items_list(items, show_completed=False)
        reply_markup = _build_action_keyboard(items, show_completed=False)
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=reply_markup)
        return

    if data == "act_clear_done":
        cleared_count = await clear_completed_action_items(user.id)
        items = await get_action_items(user.id, include_completed=False)
        if not items:
            await query.edit_message_text(
                f"{EMOJI_SUCCESS} Cleared {cleared_count} item(s).\n\n{ACTIONS_EMPTY}",
                parse_mode="HTML",
            )
            return

        text = (
            f"{EMOJI_SUCCESS} Cleared <b>{cleared_count}</b> completed item(s).\n\n"
            + format_action_items_list(items, show_completed=False)
        )
        reply_markup = _build_action_keyboard(items, show_completed=False)
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=reply_markup)
        return
