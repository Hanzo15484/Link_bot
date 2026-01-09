from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import asyncio
import subprocess
import sys
import os
from datetime import datetime, timedelta
import logging

from config import OWNER_ID, GITHUB_REPO
from database.operations import UserOperations
from utils.helpers import is_owner

logger = logging.getLogger(__name__)

async def auth_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Authorize a user with temporary access."""
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("Usage: /auth <user_id> <days>")
        return
    
    try:
        user_id = int(context.args[0])
        days = int(context.args[1])
        
        if days < 1 or days > 365:
            await update.message.reply_text("Days must be between 1 and 365.")
            return
        
        success = UserOperations.authorize_user(user_id, days, update.effective_user.id)
        
        if success:
            expiry_date = datetime.utcnow() + timedelta(days=days)
            await update.message.reply_text(
                f"User {user_id} authorized for {days} days until {expiry_date.strftime('%Y-%m-%d %H:%M:%S UTC')}"
            )
        else:
            await update.message.reply_text(f"User {user_id} not found.")
        
    except ValueError:
        await update.message.reply_text("Invalid user ID or days format. Please use numbers.")

async def deauth_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Deauthorize a user."""
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /deauth <user_id>")
        return
    
    try:
        user_id = int(context.args[0])
        
        success = UserOperations.deauthorize_user(user_id)
        
        if success:
            await update.message.reply_text(f"User {user_id} deauthorized.")
        else:
            await update.message.reply_text(f"User {user_id} not found.")
            
    except ValueError:
        await update.message.reply_text("Invalid user ID format. Please use a number.")

async def promote_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Promote a user to admin."""
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /promote <user_id>")
        return
    
    try:
        user_id = int(context.args[0])
        
        if user_id == OWNER_ID:
            await update.message.reply_text("User is already the owner.")
            return
        
        success = UserOperations.promote_to_admin(user_id)
        
        if success:
            await update.message.reply_text(f"User {user_id} promoted to admin.")
        else:
            await update.message.reply_text(f"User {user_id} not found.")
            
    except ValueError:
        await update.message.reply_text("Invalid user ID format. Please use a number.")

async def demote_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Demote a user from admin."""
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /demote <user_id>")
        return
    
    try:
        user_id = int(context.args[0])
        
        if user_id == OWNER_ID:
            await update.message.reply_text("Cannot demote the owner.")
            return
        
        success = UserOperations.demote_admin(user_id)
        
        if success:
            await update.message.reply_text(f"User {user_id} demoted from admin.")
        else:
            await update.message.reply_text(f"User {user_id} not found or not an admin.")
            
    except ValueError:
        await update.message.reply_text("Invalid user ID format. Please use a number.")

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ban a user from using the bot."""
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /ban <user_id>")
        return
    
    try:
        user_id = int(context.args[0])
        
        if user_id == OWNER_ID:
            await update.message.reply_text("Cannot ban the owner.")
            return
        
        success = UserOperations.ban_user(user_id)
        
        if success:
            await update.message.reply_text(f"User {user_id} banned from using the bot.")
        else:
            await update.message.reply_text(f"User {user_id} not found.")
            
    except ValueError:
        await update.message.reply_text("Invalid user ID format. Please use a number.")

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unban a user."""
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /unban <user_id>")
        return
    
    try:
        user_id = int(context.args[0])
        
        success = UserOperations.unban_user(user_id)
        
        if success:
            await update.message.reply_text(f"User {user_id} unbanned.")
        else:
            await update.message.reply_text(f"User {user_id} is not banned.")
            
    except ValueError:
        await update.message.reply_text("Invalid user ID format. Please use a number.")

async def restart_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Restart the bot."""
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    status_msg = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="ʀᴇꜱᴛᴀʀᴛɪɴɢ ʙᴏᴛ..."
    )
    await asyncio.sleep(2)

    await status_msg.edit_text("ʙᴏᴛ ʀᴇꜱᴛᴀʀᴛᴇᴅ ✅")
    await asyncio.sleep(3)
    
    # Restart
    os.execl(sys.executable, sys.executable, *sys.argv)

async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast a message to all users."""
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    
    message_text = " ".join(context.args)
    users = UserOperations.get_all_users()
    
    success_count = 0
    fail_count = 0
    
    for user in users:
        try:
            await context.bot.send_message(user['user_id'], f"{message_text}")
            success_count += 1
            await asyncio.sleep(0.05)  # Rate limiting
        except Exception as e:
            logger.error(f"Failed to send broadcast to {user['user_id']}: {e}")
            fail_count += 1
    
    await update.message.reply_text(
        f"Broadcast completed.\nSuccess: {success_count}\nFailed: {fail_count}"
    )

async def update_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update the bot from GitHub."""
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    status_msg = await context.bot.send_message(
          chat_id=update.effective_chat.id,
          text="𖡡 ᴩᴜʟʟɪɴɢ ʟᴀᴛᴇꜱᴛ ᴜᴩᴅᴀᴛᴇ ꜰʀᴏᴍ ɢɪᴛʜᴜʙ..."
      )
    
    try:
        # Pull latest changes from GitHub
        result = subprocess.run(["git", "pull"], capture_output=True, text=True)
        
        if result.returncode == 0:
            changes = result.stdout.strip()
            if not changes or "Already up to date" in changes:
                await status_msg.edit_text("✅ ʙᴏᴛ ɪꜱ ᴀʟʀᴇᴀᴅy ᴜᴩ ᴛᴏ ᴅᴀᴛᴇ!")
                return
            
            await status_msg.edit_text(f"✅ ᴜᴩᴅᴀᴛᴇᴅ ꜰʀᴏᴍ ɢɪᴛʜᴜʙ!\n\nChanges:\n{changes}")
            await asyncio.sleep(2)
            
            await status_msg.edit_text("♻️ ʀᴇꜱᴛᴀʀᴛɪɴɢ....")
            await asyncio.sleep(2)
            
            await status_msg.edit_text("✦ ʀᴇꜱᴛᴀʀᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟy!")
            await asyncio.sleep(3)
            
            # Restart the bot
            os.execl(sys.executable, sys.executable, *sys.argv)
        else:
            await status_msg.edit_text(f"❌ ꜰᴀɪʟᴇᴅ ᴛᴏ ᴜᴩᴅᴀᴛᴇ: {result.stderr}")
            
    except Exception as e:
        await status_msg.edit_text(f"❌ ᴇʀʀᴏʀ ᴜᴩᴅᴀᴛɪɴɢ: {str(e)}")

async def channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get database files."""
    from config import OWNER_ID
    
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    keyboard = [
        [
            InlineKeyboardButton("📂 Channels", callback_data="get_channels"),
            InlineKeyboardButton("⚙️ Bot Settings", callback_data="get_settings"),
        ],
        [     
            InlineKeyboardButton("❌ Close", callback_data="close_channels")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Choose the file you want:", reply_markup=reply_markup)
