from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import asyncio
import aiohttp
import logging

from config import MAINTENANCE_MODE, OWNER_ID, SAFE_COMMANDS, GITHUB_REPO
from database.operations import UserOperations

logger = logging.getLogger(__name__)

AWAITING_CUSTOM_ALERT = False
BROADCAST_CANCELLED = False

async def maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maintenance command."""
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("🚫 Only the bot owner can use this command.")
        return

    keyboard = [
        [
            InlineKeyboardButton("On ✅" if MAINTENANCE_MODE else "On ❌", callback_data="maint_on"),
            InlineKeyboardButton("Off ✅" if not MAINTENANCE_MODE else "Off ❌", callback_data="maint_off"),
        ],
        [InlineKeyboardButton("Close ❌", callback_data="maint_close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("⚙️ Maintenance Mode Control:", reply_markup=reply_markup)

async def maintenance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maintenance button callback."""
    global MAINTENANCE_MODE
    query = update.callback_query
    user_id = query.from_user.id

    if user_id != OWNER_ID:
        await query.answer("🚫 You are not authorized!", show_alert=True)
        return

    if query.data == "maint_on":
        MAINTENANCE_MODE = True
    elif query.data == "maint_off":
        MAINTENANCE_MODE = False
        await query.delete_message()
        keyboard = [
            [
                InlineKeyboardButton("Yes ✅", callback_data="alert_yes"),
                InlineKeyboardButton("No ❌", callback_data="alert_no")
            ]
        ]
        await query.message.reply_text(
            "📢 Do you want to alert the users?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    elif query.data == "maint_close":
        await query.delete_message()
        await query.answer("❌ Closed")
        return

    keyboard = [
        [
            InlineKeyboardButton("On ✅" if MAINTENANCE_MODE else "On ❌", callback_data="maint_on"),
            InlineKeyboardButton("Off ✅" if not MAINTENANCE_MODE else "Off ❌", callback_data="maint_off"),
        ],
        [InlineKeyboardButton("Close ❌", callback_data="maint_close")]
    ]
    await query.edit_message_text("⚙️ Maintenance Mode Control:", reply_markup=InlineKeyboardMarkup(keyboard))
    await query.answer("Updated successfully ✅")

async def get_latest_commit_message():
    """Fetch latest commit message from GitHub."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/commits"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                latest_commit = data[0]
                return latest_commit["commit"]["message"]
            else:
                return "No recent changes found."

async def broadcast_to_users_with_progress(context: ContextTypes.DEFAULT_TYPE, text: str, message_obj):
    """Broadcast message to all users with progress."""
    global BROADCAST_CANCELLED
    BROADCAST_CANCELLED = False

    users = UserOperations.get_all_users()
    total_users = len(users)
    success_count = 0
    failed_count = 0

    keyboard = [[InlineKeyboardButton("Cancel ❌", callback_data="broadcast_cancel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    for idx, user in enumerate(users, start=1):
        if BROADCAST_CANCELLED:
            await message_obj.edit_text("❌ Broadcasting cancelled by owner.")
            return

        try:
            await context.bot.send_message(chat_id=user['user_id'], text=text)
            success_count += 1
        except Exception:
            failed_count += 1

        remaining_count = total_users - idx
        percent = int((idx / total_users) * 100)
        bar_length = 20
        filled_length = int(bar_length * percent // 100)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)

        status_text = (
            f"📢 Broadcasting message...\n\n"
            f"{bar} {percent}%\n"
            f"✅ Success: {success_count}\n"
            f"❌ Failed: {failed_count}\n"
            f"⏳ Remaining: {remaining_count}\n"
        )

        await message_obj.edit_text(status_text, reply_markup=reply_markup)
        await asyncio.sleep(0.05)

    await message_obj.edit_text(
        f"✅ Broadcasting completed!\n"
        f"✅ Success: {success_count}\n"
        f"❌ Failed: {failed_count}\n"
        f"Total users: {total_users}"
    )

async def broadcast_cancel_callback(update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast cancel callback."""
    global BROADCAST_CANCELLED
    query = update.callback_query
    if query.from_user.id != OWNER_ID:
        await query.answer("🚫 You are not authorized!", show_alert=True)
        return

    BROADCAST_CANCELLED = True
    await query.answer("❌ Broadcasting cancelled")
    await query.delete_message()

async def alert_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Alert callback."""
    global AWAITING_CUSTOM_ALERT
    query = update.callback_query

    if query.from_user.id != OWNER_ID:
        await query.answer("🚫 You are not authorized!", show_alert=True)
        return

    if query.data == "alert_yes":
        keyboard = [
            [
                InlineKeyboardButton("Custom ✍️", callback_data="alert_custom"),
                InlineKeyboardButton("Default 📢", callback_data="alert_default"),
            ]
        ]
        await query.edit_message_text(
            "📢 Do you want to send a custom alert or default alert?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif query.data == "alert_no":
        await query.edit_message_text("❌ No alert will be sent.")
    elif query.data == "alert_default":
        commit_message = await get_latest_commit_message()
        final_text = f"✅ The bot is now up, you can use it now\n\n📌 Changes: {commit_message}"
        status_msg = await context.bot.send_message(
            chat_id=OWNER_ID,
            text="Starting broadcasting..."
        )
        await broadcast_to_users_with_progress(context, final_text, status_msg)
    elif query.data == "alert_custom":
        AWAITING_CUSTOM_ALERT = True
        await query.edit_message_text("✍️ Send the custom alert message now.")

async def custom_alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle custom alert message."""
    global AWAITING_CUSTOM_ALERT
    if not AWAITING_CUSTOM_ALERT or update.effective_user.id != OWNER_ID:
        return

    AWAITING_CUSTOM_ALERT = False
    custom_text = update.message.text
    status_msg = await update.message.reply_text("Starting broadcasting...")
    await broadcast_to_users_with_progress(context, custom_text, status_msg)

async def maintenance_guard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maintenance guard for commands."""
    global MAINTENANCE_MODE
    if not update.message:
        return

    if MAINTENANCE_MODE and update.effective_user.id != OWNER_ID:
        text = update.message.text or ""
        if text.startswith("/"):
            command = text.split()[0].replace("/", "").lower()
            if command not in SAFE_COMMANDS:
                await update.message.reply_text("⚠️ Bot is under maintenance. Please try again later.")
                return
