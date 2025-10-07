import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes,
    ConversationHandler, MessageHandler, filters
)
from datetime import datetime, timedelta
import re
import asyncio
import aiosqlite
import base64
import time
import traceback
import json
import os
import sys
import subprocess
import requests
from io import BytesIO
import aiofiles
from telegram.constants import ChatType
from dotenv import load_dotenv
import aiohttp
import psutil
import platform

load_dotenv("Bot_Token.env")  # Load variables from .env
BOT_TOKEN = os.getenv("BOT_TOKEN")
# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.ERROR,  # Reduce log verbosity
    handlers=[logging.FileHandler('bot.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Configuration
OWNER_ID = 5373577888
ADMIN_IDS = [5373577888, 6170814776, 6959143950]
LINK_DURATION = 5 * 60  # 5 minutes in seconds
MESSAGE_CLEANUP_TIME = 3 * 60  # 6 minutes in seconds
MAINTENANCE_MODE = False
SAFE_COMMANDS = ["start", "help", "id"]
AWAITING_CUSTOM_ALERT = False
BROADCAST_CANCELLED = False
GITHUB_REPO = "Hanzo15484/link_bot.py"

# JSON storage file
JSON_STORAGE = "channel_data.json"
SETTINGS_STORAGE = "bot_settings.json"
#Log 
LOG_FILE = "bot.log"

#Cache 
BOT_CACHE = {}
# Conversation states
(
    ABOUT, HELP_REQUIREMENTS, HELP_HOW, HELP_TROUBLESHOOT,
    SETTINGS_MAIN, SETTINGS_START, SETTINGS_START_TEXT, SETTINGS_START_IMAGE,
    SETTINGS_START_BUTTONS, SETTINGS_START_ADD_BUTTON, SETTINGS_START_REMOVE_BUTTON,
    SETTINGS_HELP, SETTINGS_HELP_TEXT, SETTINGS_HELP_IMAGE,
    SETTINGS_HELP_BUTTONS, SETTINGS_HELP_ADD_BUTTON, SETTINGS_HELP_REMOVE_BUTTON
) = range(17)

# Pagination
LIST_CHANNELS_PAGE_SIZE = 10

#Search Range
SEARCH_CHANNEL = range(1)
 #small caps
async def smallcaps_handler(update, context):
    if update.effective_chat.type != "private":
       return
    text = update.message.text or ""
    
    # skip commands or if user is in search flow
    if text.startswith("/") or context.user_data.get('skip_smallcaps'):
        return

    transformed = to_small_caps(text)

    # send bot reply and store the message object
    bot_msg = await update.message.reply_text(transformed)

    # wait 2 seconds
    await asyncio.sleep(2)

    # try deleting bot's message
    try:
        await bot_msg.delete()
    except Exception as e:
        print("Failed to delete message:", e)

# small-caps message handler
def to_small_caps(text: str) -> str:
    small_caps_map = {
        "a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ", "e": "ᴇ", "f": "ғ", "g": "ɢ",
        "h": "ʜ", "i": "ɪ", "j": "ᴊ", "k": "ᴋ", "l": "ʟ", "m": "ᴍ", "n": "ɴ",
        "o": "ᴏ", "p": "ᴘ", "q": "ǫ", "r": "ʀ", "s": "s", "t": "ᴛ", "u": "ᴜ",
        "v": "ᴠ", "w": "ᴡ", "x": "x", "y": "ʏ", "z": "ᴢ"
    }
    return "".join(small_caps_map.get(ch.lower(), ch) for ch in text)
    
def start(update, context):
    try:
        # delete the user's /start message
        context.bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)
    except:
        pass

        
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:  # skip non-message updates
        return
         # Restrict to private chat only
    if update.message.chat.type != ChatType.PRIVATE:
        return  # ignore messages from groups/channels
    user_text = update.message.text or ""
    formatted_text = to_small_caps(user_text)
    await update.message.reply_text(formatted_text)

async def load_settings(filename='settings.json'):
    try:
        async with aiofiles.open(filename, 'r') as f:
            content = await f.read()
            settings = json.loads(content)
        return settings
    except FileNotFoundError:
        # Return default settings if file does not exist
        return {}
    except Exception as e:
        print(f"Error loading settings: {e}")
        return {}
# Utility Functions
def is_admin(user_id):
    """Check if user is an admin."""
    return user_id in ADMIN_IDS

def is_owner(user_id):
    """Check if user is the owner."""
    return user_id == OWNER_ID
#temporary start message 
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        # React ❤️ to user's command
    try:
        await update.message.set_reaction("❤️")
    except Exception:
        pass  # ignore if reaction not supported

    # Step 1: Send initial "starting"
    msg = await update.message.reply_text("sᴛᴀʀᴛɪɴɢ ᴛʜᴇ ʙᴏᴛ....")

    # Step 2: Countdown edits
    for i in range(3, 0, -1):
        await asyncio.sleep(1)
        await msg.edit_text(f"sᴛᴀʀᴛɪɴɢ ᴛʜᴇ ʙᴏᴛ ɪɴ {i} sᴇᴄᴏɴᴅs....")

    # Step 3: Show "Bot started"
    await asyncio.sleep(1)
    await msg.edit_text("✅ ʙᴏᴛ sᴛᴀʀᴛᴇᴅ")

    # Step 4: Delete the startup animation message
    await asyncio.sleep(1)
    try:
        await msg.delete()
    except Exception:
        pass
#load data
async def load_data():
    """Load data from JSON file asynchronously with cache."""
    global BOT_CACHE
    if BOT_CACHE:  # Return cached version if already loaded
        return BOT_CACHE

    if os.path.exists(JSON_STORAGE):
        try:
            async with aiofiles.open(JSON_STORAGE, 'r', encoding='utf-8') as f:
                content = await f.read()
                data = json.loads(content)
                # Ensure required keys exist
                if "admins" not in data:
                    data["admins"] = ADMIN_IDS.copy()
                if "banned_users" not in data:
                    data["banned_users"] = []
                if "users" not in data:
                    data["users"] = {}
                BOT_CACHE = data
                return data
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            BOT_CACHE = {"channels": {}, "links": {}, "users": {}, "admins": ADMIN_IDS.copy(), "banned_users": []}
            return BOT_CACHE
    BOT_CACHE = {"channels": {}, "links": {}, "users": {}, "admins": ADMIN_IDS.copy(), "banned_users": []}
    return BOT_CACHE

async def save_data(data):
    """Save data to JSON file asynchronously and update cache."""
    global BOT_CACHE
    BOT_CACHE = data
    try:
        async with aiofiles.open(JSON_STORAGE, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        logger.error(f"Error saving data: {e}")
        return {           
                 "start": {
                    "text": """✦ ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ ᴀᴅᴠᴀɴᴄᴇᴅ ʟɪɴᴋs sʜᴀʀɪɴɢ ʙᴏᴛ
• ᴡɪᴛʜ ᴛʜɪs ʙᴏᴛ, ʏᴏᴜ ᴄᴀɴ sᴀғᴇʟʏ sʜᴀʀᴇ ʟɪɴᴋs ᴀɴᴅ ᴋᴇᴇᴘ ʏᴏᴜʀ ᴄʜᴀɴɴᴇʟs ᴘʀᴏᴛᴇᴄᴛᴇᴅ ғʀᴏᴍ ᴄᴏᴘʏʀɪɢʜᴛ ɪssᴜᴇs.
✦ ғᴇᴀᴛᴜʀᴇs:
• ғᴀsᴛ ᴀɴᴅ ᴇᴀsʏ ʟɪɴᴋ ᴘʀᴏᴄᴇssɪɴɢ
• ᴘᴇʀᴍᴀɴᴇɴᴛ ʟɪɴᴋs ᴡɪᴛʜ ᴛᴇᴍᴘᴏʀᴀʀʏ ᴀᴄᴄᴇss ғᴏʀ sᴀғᴇᴛʏ
• ᴘʀɪᴠᴀᴛᴇ, sᴇᴄᴜʀᴇ, ᴀɴᴅ ғᴜʟʟʏ ᴘʀᴏᴛᴇᴄᴛᴇᴅ ᴄᴏɴᴛᴇɴᴛ
✦ ᴇɴᴊᴏʏ ᴀ sᴍᴀʀᴛᴇʀ, sᴀғᴇʀ, ᴀɴᴅ ᴍᴏʀᴇ ᴘᴏᴡᴇʀғᴜʟ ᴡᴀʀ ᴛᴏ sʜᴀʀᴇ ʟɪɴᴋs!""",
                    "image": "/data/data/com.termux/files/home/storage/downloads/start_img.jpg",
                    "buttons": [
                        [{"text": "ᴀʙᴏᴜᴛ", "url": "callback:about"}],
                        [{"text": "ᴄʟᴏsᴇ", "url": "callback:close"}]
                    ]
                },
              "help": {
                    "text": """✦ ʙᴏᴛ ʜᴇʟᴘ ɢᴜɪᴅᴇ

┌─ ᴜsᴇʀ ᴄᴏᴍᴍᴀɴᴅs ─┐
• /start – sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ ᴀɴᴅ ᴠɪᴇᴡ ᴡᴇʟᴄᴏᴍᴇ ᴍᴇssᴀɢᴇ  
• /help – sʜᴏᴡ ᴛʜɪs ʜᴇʟᴘ ɢᴜɪᴅᴇ   
• /id – ɢᴇᴛ ʏᴏᴜʀ ɪᴅ
• /settings - ᴄᴏɴꜰɪɢᴜʀᴇ ʙᴏᴛ ꜱᴇᴛᴛɪɴɢꜱ

┌─ ᴀᴅᴍɪɴ ᴄᴏᴍᴍᴀɴᴅs ─┐
• /gen_link <channel_link/id> – ɢᴇɴᴇʀᴀᴛᴇ ᴀ ᴘᴇʀᴝᴀɴᴇɴᴛ ʙᴏᴛ ʟɪɴᴋ ᴡɪᴛʜ ᴀ 5-ᴍɪɴᴜᴛᴇ ᴛᴇᴍᴘᴏʀᴀʀʏ ɪɴᴠɪᴛᴇ  
• /batch_link – ɢᴇɴᴇʀᴀᴛᴇ ʟɪɴᴋs ꜰᴏʀ ᴀʟʟ ᴄʜᴀɴɴᴇʟs ᴡʜᴇʀᴇ ᴛʜᴇ ʙᴏᴛ ɪs ᴀɴ ᴀᴅᴍɪɴ 
• /debug <channel_link/id> – ᴄʜᴇᴄᴋ ᴀɴᴅ ᴅᴇʙᴜɢ ᴄʜᴀɴɴᴇʟ ᴘᴇʀᴍɪssɪᴏɴs
• /list_channels – ʟɪsᴛ ᴀʟʟ ᴀᴄᴛɪᴠᴇ ᴄʜᴀɴɴᴇʟs ᴄᴏɴɴᴇᴄᴛᴇᴅ ᴛᴏ ᴛʜᴇ ʙᴏᴛ  
• /troubleshoot – ᴅɪᴀɢɴᴏsᴇ ᴀɴᴅ ꜰɪx ᴄᴏᴍᴍᴏɴ ɪssᴜᴇs ᴡɪᴛʜ ᴛʜᴇ ʙᴏᴛ  
• /admins - ʟɪꜱᴛ ᴀʟʟ ʙᴏᴛ ᴀᴅᴍɪɴꜱ
• /users - ꜱʜᴏᴡ ᴜꜱᴇʀ ꜱᴛᴀᴛꜱ

┌─ ᴏᴡɴᴇʀ ᴄᴏᴍᴍᴀɴᴅs ─┐
• /auth – ᴀᴜᴛʜᴏʀɪᴢᴇ ᴀ ᴜsᴇʀ ᴡɪᴛʜ ᴛᴇᴍᴘᴏʀᴀʀʏ ᴀᴄᴄᴇss ᴛᴏ ʟɪᴍɪᴛᴇᴅ ᴄᴏᴍᴍᴀɴᴅs  
• /deauth – ʀᴇᴍᴏᴠᴇ ᴀᴜᴛʜᴏʀɪᴢᴀᴛɪᴏɴ ꜰʀᴏᴍ ᴀ ᴜsᴇʀ  
• /promote – ᴘʀᴏᴍᴏᴛᴇ ᴀ ᴜsᴇʀ ᴛᴏ ᴀᴅᴍɪɴ ᴡɪᴛʜ ꜰᴜʟʟ ʙᴏᴛ ᴀᴄᴄᴇss (ᴇxᴄᴇᴘᴛ ᴏᴡɴᴇʀ-ᴏɴʟʏ ᴄᴏᴍᴍᴀɴᴅs)  
• /demote – ʀᴇᴠᴏᴋᴇ ᴀᴅᴍɪɴ ʀɪɢʜᴛs ꜰʀᴏᴍ ᴀ ᴜsᴇʀ  
• /ban – ʙᴀɴ ᴀ ᴜsᴇʀ ꜰʀᴏᴍ ᴜsɪɴɢ ᴛʜᴇ ʙᴏᴛ  
• /unban – ᴜɴʙᴀɴ ᴀ ᴜsᴇʀ  
• /restart – ʀᴇsᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ  
• /broadcast – sᴇɴᴅ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ᴀʟʟ ᴜsᴇʀs  
• /update - ᴜᴘᴅᴀᴛᴇ ʙᴏᴛ ꜰʀᴏᴍ ɢɪᴛʜᴜʙ""",
                    "image": "/data/data/com.termux/files/home/storage/downloads/start_img.jpg",
                    "buttons": [
                        [
                            {"text": "ʀᴇǫᴜɪʀᴇᴍᴇɴᴛs", "url": "callback:help_requirements"},
                            {"text": "ʜᴏᴡ ɪᴛs ᴡᴏʀᴋ?", "url": "callback:help_how"}
                        ],
                        [
                            {"text": "ᴛʀᴏᴜʙʟᴇsʜᴏᴏᴛ", "url": "callback:help_troubleshoot"}
                        ],
                        [
                            {"text": "ʙᴀᴄᴋ", "url": "callback:back_start"},
                            {"text": "ᴄʟᴏsᴇ", "url": "callback:close"}
                        ]
                    ]
                }
  }
    return {
        "start": {
            "text": """✦ ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ ᴀᴅᴠᴀɴᴄᴇᴅ ʟɪɴᴋs sʜᴀʀɪɴɢ ʙᴏᴛ
• ᴡɪᴛʜ ᴛʜɪs ʙᴏᴛ, ʏᴏᴜ ᴄᴀɴ sᴀғᴇʟʏ sʜᴀʀᴇ ʟɪɴᴋs ᴀɴᴅ ᴋᴇᴇᴘ ʏᴏᴜʀ ᴄʜᴀɴɴᴇʟs ᴘʀᴏᴛᴇᴄᴛᴇᴅ ғʀᴏᴍ ᴄᴏᴘʏʀɪɢʜᴛ ɪssᴜᴇs.

✦ ғᴇᴀᴛᴜʀᴇs:
• ғᴀsᴛ ᴀɴᴅ ᴇᴀsʏ ʟɪɴᴋ ᴘʀᴏᴄᴇssɪɴɢ
• ᴘᴇʀᴍᴀɴᴇɴᴛ ʟɪɴᴋs ᴡɪᴛʜ ᴛᴇᴍᴘᴏʀᴀʀʏ ᴀᴄᴄᴇss ғᴏʀ sᴀғᴇᴛʏ
• ᴘʀɪᴠᴀᴛᴇ, sᴇᴄᴜʀᴇ, ᴀɴᴅ ғᴜʟʟʏ ᴘʀᴏᴛᴇᴄᴛᴇᴅ ᴄᴏɴᴛᴇɴᴛ
✦ ᴇɴᴊᴏʏ ᴀ sᴍᴀʀᴛᴇʀ, sᴀғᴇʀ, ᴀɴᴅ ᴍᴏʀᴇ ᴘᴏᴡᴇʀғᴜʟ ᴡᴀʏ ᴛᴏ sʜᴀʀᴇ ʟɪɴᴋs!""",
            "image": "/data/data/com.termux/files/home/storage/downloads/start_img.jpg",
            "buttons": [
                [{"text": "ᴀʙᴏᴜᴛ", "url": "callback:about"}],
                [{"text": "ᴄʟᴏsᴇ", "url": "callback:close"}]
            ]
        },
        "help": {
            "text": """✦ ʙᴏᴛ ʜᴇʟᴘ ɢᴜɪᴅᴇ

┌─ ᴜsᴇʀ ᴄᴏᴍᴍᴀɴᴅs ─┐
• /start – sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ ᴀɴᴅ ᴠɪᴇᴡ ᴡᴇʟᴄᴏᴍᴇ ᴍᴇssᴀɢᴇ  
• /help – sʜᴏᴡ ᴛʜɪs ʜᴇʟᴘ ɢᴜɪᴅᴇ   
• /id – ɢᴇᴛ ʏᴏᴜʀ ɪᴅ
• /settings - ᴄᴏɴꜰɪɢᴜʀᴇ ʙᴏ�t ꜱᴇᴛᴛɪɴɢꜱ

┌─ ᴀᴅᴍɪɴ ᴄᴏᴍᴍᴀɴᴅs ─┐
• /gen_link <channel_link/id> – ɢᴇɴᴇʀᴀᴛᴇ ᴀ ᴘᴇʀᴍᴀɴᴇɴᴛ ʙᴏᴛ ʟɪɴᴋ ᴡɪᴛʜ ᴀ 5-ᴍɪɴᴜᴛᴇ ᴛᴇᴍᴘᴏʀᴀʀʏ ɪɴᴠɪᴛᴇ  
• /batch_link – ɢᴇɴᴇʀᴀᴛᴇ ʟɪɴᴋs ꜰᴏʀ ᴀʟʟ ᴄʜᴀɴɴᴇʟs ᴡʜᴇʀᴇ ᴛʜᴇ ʙᴏᴛ ɪs ᴀɴ ᴀᴅᴍɪɴ 
• /debug <channel_link/id> – ᴄʜᴇᴄᴋ ᴀɴᴅ ᴅᴇʙᴜɢ ᴄʜᴀɴɴᴇʟ ᴘᴇʀᴍɪssɪᴏɴs
• /list_channels – ʟɪsᴛ ᴀʟʟ ᴀᴄᴛɪᴠᴇ ᴄʜᴀɴɴᴇʟs ᴄᴏɴɴᴇᴄᴛᴇᴅ ᴛᴏ ᴛʜᴇ ʙᴏᴛ  
• /troubleshoot – ᴅɪᴀɢɴᴏsᴇ ᴀɴᴅ ꜰɪx ᴄᴏᴍᴍᴏɴ ɪssᴜᴇs ᴡɪᴛʜ ᴛʜᴇ ʙᴏᴛ  
• /admins - ʟɪꜱᴛ ᴀʟʟ ʙᴏᴛ ᴀᴅᴍɪɴꜱ
• /users - ꜱʜᴏᴡ ᴜꜱᴇʀ ꜱᴛᴀᴛꜱ

┌─ ᴏᴡɴᴇʀ ᴄᴏᴍᴍᴀɴᴅs ─┐
• /auth – ᴀᴜᴛʜᴏʀɪᴢᴇ ᴀ ᴜsᴇʀ ᴡɪᴛʜ ᴛᴇᴜᴘᴏʀᴀʀʏ ᴀᴄᴄᴇss ᴛᴏ ʟɪᴍɪᴛᴇᴅ ᴄᴏᴍᴍᴀɴᴅs  
• /deauth – ʀᴇᴍᴏᴠᴇ ᴀᴜᴛʜᴏʀɪᴢᴀᴛɪᴏɴ ꜰʀᴏᴍ ᴀ ᴜsᴇʀ  
• /promote – ᴘʀᴏᴍᴏᴛᴇ ᴀ ᴜsᴇʀ ᴛᴏ ᴀᴅᴍɪɴ ᴡɪᴛʜ ꜰᴜʟʟ ʙᴏᴛ ᴀᴄᴄᴇss (ᴇxᴄᴇᴘᴛ ᴏᴡɴᴇʀ-ᴏɴʟʏ ᴄᴏᴍᴍᴀɴᴅs)  
• /demote – ʀᴇᴠᴏᴋᴇ ᴀᴅᴍɪɴ ʀɪɢʜᴛs ꜰʀᴏᴍ ᴀ ᴜsᴇʀ  
• /ban – ʙᴀɴ ᴀ ᴜsᴇʀ ꜰʀᴏᴍ ᴜsɪɴɢ ᴛʜᴇ ʙᴏᴛ  
• /unban – ᴜɴʙᴀɴ ᴀ ᴜsᴇʀ  
• /restart – ʀᴇsᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ  
• /broadcast – sᴇɴᴅ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ᴀʟʟ ᴜsᴇʀs  
• /update - ᴜᴘᴅᴀᴛᴇ ʙᴏᴛ ꜰʀᴏᴍ ɢɪᴛʜᴜʙ
• /settings - ᴄᴏɴꜰɪɢᴜʀᴇ ʙᴏt ꜱᴇᴛᴛɪɴɢꜱ""",
            "image": "photo_2025-08-31_23-16-44.jpg",
            "buttons": [
                [
                    {"text": "ʀᴇǫᴜɪʀᴇᴍᴇɴᴛs", "url": "callback:help_requirements"},
                    {"text": "ʜᴏᴡ ɪᴛs ᴡᴏʀᴋ?", "url": "callback:help_how"}
                ],
                [
                    {"text": "ᴛʀᴏᴜʙʟᴇsʜᴏᴏᴛ", "url": "callback:help_troubleshoot"}
                ],
                [
                    {"text": "ʙᴀᴄᴋ", "url": "callback:back_start"},
                    {"text": "ᴄʟᴏsᴇ", "url": "callback:close"}
                ]
            ]
        }
    }

async def save_settings(settings):
    """Save settings to JSON file asynchronously."""
    try:
        async with aiofiles.open(SETTINGS_STORAGE, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(settings, indent=2, ensure_ascii=False))
    except Exception as e:
        logger.error(f"Error saving settings: {e}")

async def cleanup_message(context, chat_id, message_id):
    """Clean up message after timeout."""
    await asyncio.sleep(MESSAGE_CLEANUP_TIME)
    try:
        await context.bot.delete_message(chat_id, message_id)
        logger.info(f"Message {message_id} cleaned up")
    except Exception as e:
        logger.error(f"Error deleting message: {e}")

async def extract_channel_info(context, input_str):
    """Extract channel info from input and verify bot is admin."""
    try:
        chat = None
        logger.info(f"Extracting channel info from: {input_str}")
        
        # Clean the input
        cleaned_input = input_str.strip()
        
        # Try different input formats
        formats_to_try = []
        
        # If it's a numeric ID (starts with -100)
        if cleaned_input.startswith('-100') and cleaned_input[1:].isdigit():
            formats_to_try.append(cleaned_input)
        
        # If it's a username (with or without @)
        elif cleaned_input.replace('@', '').replace('-', '').isalnum():
            if not cleaned_input.startswith('@'):
                formats_to_try.append(f"@{cleaned_input}")
            formats_to_try.append(cleaned_input)
        
        # If it's a URL
        elif 't.me/' in cleaned_input:
            # Extract from t.me URL
            if 't.me/+' in cleaned_input:  # Private invite link
                match = re.search(r't\.me/\+(.+)', cleaned_input)
                if match:
                    formats_to_try.append(f"+{match.group(1)}")
            else:  # Public channel
                match = re.search(r't\.me/([a-zA-Z0-9_]+)', cleaned_input)
                if match:
                    username = match.group(1)
                    formats_to_try.append(f"@{username}")
        
        # Also try the raw input
        formats_to_try.append(cleaned_input)
        
        logger.info(f"Trying formats: {formats_to_try}")
        
        for format_to_try in formats_to_try:
            try:
                chat = await context.bot.get_chat(format_to_try)
                logger.info(f"Successfully got chat: {chat.title} ({chat.id})")
                break
            except Exception as e:
                logger.info(f"Failed with format '{format_to_try}': {e}")
                continue
        
        if not chat:
            logger.error("All format attempts failed")
            return None
            
        # Verify bot is admin with proper permissions
        try:
            admins = await context.bot.get_chat_administrators(chat.id)
            bot_id = (await context.bot.get_me()).id
            
            bot_admin = next((admin for admin in admins if admin.user.id == bot_id), None)
            
            if not bot_admin:
                logger.error(f"❌ Bot is NOT admin in {chat.title}")
                return None
            
            # Check permissions - handle different permission attribute formats
            can_invite = False
            if hasattr(bot_admin, 'can_invite_users'):
                can_invite = bot_admin.can_invite_users
            elif hasattr(bot_admin, 'permissions') and hasattr(bot_admin.permissions, 'can_invite_users'):
                can_invite = bot_admin.permissions.can_invite_users
            elif hasattr(bot_admin, 'can_invite_users'):
                can_invite = bot_admin.can_invite_users
            
            if not can_invite:
                logger.error(f"❌ Bot cannot create invite links in {chat.title}")
                # Try to create a link anyway to see what error we get
                try:
                    test_link = await context.bot.create_chat_invite_link(
                        chat_id=chat.id,
                        expire_date=datetime.utcnow() + timedelta(minutes=5),
                        creates_join_request=False
                    )
                    logger.info(f"✅ Actually can create links despite permission check")
                    can_invite = True
                except Exception as test_error:
                    logger.error(f"❌ Confirmed cannot create links: {test_error}")
                    return None
                
            logger.info(f"✅ Bot verified as admin with invite permissions in {chat.title}")
            return str(chat.id), chat.title, chat
            
        except Exception as e:
            logger.error(f"Error checking admin status: {e}")
            # Try direct link creation as fallback
            try:
                test_link = await context.bot.create_chat_invite_link(
                    chat_id=chat.id,
                    expire_date=datetime.utcnow() + timedelta(seconds=60),
                    creates_join_request=False
                )
                logger.info(f"✅ Can create links directly")
                return str(chat.id), chat.title, chat
            except Exception as test_error:
                logger.error(f"❌ Cannot create links: {test_error}")
                return None
            
    except Exception as e:
        logger.error(f"Error in extract_channel_info: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None

async def generate_single_link(update, context, channel_input):
    """Generate a link for a single channel."""
    status_msg = await update.message.reply_text("Processing...")
    
    try:
        # Extract channel info from the input
        channel_info = await extract_channel_info(context, channel_input)
        if not channel_info:
            await status_msg.edit_text("Invalid channel link or bot is not admin in this channel.\n\nPlease check:\n• Channel link format\n• Bot is admin with invite permissions\n\nTry: /debug @channelname to check permissions")
            return
        
        channel_id, channel_name, chat = channel_info
        
        # Create a permanent file_id for this channel
        unique_string = f"{channel_id}_permanent"
        file_id = base64.urlsafe_b64encode(unique_string.encode()).decode('utf-8').replace('=', '')
        
        # Create a 5-minute invite link (using UTC time)
        expiry_date = datetime.utcnow() + timedelta(seconds=LINK_DURATION)
        
        try:
            invite_link = await context.bot.create_chat_invite_link(
                chat_id=chat.id,
                expire_date=expiry_date,
                creates_join_request=False
            )
            logger.info(f"Created 5-minute invite link expiring at: {expiry_date}")
        except Exception as e:
            logger.error(f"Error creating invite link: {e}")
            await status_msg.edit_text(f"Error creating invite link: {str(e)}")
            return
        
        # Store the link information in JSON
        data = await load_data()
        
        # Store channel info
        if channel_id not in data["channels"]:
            data["channels"][channel_id] = {
                "name": channel_name,
                "file_id": file_id,
                "created_at": datetime.utcnow().isoformat()
            }
        
        # Store link info
        data["links"][file_id] = {
            "channel_id": channel_id,
            "invite_link": invite_link.invite_link,
            "expiry_time": expiry_date.isoformat(),
            "is_active": True,
            "created_at": datetime.utcnow().isoformat()
        }
        
        await save_data(data)
        
        # Generate the bot link (this will be permanent)
        bot_username = (await context.bot.get_me()).username
        bot_link = f"https://t.me/{bot_username}?start={file_id}"
        
        await status_msg.edit_text(
            f"✅ Generated PERMANENT link for '{channel_name}':\n{bot_link}\n\n"
            f"• Channel ID: {chat.id}\n"
            f"• Current invite: {invite_link.invite_link}\n"
            f"• This invite expires in: 5 minutes\n"
            f"• The bot link above is PERMANENT and will always work"
        )
        
        # Schedule link regeneration
        asyncio.create_task(regenerate_channel_link(context, channel_id, channel_name, file_id))
        
    except Exception as e:
        logger.error(f"Error generating link: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        await status_msg.edit_text(f"❌ Failed to generate link.\nError: {str(e)}\n\nUse /debug @channelname to check permissions.")

async def regenerate_channel_link(context, channel_id, channel_name, file_id):
    """Regenerate channel link before it expires."""
    await asyncio.sleep(LINK_DURATION - 60)  # Regenerate 1 minute before expiry
    
    try:
        # Create a new 5-minute invite link
        expiry_date = datetime.utcnow() + timedelta(seconds=LINK_DURATION)
        invite_link = await context.bot.create_chat_invite_link(
            chat_id=channel_id,
            expire_date=expiry_date,
            creates_join_request=False
        )
        
        # Update JSON data
        data = await load_data()
        
        if file_id in data["links"]:
            # Revoke old invite link
            try:
                old_invite = data["links"][file_id]["invite_link"]
                await context.bot.revoke_chat_invite_link(channel_id, old_invite)
                logger.info(f"Revoked old invite link for {channel_name}")
            except Exception as e:
                logger.warning(f"Could not revoke old invite link: {e}")
            
            # Update with new link
            data["links"][file_id] = {
                "channel_id": channel_id,
                "invite_link": invite_link.invite_link,
                "expiry_time": expiry_date.isoformat(),
                "is_active": True,
                "created_at": datetime.utcnow().isoformat()
            }
            
            await save_data(data)
            logger.info(f"✅ Auto-regenerated link for {channel_name}")
            
            # Schedule next regeneration
            asyncio.create_task(regenerate_channel_link(context, channel_id, channel_name, file_id))
                
    except Exception as e:
        logger.error(f"Error regenerating link for {channel_id}: {e}")

async def get_active_link(file_id):
    """Get active link for a file_id, regenerating if expired."""
    data = await load_data()
    
    if file_id not in data["links"]:
        return None
    
    link_data = data["links"][file_id]
    
    # Check if link is expired
    expiry_time = datetime.fromisoformat(link_data["expiry_time"])
    if datetime.utcnow() > expiry_time:
        # Link expired, need to regenerate
        channel_id = link_data["channel_id"]
        channel_name = data["channels"][channel_id]["name"]
        
        # Create new invite link
        new_expiry = datetime.utcnow() + timedelta(seconds=LINK_DURATION)
        try:
            # This would need the bot context to create a new link
            # For now, we'll return the expired link and the regeneration will happen async
            return None
        except:
            return None
    
    return link_data

async def update_link_message(context, chat_id, message_id, new_invite_link, channel_name):
    """Update an existing message with a new invite link."""
    try:
        keyboard = [
            [InlineKeyboardButton("• ᴄʟɪᴄᴋ ʜᴇʀᴇ ᴛᴏ ᴊᴏɪɴ ɴᴏᴡ •", url=new_invite_link)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"ᴊᴏɪɴ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ '{channel_name}' ʙy ᴄʟɪᴄᴋɪɴɢ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ:",
            reply_markup=reply_markup
        )
        logger.info(f"Updated message {message_id} with new invite link")
    except Exception as e:
        logger.error(f"Error updating message: {e}")

# Button Handlers
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    if data == "about":
        # Show about message
        about_text = "✦ ᴅᴇᴠᴇʟᴏᴘᴇʀ - [ʜᴀɴᴢᴏ](t.me/quarel7)"
        keyboard = [
            [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="back_start"),
            InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=about_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return ABOUT
        
    elif data == "help_requirements":
        # Show requirements
        requirements_text = """✦ ʀᴇǫᴜɪʀᴇᴍᴇɴᴛs:
• ʙᴏᴛ ᴍᴜsᴛ ʙᴇ ᴀᴅᴍɪɴ ɪɴ ᴛᴀʀɢᴇᴛ ᴄʜᴀɴɴᴇʟs
• ʙᴏᴛ ɴᴇᴇᴅs ᴘᴇʀᴍɪssɪᴏɴ ᴛᴏ ᴄʀᴇᴀᴛᴇ ɪɴᴠɪᴛᴇ ʟɪɴᴋs"""
        
        keyboard = [
            [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="back_help"),
            InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=requirements_text,
            reply_markup=reply_markup
        )
        return HELP_REQUIREMENTS
        
    elif data == "help_how":
        # Show how it works
        how_text = """✦ ʜᴏᴡ ɪᴛ ᴡᴏʀᴋs:

1. ʙᴏᴛ ɢᴇɴᴇʀᴀᴛᴇs ᴀ ᴘᴇʀᴍᴀɴᴇɴᴛ ʟɪɴᴋ ʟɪᴋᴇ: https://t.me/YourBot?start=base64_code

2. ᴛʜɪs ᴘᴇʀᴍᴀɴᴇɴᴛ ʟɪɴᴋ ᴘᴏɪɴᴛs ᴛᴏ ᴀ ᴛᴇᴍᴘᴏʀᴀʀʏ ᴄʜᴀɴɴᴇʟ ɪɴᴠɪᴛᴇ ᴛʜᴀᴛ ᴇxᴘɪʀᴇs ɪɴ 5 ᴍɪɴᴜᴛᴇs

3. ᴀғᴛᴇʀ ᴇxᴘɪʀᴀᴛɪᴏɴ, ᴛʜᴇ ʙᴏᴛ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴄʀᴇᴀᴛᴇs ᴀ ɴᴇᴡ ᴄʜᴀɴɴᴇʟ ɪɴᴠɪᴛᴇ

4. ᴛʜᴇ ʙᴏᴛ ʟɪɴᴋ ʀᴇᴍᴀɪɴs ᴛʜᴇ sᴀᴍᴇ ʙᴜᴛ ᴘᴏɪɴᴛs ᴛᴏ ᴛʜᴇ ɴᴇᴡ ᴄʜᴀɴɴᴇʟ ɪɴᴠɪᴛᴇ"""
        
        keyboard = [
            [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="back_help"),
            InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=how_text,
            reply_markup=reply_markup
        )
        return HELP_HOW
        
    elif data == "help_troubleshoot":
        # Show troubleshoot
        troubleshoot_text = """✦ ᴛʀᴏᴜʙʟᴇsʜᴏᴏᴛ

1\\. ɪғ ʙᴏᴛ ɪs ɴᴏᴛ ᴡᴏʀᴋɪɴɢ, ᴇɴsᴜʀᴇ ɪᴛ ɪs ᴀᴅᴍɪɴ ɪɴ ᴛᴀʀɢᴇᴛ ᴄʜᴀɴɴᴇʟs\\.    
2\\. ᴠᴇʀɪғʏ ʙᴏᴛ ʜᴀs ᴘᴇʀᴍɪssɪᴏɴ ᴛᴏ ᴄʀᴇᴀᴛᴇ ɪɴᴠɪᴛᴇ ʟɪɴᴋs\\.  
3\\. ᴜsᴇ ᴄʜᴀɴɴᴇʟ ɪᴅ ɪɴsᴛᴇᴀᴅ ᴏғ ᴄʜᴀɴɴᴇʟ ʟɪɴᴋ\\.  
4\\. ᴄʜᴇᴄᴋ ɪɴᴛᴇʀɴᴇᴛ ᴄᴏɴɴᴇᴄᴛɪᴏɴ ɪғ ʙᴏᴛ ғᴀɪʟs ᴛᴏ ʀᴇsᴘᴏɴᴅ\\.  
5\\. ᴜsᴇ /debug \\<channel\\_link/id\\> ᴛᴏ ᴄʜᴇᴄᴋ ᴘᴇʀᴍɪssɪᴏɴ ɪssᴜᴇs\\.  

ғᴏʀ ғᴜʀᴛʜᴇʀ ᴀssɪsᴛᴀɴᴄᴇ\\, ᴄᴏɴᴛᴀᴄᴛ [ᴏᴡɴᴇʀ](https://t.me/Quarel7)\\."""
        
        keyboard = [
            [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="back_help"),
            InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=troubleshoot_text,
            reply_markup=reply_markup,
            parse_mode="MarkdownV2"
        )
        return HELP_TROUBLESHOOT
        
    elif data == "back_start":
        # Go back to start
        await start_callback(update, context)
        return ConversationHandler.END
        
    elif data == "back_help":
        # Go back to help
        await help_command_callback(update, context)
        return ConversationHandler.END
        
    elif data == "close":
        # Delete the message
        await query.delete_message()
        return ConversationHandler.END
    
    # Settings navigation
    elif data == "settings_main":
        await settings_command_callback(update, context)
        return SETTINGS_MAIN
        
    elif data == "settings_start":
        await settings_start_callback(update, context)
        return SETTINGS_START
        
    elif data == "settings_start_text":
        context.user_data['settings_mode'] = 'start_text'
        await query.edit_message_text(
            text="Send the text you want to add or replace.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Back", callback_data="settings_start"),
                    InlineKeyboardButton("Close", callback_data="close")
                ]
            ])
        )
        return SETTINGS_START_TEXT
        
    elif data == "settings_start_image":
        context.user_data['settings_mode'] = 'start_image'
        await query.edit_message_text(
            text="Send the image you want to add or replace.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Back", callback_data="settings_start"),
                    InlineKeyboardButton("Close", callback_data="close")
                ]
            ])
        )
        return SETTINGS_START_IMAGE
        
    elif data == "settings_start_buttons":
        await settings_start_buttons_callback(update, context)
        return SETTINGS_START_BUTTONS
        
    elif data == "settings_start_add_button":
        context.user_data['settings_mode'] = 'start_button'
        await query.edit_message_text(
            text="Send me new text & link for the button in format:\n\nButtonText1 - URL  \nButtonText1 - URL | ButtonText2 - URL\n\nButtons separated by | appear in the same row.\n\nExample:\nButtonText1 - URL | ButtonText2 - URL → same row\nButtonText3 - URL → new row\n\nSpecial buttons:\nBack - callback:back_start\nClose - callback:close",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Back", callback_data="settings_start_buttons"),
                    InlineKeyboardButton("Close", callback_data="close")
                ]
            ])
        )
        return SETTINGS_START_ADD_BUTTON
        
    elif data == "settings_start_remove_button":
        await settings_start_remove_button_callback(update, context)
        return SETTINGS_START_REMOVE_BUTTON
        
    elif data == "settings_help":
        await settings_help_callback(update, context)
        return SETTINGS_HELP
        
    elif data == "settings_help_text":
        context.user_data['settings_mode'] = 'help_text'
        await query.edit_message_text(
            text="Send the text you want to add or replace.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Back", callback_data="settings_help"),
                    InlineKeyboardButton("Close", callback_data="close")
                ]
            ])
        )
        return SETTINGS_HELP_TEXT
        
    elif data == "settings_help_image":
        context.user_data['settings_mode'] = 'help_image'
        await query.edit_message_text(
            text="Send the image you want to add or replace.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Back", callback_data="settings_help"),
                    InlineKeyboardButton("Close", callback_data="close")
                ]
            ])
        )
        return SETTINGS_HELP_IMAGE
        
    elif data == "settings_help_buttons":
        await settings_help_buttons_callback(update, context)
        return SETTINGS_HELP_BUTTONS
        
    elif data == "settings_help_add_button":
        context.user_data['settings_mode'] = 'help_button'
        await query.edit_message_text(
            text="Send me new text & link for the button in format above.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Back", callback_data="settings_help_buttons"),
                    InlineKeyboardButton("Close", callback_data="close")
                ]
            ])
        )
        return SETTINGS_HELP_ADD_BUTTON
        
    elif data == "settings_help_remove_button":
        await settings_help_remove_button_callback(update, context)
        return SETTINGS_HELP_REMOVE_BUTTON
        
    # Handle button removal confirmation
    elif data.startswith("remove_button_confirm_"):
        button_index = int(data.split("_")[-1])
        settings = await load_settings()
        
        # Remove the button
        row_idx = button_index // 10
        col_idx = button_index % 10
        
        if row_idx < len(settings["start"]["buttons"]):
            if col_idx < len(settings["start"]["buttons"][row_idx]):
                del settings["start"]["buttons"][row_idx][col_idx]
                
                # Remove empty rows
                settings["start"]["buttons"] = [row for row in settings["start"]["buttons"] if row]
                
                await save_settings(settings)
                await query.edit_message_text(
                    text="✅ Button removed successfully!",
                    reply_markup=InlineKeyboardMarkup([
    [
        InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="settings_start"),
        InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")
    ]
])
)
                return SETTINGS_START_BUTTONS
        
        await query.edit_message_text(
            text="❌ Error removing button.",
            reply_markup=InlineKeyboardMarkup([
    [
        InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="settings_start_buttons"),
        InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")
    ]
])
)
        return SETTINGS_START_BUTTONS
        
    elif data.startswith("remove_help_button_confirm_"):
        button_index = int(data.split("_")[-1])
        settings = await load_settings()
        
        # Remove the button
        row_idx = button_index // 10
        col_idx = button_index % 10
        
        if row_idx < len(settings["help"]["buttons"]):
            if col_idx < len(settings["help"]["buttons"][row_idx]):
                del settings["help"]["buttons"][row_idx][col_idx]
                
                # Remove empty rows
                settings["help"]["buttons"] = [row for row in settings["help"]["buttons"] if row]
                
                await save_settings(settings)
                await query.edit_message_text(
                    text="✅ Button removed successfully!",
                    reply_markup=InlineKeyboardMarkup([
    [
        InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="settings_help_buttons"),
        InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")
    ]
])
)
                return SETTINGS_HELP_BUTTONS
        
        await query.edit_message_text(
            text="❌ Error removing button.",
            reply_markup=InlineKeyboardMarkup([
    [
        InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="settings_help_buttons"),
        InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")
    ]
])
)
        return SETTINGS_HELP_BUTTONS
        
    # Handle button removal cancellation
    elif data.startswith("remove_button_cancel_"):
        await settings_start_buttons_callback(update, context)
        return SETTINGS_START_BUTTONS
        
    elif data.startswith("remove_help_button_cancel_"):
        await settings_help_buttons_callback(update, context)
        return SETTINGS_HELP_BUTTONS
    
    return ConversationHandler.END

async def start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command callback for button navigation."""
    query = update.callback_query
    if query:
        await query.answer()
        message = query.message
    else:
        message = update.message
    
    settings = await load_settings()
    start_settings = settings["start"]
    
    # Create inline keyboard from settings
    keyboard = []
    for row in start_settings["buttons"]:
        keyboard_row = []
        for button in row:
            if button["url"].startswith("callback:"):
                callback_data = button["url"].replace("callback:", "")
                keyboard_row.append(InlineKeyboardButton(button["text"], callback_data=callback_data))
            else:
                keyboard_row.append(InlineKeyboardButton(button["text"], url=button["url"]))
        keyboard.append(keyboard_row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send message with image and buttons
    if query:
        try:
            # Try to send with image first
            if os.path.exists(start_settings["image"]):
                await query.edit_message_media(
                    media=InputMediaPhoto(media=open(start_settings["image"], 'rb'), caption=start_settings["text"]),
                    reply_markup=reply_markup
                )
            else:
                await query.edit_message_text(
                    text=start_settings["text"],
                    reply_markup=reply_markup
                )
        except:
            await query.edit_message_text(
                text=start_settings["text"],
                reply_markup=reply_markup
            )
    else:
        try:
            # Try to send with image first
            if os.path.exists(start_settings["image"]):
                await message.reply_photo(
                    photo=open(start_settings["image"], 'rb'),
                    caption=start_settings["text"],
                    reply_markup=reply_markup
                )
            else:
                await message.reply_text(
                    text=start_settings["text"],
                    reply_markup=reply_markup
                )
        except:
            await message.reply_text(
                text=start_settings["text"],
                reply_markup=reply_markup
            )

async def help_command_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command callback for button navigation."""
    query = update.callback_query
    if query:
        await query.answer()
        message = query.message
    else:
        message = update.message
    
    user_id = update.effective_user.id
    settings = await load_settings()
    help_settings = settings["help"]
    
    if is_admin(user_id):
        # Create inline keyboard from settings
        keyboard = []
        for row in help_settings["buttons"]:
            keyboard_row = []
            for button in row:
                if button["url"].startswith("callback:"):
                    callback_data = button["url"].replace("callback:", "")
                    keyboard_row.append(InlineKeyboardButton(button["text"], callback_data=callback_data))
                else:
                    keyboard_row.append(InlineKeyboardButton(button["text"], url=button["url"]))
            keyboard.append(keyboard_row)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if query:
            try:
                # Try to send with image first
                if os.path.exists(help_settings["image"]):
                    await query.edit_message_media(
                        media=InputMediaPhoto(media=open(help_settings["image"], 'rb'), caption=help_settings["text"]),
                        reply_markup=reply_markup
                    )
                else:
                    await query.edit_message_text(text=help_settings["text"], reply_markup=reply_markup)
            except:
                await query.edit_message_text(text=help_settings["text"], reply_markup=reply_markup)
        else:
            try:
                # Try to send with image first
                if os.path.exists(help_settings["image"]):
                    await message.reply_photo(
                        photo=open(help_settings["image"], 'rb'),
                        caption=help_settings["text"],
                        reply_markup=reply_markup
                    )
                else:
                    await message.reply_text(text=help_settings["text"], reply_markup=reply_markup)
            except:
                await message.reply_text(text=help_settings["text"], reply_markup=reply_markup)
    else:
        # Inline keyboard for non-admins
        keyboard = [
            [InlineKeyboardButton("Contact Owner", url="https://t.me/Quarel7")],
            [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="back_start"), InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        help_text = """This bot generates permanent channel links with temporary invites for admins only.
    Contact the bot administrator for access."""
        if query:
            await query.edit_message_text(help_text, reply_markup=reply_markup)
        else:
            await message.reply_text(help_text, reply_markup=reply_markup)

# Settings command handlers
async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Settings command handler."""
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    await settings_command_callback(update, context)

async def settings_command_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Settings command callback."""
    query = update.callback_query
    if query:
        await query.answer()
        message = query.message
    else:
        message = update.message
    
    keyboard = [
        [InlineKeyboardButton("Start", callback_data="settings_start")],
        [InlineKeyboardButton("Help", callback_data="settings_help")],
        [InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = "Choose the option you want to change"

    if query:
        await query.edit_message_text(text=text, reply_markup=reply_markup)
    else:
        await message.reply_text(text=text, reply_markup=reply_markup)

    return SETTINGS_MAIN

async def settings_start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start settings callback."""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("Text", callback_data="settings_start_text")],
        [InlineKeyboardButton("Image", callback_data="settings_start_image")],
        [InlineKeyboardButton("Button", callback_data="settings_start_buttons")],
        [
            InlineKeyboardButton("Back", callback_data="settings_main"),
            InlineKeyboardButton("Close", callback_data="close")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text="Choose what you want to change",
        reply_markup=reply_markup
    )

    return SETTINGS_START

async def settings_start_buttons_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start buttons settings callback."""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("Add Button", callback_data="settings_start_add_button")],
        [InlineKeyboardButton("Remove Button", callback_data="settings_start_remove_button")],
        [
            InlineKeyboardButton("Back", callback_data="settings_start"),
            InlineKeyboardButton("Close", callback_data="close")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text="Choose the option you want to change",
        reply_markup=reply_markup
    )

    return SETTINGS_START_BUTTONS

async def settings_start_remove_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start remove button callback."""
    query = update.callback_query
    await query.answer()
    
    settings = await load_settings()
    buttons = settings["start"]["buttons"]
    
    if not buttons:
        await query.edit_message_text(
            text="No buttons to remove.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="settings_start_buttons"),
                 InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]
            ])
        )
        return SETTINGS_START_BUTTONS
    
    # Create a list of all buttons with their positions
    keyboard = []
    button_index = 0
    
    for row_idx, row in enumerate(buttons):
        keyboard_row = []
        for col_idx, button in enumerate(row):
            callback_data = f"remove_button_confirm_{row_idx * 10 + col_idx}"
            keyboard_row.append(InlineKeyboardButton(button["text"], callback_data=callback_data))
        keyboard.append(keyboard_row)
        button_index += len(row)
    
    # Add navigation buttons
    keyboard.append([
        InlineKeyboardButton("Back", callback_data="settings_start_buttons"),
        InlineKeyboardButton("Close", callback_data="close")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text="Select the button you want to remove:",
        reply_markup=reply_markup
    )
    
    return SETTINGS_START_REMOVE_BUTTON

async def settings_help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help settings callback."""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("Text", callback_data="settings_help_text")],
        [InlineKeyboardButton("Image", callback_data="settings_help_image")],
        [InlineKeyboardButton("Button", callback_data="settings_help_buttons")],
        [
            InlineKeyboardButton("Back", callback_data="settings_main"),
            InlineKeyboardButton("Close", callback_data="close")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text="Choose what you want to change",
        reply_markup=reply_markup
    )

    return SETTINGS_HELP

async def settings_help_buttons_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help buttons settings callback."""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("Add Button", callback_data="settings_help_add_button")],
        [InlineKeyboardButton("Remove Button", callback_data="settings_help_remove_button")],
        [
            InlineKeyboardButton("Back", callback_data="settings_help"),
            InlineKeyboardButton("Close", callback_data="close")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text="Choose the option you want to change",
        reply_markup=reply_markup
    )

    return SETTINGS_HELP_BUTTONS

async def settings_help_remove_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help remove button callback."""
    query = update.callback_query
    await query.answer()
    
    settings = await load_settings()
    buttons = settings["help"]["buttons"]
    
    if not buttons:
        await query.edit_message_text(
            text="No buttons to remove.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="settings_help_buttons"),
                 InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]
            ])
        )
        return SETTINGS_HELP_BUTTONS
    
    # Create a list of all buttons with their positions
    keyboard = []
    button_index = 0
    
    for row_idx, row in enumerate(buttons):
        keyboard_row = []
        for col_idx, button in enumerate(row):
            callback_data = f"remove_help_button_confirm_{row_idx * 10 + col_idx}"
            keyboard_row.append(InlineKeyboardButton(button["text"], callback_data=callback_data))
        keyboard.append(keyboard_row)
        button_index += len(row)
    
    # Add navigation buttons
    keyboard.append([
        InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="settings_help_buttons"),
        InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text="Select the button you want to remove:",
        reply_markup=reply_markup
    )
    
    return SETTINGS_HELP_REMOVE_BUTTON

async def settings_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text settings updates."""
    user_id = update.effective_user.id
    if not is_owner(user_id):
        return
    
    settings = await load_settings()
    new_text = update.message.text
    
    # Determine which setting we're updating based on conversation state
    if context.user_data.get('settings_mode') == 'start_text':
        settings["start"]["text"] = new_text
        await update.message.reply_text(
            "✅ Start text updated successfully!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="settings_start"),
                 InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]
            ])
        )
    elif context.user_data.get('settings_mode') == 'help_text':
        settings["help"]["text"] = new_text
        await update.message.reply_text(
            "✅ Help text updated successfully!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="settings_help"),
                 InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]
            ])
        )
    
    await save_settings(settings)
    return ConversationHandler.END

async def settings_image_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle image settings updates."""
    user_id = update.effective_user.id
    if not is_owner(user_id):
        return
    
    if not update.message.photo:
        await update.message.reply_text("Please send an image.")
        return
    
    settings = await load_settings()
    photo = update.message.photo[-1]
    file_id = photo.file_id
    
    # Determine which setting we're updating based on conversation state
    if context.user_data.get('settings_mode') == 'start_image':
        settings["start"]["image"] = file_id
        await update.message.reply_text(
            "✅ Start image updated successfully!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="settings_start"),
                 InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]
            ])
        )
    elif context.user_data.get('settings_mode') == 'help_image':
        settings["help"]["image"] = file_id
        await update.message.reply_text(
            "✅ Help image updated successfully!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="settings_help"),
                 InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]
            ])
        )
    
    await save_settings(settings)
    return ConversationHandler.END

async def settings_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button settings updates."""
    user_id = update.effective_user.id
    if not is_owner(user_id):
        return
    
    button_text = update.message.text
    settings = await load_settings()
    
    try:
        # Parse button configuration
        buttons = []
        rows = button_text.split('\n')
        
        for row in rows:
            row_buttons = []
            button_configs = row.split('|')
            
            for config in button_configs:
                config = config.strip()
                if ' - ' in config:
                    text, url = config.split(' - ', 1)
                    text = text.strip()
                    url = url.strip()
                    
                    # Handle special callback buttons
                    if url.lower() in ['callback:back_start', 'callback:back_help', 'callback:close']:
                        url = url.lower()
                    
                    row_buttons.append({"text": text, "url": url})
            
            if row_buttons:
                buttons.append(row_buttons)
        
        # Determine which setting we're updating based on conversation state
        if context.user_data.get('settings_mode') == 'start_button':
            settings["start"]["buttons"] = buttons
            await update.message.reply_text(
                "✅ Start buttons updated successfully!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="settings_start_buttons"),
                     InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]
                ])
            )
        elif context.user_data.get('settings_mode') == 'help_button':
            settings["help"]["buttons"] = buttons
            await update.message.reply_text(
                "✅ Help buttons updated successfully!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="settings_help_buttons"),
                     InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]
                ])
            )
        
        await save_settings(settings)
        return ConversationHandler.END
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ Error parsing button configuration: {str(e)}\n\nPlease use the correct format.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="settings_start_buttons"),
                 InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]
            ])
        )
        return ConversationHandler.END

# Command Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    if update.message.chat.type == "private":
        # Track user
        data = await load_data()
        user_id = str(update.effective_user.id)
        if user_id not in data["users"]:
            data["users"][user_id] = {
                "first_seen": datetime.utcnow().isoformat(),
                "last_seen": datetime.utcnow().isoformat(),
                "username": update.effective_user.username,
                "first_name": update.effective_user.first_name,
                "last_name": update.effective_user.last_name
            }
        else:
            data["users"][user_id]["last_seen"] = datetime.utcnow().isoformat()
        await save_data(data)
        
        # Check if this is a deep link
        if context.args:
            file_id = context.args[0]
            data = await load_data()
            
            if file_id not in data["links"]:
                await update.message.reply_text("Invalid or expired invite link.")
                return
            
            link_data = data["links"][file_id]
            channel_data = data["channels"][link_data["channel_id"]]
            
            # Check if link is expired
            expiry_time = datetime.fromisoformat(link_data["expiry_time"])
            if datetime.utcnow() > expiry_time:
                # Link expired, create a new one
                try:
                    new_expiry = datetime.utcnow() + timedelta(seconds=LINK_DURATION)
                    new_invite_link = await context.bot.create_chat_invite_link(
                        chat_id=link_data["channel_id"],
                        expire_date=new_expiry,
                        creates_join_request=False
                    )
                    
                    # Update JSON with new link
                    data["links"][file_id] = {
                        "channel_id": link_data["channel_id"],
                        "invite_link": new_invite_link.invite_link,
                        "expiry_time": new_expiry.isoformat(),
                        "is_active": True,
                        "created_at": datetime.utcnow().isoformat()
                    }
                    await save_data(data)
                    
                    # Use the new link
                    link_data = data["links"][file_id]
                    logger.info(f"Regenerated expired link for {channel_data['name']}")
                except Exception as e:
                    await update.message.reply_text("Error generating new invite link. Please try again.")
                    logger.error(f"Error regenerating link: {e}")
                    return
            
            # Create inline button with the channel link
            keyboard = [
                [InlineKeyboardButton("Click here to join now", url=link_data["invite_link"])]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message = await update.message.reply_text(
                f"Join the channel '{channel_data['name']}' by clicking the button below:",
                reply_markup=reply_markup
            )
            
            message = await update.message.reply_text(
               "> *ɴᴏᴛᴇ\\:* ᴛʜɪs ɪɴᴠɪᴛᴇ ʟɪɴᴋ ᴇxᴘɪʀᴇs ɪɴ 5 ᴍɪɴᴜᴛᴇs\\. ɪғ ɪᴛ ᴇxᴘɪʀᴇs, ᴊᴜsᴛ ᴄʟɪᴄᴋ ᴛʜᴇ ᴘᴏsᴛ ʟɪɴᴋ ᴀɢᴀɪɴ ᴛᴏ ɢᴇᴛ ᴀ ɴᴇᴡ ᴏɴᴇ\\.",
                        parse_mode="MarkdownV2"
            )

            # Schedule message cleanup
            asyncio.create_task(cleanup_message(context, update.effective_chat.id, message.message_id))
        else:
            await start_callback(update, context)
    else:
        await update.message.reply_text("Please use this bot in private messages.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message with help information."""
    await help_command_callback(update, context)

async def gen_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate a permanent bot link with temporary channel invites."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("You are not authorized to use this bot.")
        return
    
    if not context.args:
        await update.message.reply_text("Please provide a channel link.\nUsage: /gen_link <channel_link>")
        return
    
    channel_input = context.args[0]
    await generate_single_link(update, context, channel_input)

async def batch_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate links for all channels where bot is admin."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("You are not authorized to use this bot.")
        return
    
    status_msg = await update.message.reply_text("Fetching all channels where bot is admin...")
    
    try:
        # This is a simplified approach - in a real implementation, you would need to
        # maintain a list of all channels where the bot has been added as admin
        
        # For now, we'll use the channels already in our database
        data = await load_data()
        
        if not data["channels"]:
            await status_msg.edit_text("No channels found in database. Use /gen_link to add channels first.")
            return
        
        count = 0
        bot_username = (await context.bot.get_me()).username
        message = "Generated links for all channels:\n\n"
        
        for channel_id, channel_data in data["channels"].items():
            file_id = channel_data["file_id"]
            
            # Check if link exists and is valid
            if file_id in data["links"]:
                link_data = data["links"][file_id]
                expiry_time = datetime.fromisoformat(link_data["expiry_time"])
                
                # If link is expired or about to expire, regenerate it
                if datetime.utcnow() > expiry_time - timedelta(minutes=1):
                    try:
                        new_expiry = datetime.utcnow() + timedelta(seconds=LINK_DURATION)
                        new_invite_link = await context.bot.create_chat_invite_link(
                            chat_id=channel_id,
                            expire_date=new_expiry,
                            creates_join_request=False
                        )
                        
                        # Update JSON with new link
                        data["links"][file_id] = {
                            "channel_id": channel_id,
                            "invite_link": new_invite_link.invite_link,
                            "expiry_time": new_expiry.isoformat(),
                            "is_active": True,
                            "created_at": datetime.utcnow().isoformat()
                        }
                        
                        count += 1
                        logger.info(f"Regenerated link for {channel_data['name']}")
                        
                        # Add to message
                        bot_link = f"https://t.me/{bot_username}?start={file_id}"
                        message += f"• {channel_data['name']}: {bot_link}\n"
                    except Exception as e:
                        logger.error(f"Error regenerating link for {channel_data['name']}: {e}")
                        message += f"• {channel_data['name']}: Error - {str(e)}\n"
                else:
                    # Link is still valid
                    bot_link = f"https://t.me/{bot_username}?start={file_id}"
                    message += f"• {channel_data['name']}: {bot_link}\n"
                    count += 1
        
        await save_data(data)
        
        # Split message if too long
        if len(message) > 4000:
            parts = [message[i:i+4000] for i in range(0, len(message), 4000)]
            for part in parts:
                await update.message.reply_text(part)
        else:
            await update.message.reply_text(message)
            
        await status_msg.edit_text(f"Batch link generation completed. Processed {count} channels.")
        
    except Exception as e:
        logger.error(f"Error in batch_link: {e}")
        await status_msg.edit_text(f"Error: {str(e)}")

async def list_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all active channels and their current links with pagination."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("You are not authorized to use this bot.")
        return
    
    try:
        data = await load_data()
        
        if not data["channels"]:
            await update.message.reply_text("No active channels found.\n\nUse /gen_link to create channel links.")
            return
        
        # Get page number from context args or default to 1
        page = 1
        if context.args and context.args[0].isdigit():
            page = int(context.args[0])
        
        bot_username = (await context.bot.get_me()).username
        channels = list(data["channels"].items())
        total_pages = (len(channels) + LIST_CHANNELS_PAGE_SIZE - 1) // LIST_CHANNELS_PAGE_SIZE
        page = max(1, min(page, total_pages))
        
        start_idx = (page - 1) * LIST_CHANNELS_PAGE_SIZE
        end_idx = min(start_idx + LIST_CHANNELS_PAGE_SIZE, len(channels))
        
        message = f"Active Channels (Page {page}/{total_pages}):\n\n"
        
        for i in range(start_idx, end_idx):
            channel_id, channel_data = channels[i]
            file_id = channel_data["file_id"]
            
            if file_id in data["links"]:
                link_data = data["links"][file_id]
                expiry_time = datetime.fromisoformat(link_data["expiry_time"])
                time_left = expiry_time - datetime.utcnow()
                minutes_left = max(0, int(time_left.total_seconds() / 60))
                
                bot_link = f"https://t.me/{bot_username}?start={file_id}"
                message += f"• {channel_data['name']}:\n  Permanent Link: {bot_link}\n  Current invite expires in: {minutes_left} minutes\n\n"
            else:
                message += f"• {channel_data['name']}: Link expired or missing\n\n"
        
        message += f"Total: {len(data['channels'])} channels"
        
        # Create pagination buttons
        keyboard = []
        if total_pages > 1:
            if page > 1:
                keyboard.append([InlineKeyboardButton("《 ᴩʀᴇᴠɪᴏᴜꜱ", callback_data=f"list_channels_{page-1}")])
            if page < total_pages:
                if keyboard:
                    keyboard[0].append(InlineKeyboardButton("ɴᴇxᴛ 》", callback_data=f"list_channels_{page+1}"))
                else:
                    keyboard.append([InlineKeyboardButton("ɴᴇxᴛ 》", callback_data=f"list_channels_{page+1}")])
        
        keyboard.append([InlineKeyboardButton(f"ᴩᴀɢᴇ {page}/{total_pages}", callback_data="page_info")])
        keyboard.append([InlineKeyboardButton("⌕ ꜱᴇᴀʀᴄʜ ᴄʜᴀɴɴᴇʟ", callback_data="search_channel")])
        keyboard.append([InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)

        # If this is a callback query, edit the message instead of sending a new one
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message, reply_markup=reply_markup)
                
    except Exception as e:
        logger.error(f"Error listing channels: {e}")
        await update.message.reply_text(f"Error retrieving channel list: {str(e)}")

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
      query = update.callback_query
    #Get page number from context args or default to 1
      page = 1
      if context.args and context.args[0].isdigit():
        page = int(context.args[0])
        
     bot_username = (await context.bot.get_me()).username
     channels = list(data["channels"].items())
     total_pages = (len(channels) + LIST_CHANNELS_PAGE_SIZE - 1) // LIST_CHANNELS_PAGE_SIZE
     page = max(1, min(page, total_pages))

      if query.data == "page_info":
       await query.answer(text=f"ʏᴏᴜ ᴀʀᴇ ᴏɴ: {page}/{total_pages}", show_alert=True)
    
# Temporary dict to store users who clicked "Search 🔍"
pending_search = {}

# Load channel data
async def load_channel_data():
    try:
        with open("channel_data.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"channels": {}}

# 🔍 Callback for "Search 🔍" button
async def search_channel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Delete previous list message
    try:
        await query.message.delete()
    except:
        pass

    # Ask user for channel name
    prompt_msg = await query.message.reply_text("🔍 Please send the channel name you want to search:")

    # Store pending search: user_id -> chat_id and prompt message
    pending_search[query.from_user.id] = {
        "chat_id": query.message.chat_id,
        "prompt_msg_id": prompt_msg.message_id
    }

# Message handler to capture search term
async def search_channel_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    # Only respond if user clicked the search button before
    if user_id not in pending_search:
        return

    search_term = update.message.text.strip()

    # Delete user's message for cleaner chat
    try:
        await update.message.delete()
    except:
        pass

    # Send temporary "Searching..." message
    searching_msg = await update.message.reply_text(f"🔎 Searching for {search_term}...")

    # Load channel data
    data = await load_channel_data()
    channels = data.get("channels", {})

    found_channel = None
    for channel_id, info in channels.items():
        if search_term.lower() in info.get("name", "").lower():
            found_channel = {
                "title": info.get("name", "Unknown"),
                "id": channel_id,
                "file_id": info.get("file_id", "N/A")
            }
            break

    # Delete prompt and "Searching..." messages
    try:
        chat_id = pending_search[user_id]["chat_id"]
        prompt_msg_id = pending_search[user_id]["prompt_msg_id"]
        await context.bot.delete_message(chat_id=chat_id, message_id=prompt_msg_id)
        await asyncio.sleep(1)  # small delay
        await searching_msg.delete()
    except:
        pass

    # Remove user from pending_search
    pending_search.pop(user_id, None)

    # Send result
    if found_channel:
        bot_username = (await context.bot.get_me()).username
        base64_link = f"https://t.me/{bot_username}?start={found_channel['file_id']}"
        result_text = (
            f"✅ Channel Found!\n\n"
            f"Title: {found_channel['title']}\n"
            f"ID: {found_channel['id']}\n"
            f"Link: {base64_link}"
        )
        await update.message.reply_text(result_text)
    else:
        await update.message.reply_text("❌ No matching channel found.")

    
async def list_channels_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle list channels pagination callbacks."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith("list_channels_"):
        page = int(data.split("_")[2])
        context.args = [str(page)]
        # Call list_channels and pass update as callback_query
        await list_channels(update, context)

async def debug_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Debug channel permissions."""
    if not is_admin(update.effective_user.id):
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /debug <channel_link>")
        return
    
    channel_input = context.args[0]
    status_msg = await update.message.reply_text("Debugging...")
    
    try:
        # Try to get chat using our improved extractor
        channel_info = await extract_channel_info(context, channel_input)
        
        if not channel_info:
            await status_msg.edit_text("❌ Could not find channel or bot is not admin")
            return
        
        channel_id, channel_name, chat = channel_info
        
        # Test creating an actual link
        try:
            test_link = await context.bot.create_chat_invite_link(
                chat_id=chat.id,
                expire_date=datetime.utcnow() + timedelta(seconds=60),
                creates_join_request=False
            )
            
            await status_msg.edit_text(
                f"✅ Bot has proper permissions in {channel_name}\n\n"
                f"• Channel ID: {chat.id}\n"
                f"• Can create links: YES\n"
                f"• Test link created: {test_link.invite_link}\n\n"
                f"Now try: /gen_link {channel_input}"
            )
            
        except Exception as e:
            await status_msg.edit_text(
                f"❌ Bot cannot create invite links in {channel_name}\n\n"
                f"• Channel ID: {chat.id}\n"
                f"• Error: {str(e)}\n\n"
                f"Please ensure the bot has 'Create invite links' permission."
            )
            
    except Exception as e:
        await status_msg.edit_text(f"Error: {str(e)}")

async def troubleshoot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Troubleshoot common issues."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id) and not is_owner(user_id):
        await update.message.reply_text("You are not authorized to use this bot.")
        return
    
    troubleshoot_text = """✦ ᴛʀᴏᴜʙʟᴇsʜᴏᴏᴛ

1\\. ɪғ ʙᴏᴛ ɪs ɴᴏᴛ ᴡᴏʀᴋɪɴɢ, ᴇɴsᴜʀᴇ ɪᴛ ɪs ᴀᴅᴍɪɴ ɪɴ ᴛᴀʀɢᴇᴛ ᴄʜᴀɴɴᴇʟs\\.    
2\\. ᴠᴇʀɪғʏ ʙᴏᴛ ʜᴀs ᴘᴇʀᴍɪssɪᴏɴ ᴛᴏ ᴄʀᴇᴀᴛᴇ ɪɴᴠɪᴛᴇ ʟɪɴᴋs\\.  
3\\. ᴜsᴇ ᴄʜᴀɴɴᴇʟ ɪᴅ ɪɴsᴛᴇᴀᴅ ᴏғ ᴄʜᴀɴɴᴇʟ ʟɪɴᴋ\\.  
4\\. ᴄʜᴇᴄᴋ ɪɴᴛᴇʀɴᴇᴛ ᴄᴏɴɴᴇᴄᴛɪᴏɴ ɪғ ʙᴏᴛ ғᴀɪʟs ᴛᴏ ʀᴇsᴘᴏɴᴅ\\.  
5\\. ᴜsᴇ /debug \\<channel\\_link/id\\> ᴛᴏ ᴄʜᴇᴄᴋ ᴘᴇʀᴍɪssɪᴏɴ ɪssᴜᴇs\\.  

ғᴏʀ ғᴜʀᴛʜᴇʀ ᴀssɪsᴛᴀɴᴄᴇ\\, ᴄᴏɴᴛᴀᴄᴛ [ᴏᴡɴᴇʀ](https://t.me/Quarel7)\\."""
    
    keyboard = [
        [InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(troubleshoot_text, reply_markup=reply_markup, parse_mode="MarkdownV2")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get user ID."""
    user_id = update.effective_user.id
    await update.message.reply_text(f"Your ID: `{user_id}`", parse_mode="Markdown")

async def admins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all bot admins."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("You are not authorized to use this bot.")
        return
    
    data = await load_data()
    admins = data.get("admins", [])
    
    message = "Bot Admins:\n\n"
    for i, admin_id in enumerate(admins, 1):
        try:
            user = await context.bot.get_chat(admin_id)
            message += f"{i}. {user.first_name} ({user.id})\n"
        except:
            message += f"{i}. Unknown User ({admin_id})\n"
    
    keyboard = [
        [InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user statistics."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("You are not authorized to use this bot.")
        return
    
    data = await load_data()
    users_count = len(data.get("users", {}))
    admins_count = len(data.get("admins", []))
    banned_count = len(data.get("banned_users", []))
    
    message = f"""User Statistics:

• Total Users: {users_count}
• Admins: {admins_count}
• Banned Users: {banned_count}"""

    keyboard = [
        [InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

# Owner-only commands
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
        
        data = await load_data()
        
        # Initialize users dictionary if it doesn't exist
        if "users" not in data:
            data["users"] = {}
        
        # Add or update user authorization
        expiry_date = datetime.utcnow() + timedelta(days=days)
        data["users"][str(user_id)] = {
            "authorized": True,
            "expiry_date": expiry_date.isoformat(),
            "authorized_by": update.effective_user.id,
            "authorized_at": datetime.utcnow().isoformat()
        }
        
        await save_data(data)
        
        await update.message.reply_text(
            f"User {user_id} authorized for {days} days until {expiry_date.strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )
        
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
        
        data = await load_data()
        
        if "users" in data and str(user_id) in data["users"]:
            del data["users"][str(user_id)]
            await save_data(data)
            await update.message.reply_text(f"User {user_id} deauthorized.")
        else:
            await update.message.reply_text(f"User {user_id} not found in authorized users.")
            
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
        
        if user_id not in ADMIN_IDS:
            ADMIN_IDS.append(user_id)
            
            # Save to data file for persistence
            data = await load_data()
            if "admins" not in data:
                data["admins"] = []
            
            if user_id not in data["admins"]:
                data["admins"].append(user_id)
                await save_data(data)
            
            await update.message.reply_text(f"User {user_id} promoted to admin.")
        else:
            await update.message.reply_text(f"User {user_id} is already an admin.")
            
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
        
        if user_id in ADMIN_IDS and user_id != OWNER_ID:
            ADMIN_IDS.remove(user_id)
            
            # Remove from data file
            data = await load_data()
            if "admins" in data and user_id in data["admins"]:
                data["admins"].remove(user_id)
                await save_data(data)
            
            await update.message.reply_text(f"User {user_id} demoted from admin.")
        elif user_id == OWNER_ID:
            await update.message.reply_text("Cannot demote the owner.")
        else:
            await update.message.reply_text(f"User {user_id} is not an admin.")
            
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
        
        data = await load_data()
        
        # Initialize banned users list if it doesn't exist
        if "banned_users" not in data:
            data["banned_users"] = []
        
        if user_id not in data["banned_users"]:
            data["banned_users"].append(user_id)
            await save_data(data)
            
            # Also remove from admins and authorized users if present
            if user_id in ADMIN_IDS and user_id != OWNER_ID:
                ADMIN_IDS.remove(user_id)
            
            if "admins" in data and user_id in data["admins"]:
                data["admins"].remove(user_id)
            
            if "users" in data and str(user_id) in data["users"]:
                del data["users"][str(user_id)]
            
            await save_data(data)
            
            await update.message.reply_text(f"User {user_id} banned from using the bot.")
        else:
            await update.message.reply_text(f"User {user_id} is already banned.")
            
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
        
        data = await load_data()
        
        if "banned_users" in data and user_id in data["banned_users"]:
            data["banned_users"].remove(user_id)
            await save_data(data)
            await update.message.reply_text(f"User {user_id} unbanned.")
        else:
            await update.message.reply_text(f"User {user_id} is not banned.")
            
    except ValueError:
        await update.message.reply_text("Invalid user ID format. Please use a number.")

async def restart_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Restart the bot."""
    try:
        await update.message.delete()
    except Exception as e:
        print(f"Could not delete message: {e}")
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
    
    # Save current state
    data = await load_data()
    data["restart"] = {
        "chat_id": update.effective_chat.id,
        "message_id": update.effective_message.message_id,
        "time": datetime.utcnow().isoformat()
    }
    await save_data(data)
    
    # Use a proper restart mechanism
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
    data = await load_data()
    
    # Get all user IDs from various sources
    user_ids = set()
    
    # From authorized users
    if "users" in data:
        user_ids.update([int(uid) for uid in data["users"].keys()])
    
    # From admins
    if "admins" in data:
        user_ids.update(data["admins"])
    
    # From channels (owners)
    for channel_id in data.get("channels", {}):
        # Try to get channel info to find owner
        try:
            chat = await context.bot.get_chat(channel_id)
            if chat and hasattr(chat, 'id'):
                user_ids.add(chat.id)
        except:
            pass
    
    # Send message to all users
    success_count = 0
    fail_count = 0
    
    for user_id in user_ids:
        try:
            await context.bot.send_message(user_id, f"{message_text}")
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to send broadcast to {user_id}: {e}")
            fail_count += 1
    
    await update.message.reply_text(
        f"Broadcast completed.\nSuccess: {success_count}\nFailed: {fail_count}"
    )

async def update_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update the bot from GitHub."""
    try:
        await update.message.delete()
    except Exception as e:
        print(f"Could not delete message: {e}")
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

# /channels command
async def channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ You are not authorized to use this bot.")
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

    # Send the main menu and store its message ID in user_data
    menu_message = await update.message.reply_text("Choose the file you want:", reply_markup=reply_markup)
    context.user_data["menu_message_id"] = menu_message.message_id


# Channels button handler
async def button_handler_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id != OWNER_ID:
        await query.edit_message_text("❌ You are not authorized to use this bot.")
        return

    menu_message_id = context.user_data.get("menu_message_id")

    # Main menu keyboard
    main_menu = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("📂 Channels", callback_data="get_channels"),
            InlineKeyboardButton("⚙️ Bot Settings", callback_data="get_settings")
        ]]
    )

    # Back + Close keyboard
    back_close_keyboard = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("🔙 Back", callback_data="back_channels"),
            InlineKeyboardButton("❌ Close", callback_data="close_channels")
        ]]
    )

    if query.data == "get_channels":
        # Delete previous document message (if any)
        try:
            await query.message.delete()
        except:
            pass
        if os.path.exists(JSON_STORAGE):
            with open(JSON_STORAGE, "rb") as file:
                await query.message.reply_document(
                    document=file,
                    filename="Channel_data.json",
                    caption="📂 Here is your Channel data.",
                    reply_markup=back_close_keyboard
                )
        else:
            await query.message.reply_text("⚠️ Channel_data.json file not found!", reply_markup=main_menu)

    elif query.data == "get_settings":
        try:
            await query.message.delete()
        except:
            pass
        if os.path.exists(SETTINGS_STORAGE):
            with open(SETTINGS_STORAGE, "rb") as file:
                await query.message.reply_document(
                    document=file,
                    filename="Bot_Setting.json",
                    caption="⚙️ Here is your Bot Settings.",
                    reply_markup=back_close_keyboard
                )
        else:
            await query.message.reply_text("⚠️ Bot_Setting.json file not found!", reply_markup=main_menu)

    elif query.data == "back_channels":
        # Delete current document message first
        try:
            await query.message.delete()
        except:
            pass
        # Send main menu again
        menu_message = await query.message.chat.send_message("Choose the file you want:", reply_markup=main_menu)
        context.user_data["menu_message_id"] = menu_message.message_id

    elif query.data == "close_channels":
        try:
            await query.message.delete()
        except:
            pass

#Ping 
BOT_START_TIME = time.time()

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check bot uptime and responsiveness."""
    start_time = time.time()
    try:
        await update.message.delete()
    except Exception as e:
        print(f"Could not delete message: {e}")
        
    # Send "Pinging..." message first
    msg = await context.bot.send_message(
       chat_id=update.effective_chat.id,
       text="⏳ Pinging..."
    )
    # Calculate latency
    end_time = time.time()
    latency_ms = int((end_time - start_time) * 1000)

    # Calculate uptime
    uptime_sec = int(time.time() - BOT_START_TIME)
    uptime_str = str(timedelta(seconds=uptime_sec))

    # Delete "Pinging..." message
    try:
        await msg.delete()
    except Exception:
        pass

    # Send final message with image
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo="/data/data/com.termux/files/home/storage/downloads/IMG_20250917_181004.jpg",
        caption=(
            f"✅ **Pong!**\n"
            f"📡 Latency: `{latency_ms} ms`\n"
            f"⏱️ Uptime: `{uptime_str}`"
        ),
        parse_mode="Markdown"
    )
#log file 
async def get_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    msg = await update.message.reply_text("📄 Generating log...")

    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()

        log_content = ""
        for line in lines:
            if "ERROR" in line or "Exception" in line:
                log_content += f"❌ {line}"
            else:
                log_content += line

        with open("log.txt", "w") as f:
            f.write(log_content)

        await msg.delete()

        # Send log.txt as document only (no image)
        with open("log.txt", "rb") as f_doc:
            await update.message.reply_document(
                document=f_doc,
                filename="log.txt",
                caption="📄 Log file"
            )
    else:
        await msg.edit_text("⚠️ Log file not found!")

#/maintenance command
async def get_latest_commit_message():
    """Fetch latest commit message from GitHub repo."""
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
    """
    Broadcast message to all active users with progress bar and cancel support.
    """
    global BROADCAST_CANCELLED
    BROADCAST_CANCELLED = False

    data = await load_data()
    users = list(data.get("users", {}))
    total_users = len(users)
    success_count = 0
    failed_count = 0

    keyboard = [[InlineKeyboardButton("Cancel ❌", callback_data="broadcast_cancel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    for idx, user_id in enumerate(users, start=1):
        if BROADCAST_CANCELLED:
            await message_obj.edit_text("❌ Broadcasting cancelled by owner.")
            return

        try:
            await context.bot.send_message(chat_id=int(user_id), text=text)
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
        await asyncio.sleep(0.05)  # slight delay to avoid rate limits

    await message_obj.edit_text(
        f"✅ Broadcasting completed!\n"
        f"✅ Success: {success_count}\n"
        f"❌ Failed: {failed_count}\n"
        f"Total users: {total_users}"
    )


async def broadcast_cancel_callback(update, context: ContextTypes.DEFAULT_TYPE):
    global BROADCAST_CANCELLED
    query = update.callback_query
    if query.from_user.id != OWNER_ID:
        await query.answer("🚫 You are not authorized!", show_alert=True)
        return

    BROADCAST_CANCELLED = True
    await query.answer("❌ Broadcasting cancelled")
    await query.delete_message()


# --- MAINTENANCE COMMAND ---
async def maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


# --- MAINTENANCE BUTTON CALLBACK ---
async def maintenance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        # Ask if user wants to alert
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

    # Update buttons
    keyboard = [
        [
            InlineKeyboardButton("On ✅" if MAINTENANCE_MODE else "On ❌", callback_data="maint_on"),
            InlineKeyboardButton("Off ✅" if not MAINTENANCE_MODE else "Off ❌", callback_data="maint_off"),
        ],
        [InlineKeyboardButton("Close ❌", callback_data="maint_close")]
    ]
    await query.edit_message_text("⚙️ Maintenance Mode Control:", reply_markup=InlineKeyboardMarkup(keyboard))
    await query.answer("Updated successfully ✅")


# --- ALERT CALLBACK ---
async def alert_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


# --- CUSTOM ALERT MESSAGE HANDLER ---
async def custom_alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global AWAITING_CUSTOM_ALERT
    if not AWAITING_CUSTOM_ALERT or update.effective_user.id != OWNER_ID:
        return

    AWAITING_CUSTOM_ALERT = False
    custom_text = update.message.text
    status_msg = await update.message.reply_text("Starting broadcasting...")
    await broadcast_to_users_with_progress(context, custom_text, status_msg)


# --- MAINTENANCE GUARD ---
async def maintenance_guard(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
                
#Forward_from_channel              
async def forwarded_channel_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if not message:
        return  

    # Restrict only to private chat (DM)
    if message.chat.type != "private":
        return  

    if not getattr(message, "forward_origin", None):
        await message.reply_text("⚠️ This message is not forwarded from a channel!")
        return

    origin = message.forward_origin

    if origin.type == "channel":
        channel_id = str(origin.chat.id)
        channel_title = origin.chat.title

        # Escape MarkdownV2 special characters for title and ID
        import re
        channel_title_safe = re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', channel_title)
        channel_id_safe = re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', channel_id)

        await message.reply_text(
            f"📢 Forwarded Channel:\nTitle: {channel_title_safe}\nID: `{channel_id_safe}`",
            parse_mode="MarkdownV2"
        )
    else:
        await message.reply_text("⚠️ This forwarded message is not from a channel.")
#main
def main():
    """Start the bot."""
    # Load admin IDs from data file for persistence
    async def load_admin_ids():
        data = await load_data()
        if "admins" in data:
            for admin_id in data["admins"]:
                if admin_id not in ADMIN_IDS:
                    ADMIN_IDS.append(admin_id)
    
    # Create the Application
    application = (Application.builder()
    .token(BOT_TOKEN)
    .read_timeout(15)
    .write_timeout(30)  
    .connect_timeout(20)
    .pool_timeout(20)
    .build())

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("gen_link", gen_link))
    application.add_handler(CommandHandler("batch_link", batch_link))
    application.add_handler(CommandHandler("list_channels", list_channels))
    application.add_handler(CommandHandler("debug", debug_channel))
    application.add_handler(CommandHandler("troubleshoot", troubleshoot))
    application.add_handler(CommandHandler("id", get_id))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("admins", admins_command))
    application.add_handler(CommandHandler("users", users_command))
    
    # Owner commands
    application.add_handler(CommandHandler("auth", auth_user))
    application.add_handler(CommandHandler("deauth", deauth_user))
    application.add_handler(CommandHandler("promote", promote_user))
    application.add_handler(CommandHandler("demote", demote_user))
    application.add_handler(CommandHandler("ban", ban_user))
    application.add_handler(CommandHandler("unban", unban_user))
    application.add_handler(CommandHandler("restart", restart_bot))
    application.add_handler(CommandHandler("broadcast", broadcast_message))
    application.add_handler(CommandHandler("update", update_bot))
    application.add_handler(CommandHandler("channels", channels))
    application.add_handler(CommandHandler("ping", ping))
    application.add_handler(CommandHandler("log", get_log))
    application.add_handler(CommandHandler("maintenance", maintenance))
    # Button handlers
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^(about|help_requirements|help_how|help_troubleshoot|back_start|back_help|close|settings_main|settings_start|settings_start_text|settings_start_image|settings_start_buttons|settings_start_add_button|settings_start_remove_button|settings_help|settings_help_text|settings_help_image|settings_help_buttons|settings_help_add_button|settings_help_remove_button|remove_button_confirm_.*|remove_help_button_confirm_.*|remove_button_cancel_.*|remove_help_button_cancel_.*)$"))
    #Channels Button Handlers 
    application.add_handler(CallbackQueryHandler(button_handler_channels, pattern="^(get_channels|get_settings|back_channels|close_channels)$"))

    #Forward
    application.add_handler(MessageHandler(filters.FORWARDED, forwarded_channel_id))
    
    #Maintenance mode 
    application.add_handler(CallbackQueryHandler(maintenance_callback, pattern="^maint_"))
    application.add_handler(CallbackQueryHandler(alert_callback, pattern="^alert_"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, custom_alert),
    group=1)
    application.add_handler(MessageHandler(filters.COMMAND, maintenance_guard), group=0)
    application.add_handler(CallbackQueryHandler(broadcast_cancel_callback, pattern="broadcast_cancel"))
    
    # List channels pagination
    application.add_handler(CallbackQueryHandler(list_channels_callback, pattern="^list_channels_"))

    #Page alert
    application.add_handler(CallbackQueryHandler(button_click),
    group=1)
    
    #Search Handler
    application.add_handler(CallbackQueryHandler(search_channel_callback, pattern="^search_channel$"))
    # Message handler for capturing search term
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_channel_message),
    group=0)
    # Settings conversation handler
    settings_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("settings", settings_command)],
        states={
            SETTINGS_MAIN: [CallbackQueryHandler(settings_command_callback, pattern="^settings_main$")],
            SETTINGS_START: [CallbackQueryHandler(settings_start_callback, pattern="^settings_start$")],
            SETTINGS_START_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, settings_text_handler)],
            SETTINGS_START_IMAGE: [MessageHandler(filters.PHOTO, settings_image_handler)],
            SETTINGS_START_BUTTONS: [CallbackQueryHandler(settings_start_buttons_callback, pattern="^settings_start_buttons$")],
            SETTINGS_START_ADD_BUTTON: [MessageHandler(filters.TEXT & ~filters.COMMAND, settings_button_handler)],
            SETTINGS_START_REMOVE_BUTTON: [CallbackQueryHandler(settings_start_remove_button_callback, pattern="^settings_start_remove_button$")],
            SETTINGS_HELP: [CallbackQueryHandler(settings_help_callback, pattern="^settings_help$")],
            SETTINGS_HELP_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, settings_text_handler)],
            SETTINGS_HELP_IMAGE: [MessageHandler(filters.PHOTO, settings_image_handler)],
            SETTINGS_HELP_BUTTONS: [CallbackQueryHandler(settings_help_buttons_callback, pattern="^settings_help_buttons$")],
            SETTINGS_HELP_ADD_BUTTON: [MessageHandler(filters.TEXT & ~filters.COMMAND, settings_button_handler)],
            SETTINGS_HELP_REMOVE_BUTTON: [CallbackQueryHandler(settings_help_remove_button_callback, pattern="^settings_help_remove_button$")],
        },
        fallbacks=[CommandHandler("cancel", lambda update, context: ConversationHandler.END)],
    )
    
    application.add_handler(settings_conv_handler)
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, smallcaps_handler),
    group=2)

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message),
    group=2)
    
    
    # Initialize and run
    async def run():
        await load_admin_ids()
        logger.info("Bot started successfully!")
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
  # Keep connection alive with shorter intervals for Termux  
        if hasattr(application.updater, 'job_queue') and hasattr(application.updater.job_queue, 'scheduler'):
            application.updater.job_queue.scheduler.configure(
                timezone="UTC",
                max_workers=2  # Reduce worker threads for Termux
            )
        # Check if we need to send restart confirmation
        data = await load_data()
        if "restart" in data:
            restart_data = data["restart"]
            try:
                await application.bot.edit_message_text(
                    chat_id=restart_data["chat_id"],
                    message_id=restart_data["message_id"],
                    text="✅ ʙᴏᴘ ʀᴇꜱᴛᴀʀᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟy!"
                )
            except:
                pass
            
            # Remove restart data
            del data["restart"]
            await save_data(data)
        
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("Received stop signal")
        finally:
            await application.updater.stop()
            await application.stop()
            await application.shutdown()
            logger.info("Bot stopped")

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")

if __name__ == '__main__':
    main()





























































































