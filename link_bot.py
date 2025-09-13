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

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = "7965411711:AAHcFqZYLiNE6bvmBE2iQB_CYBWxME4PuKs"
OWNER_ID = 5373577888
ADMIN_IDS = [5373577888, 6170814776, 6959143950]
LINK_DURATION = 5 * 60  # 5 minutes in seconds
MESSAGE_CLEANUP_TIME = 3 * 60  # 6 minutes in seconds

# JSON storage file
JSON_STORAGE = "channel_data.json"
SETTINGS_STORAGE = "bot_settings.json"

# Conversation states
(
    ABOUT, HELP_REQUIREMENTS, HELP_HOW, HELP_TROUBLESHOOT,
    SETTINGS_MAIN, SETTINGS_START, SETTINGS_START_TEXT, SETTINGS_START_IMAGE,
    SETTINGS_START_BUTTONS, SETTINGS_START_ADD_BUTTON, SETTINGS_START_REMOVE_BUTTON,
    SETTINGS_HELP, SETTINGS_HELP_TEXT, SETTINGS_HELP_IMAGE,
    SETTINGS_HELP_BUTTONS, SETTINGS_HELP_ADD_BUTTON, SETTINGS_HELP_REMOVE_BUTTON
) = range(16)

# Image paths (will be managed through settings)
START_IMAGE = "photo_2025-08-31_23-17-37.jpg"
HELP_IMAGE = "photo_2025-08-31_23-16-44.jpg"

# Pagination
LIST_CHANNELS_PAGE_SIZE = 10

# small caps
def to_small_caps(text: str) -> str:
    small_caps_map = {
        "a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ", "e": "ᴇ", "f": "ғ", "g": "ɢ",
        "h": "ʜ", "i": "ɪ", "j": "ᴊ", "k": "ᴋ", "l": "ʟ", "m": "ᴍ", "n": "ɴ",
        "o": "ᴏ", "p": "ᴘ", "q": "ǫ", "r": "ʀ", "s": "s", "t": "ᴛ", "u": "ᴜ",
        "v": "ᴠ", "w": "ᴡ", "x": "x", "y": "ʏ", "z": "ᴢ"
    }
    return "".join(small_caps_map.get(ch.lower(), ch) for ch in text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:  # skip non-message updates
        return
    user_text = update.message.text or ""
    formatted_text = to_small_caps(user_text)
    await update.message.reply_text(formatted_text)

# Utility Functions
def is_admin(user_id):
    """Check if user is an admin."""
    return user_id in ADMIN_IDS

def is_owner(user_id):
    """Check if user is the owner."""
    return user_id == OWNER_ID

def load_data():
    """Load data from JSON file."""
    if os.path.exists(JSON_STORAGE):
        try:
            with open(JSON_STORAGE, 'r') as f:
                return json.load(f)
        except:
            return {"channels": {}, "links": {}, "users": {}, "admins": []}
    return {"channels": {}, "links": {}, "users": {}, "admins": []}

def save_data(data):
    """Save data to JSON file."""
    with open(JSON_STORAGE, 'w') as f:
        json.dump(data, f, indent=2)

def load_settings():
    """Load settings from JSON file."""
    if os.path.exists(SETTINGS_STORAGE):
        try:
            with open(SETTINGS_STORAGE, 'r') as f:
                return json.load(f)
        except:
            return {
                "start": {
                    "text": """✦ ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ ᴀᴅᴠᴀɴᴄᴇᴅ ʟɪɴᴋs sʜᴀʀɪɴɢ ʙᴏᴛ
• ᴡɪᴛʜ ᴛʜɪs ʙᴏᴛ, ʏᴏᴜ ᴄᴀɴ sᴀғᴇʟʏ sʜᴀʀᴇ ʟɪɴᴋs ᴀɴᴅ ᴋᴇᴇᴘ ʏᴏᴜʀ ᴄʜᴀɴɴᴇʟs ᴘʀᴏᴛᴇᴄᴛᴇᴅ ғʀᴏᴍ ᴄᴏᴘʏʀɪɢʜᴛ ɪssᴜᴇs.

✦ ғᴇᴀᴛᴜʀᴇs:
• ғᴀsᴛ ᴀɴᴅ ᴇᴀsʏ ʟɪɴᴋ ᴘʀᴏᴄᴇssɪɴɢ
• ᴘᴇʀᴍᴀɴᴇɴᴛ ʟɪɴᴋs ᴡɪᴛʜ ᴛᴇᴍᴘᴏʀᴀʀʏ ᴀᴄᴄᴇss ғᴏʀ sᴀғᴇᴛʏ
• ᴘʀɪᴠᴀᴛᴇ, sᴇᴄᴜʀᴇ, ᴀɴᴅ ғᴜʟʟʏ ᴘʀᴏᴛᴇᴄᴛᴇᴅ ᴄᴏɴᴛᴇɴᴛ
✦ ᴇɴᴊᴏʏ ᴀ sᴍᴀʀᴛᴇʀ, sᴀғᴇʀ, ᴀɴᴅ ᴍᴏʀᴇ ᴘᴏᴡᴇʀғᴜʟ ᴡᴀʏ ᴛᴏ sʜᴀʀᴇ ʟɪɴᴋs!""",
                    "image": "photo_2025-08-31_23-17-37.jpg",
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
• /gen_link <channel_link/id> – ɢᴇɴᴇʀᴀᴛᴇ ᴀ ᴘᴇʀᴍᴀɴᴇɴᴛ ʙᴏᴛ ʟɪɴᴋ ᴡɪᴛʜ ᴀ 5-ᴍɪɴᴜᴛᴇ ᴛᴇᴍᴘᴏʀᴀʀʏ ɪɴᴠɪᴛᴇ  
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
• /broadcast – sᴇɴᴅ ᴀ ᴍᴇssᴀᴢᴇ ᴛᴏ ᴀʟʟ ᴜsᴇʀs  
• /update - ᴜᴘᴅᴀᴛᴇ ʙᴏᴛ ꜰʀᴏᴍ ɢɪᴛʜᴜʙ""",
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
    return {
        "start": {
            "text": """✦ ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ ᴀᴅᴠᴀɴᴄᴇᴅ ʟɪɴᴋs sʜᴀʀɪɴɢ ʙᴏᴛ
• ᴡɪᴛʜ ᴛʜɪs ʙᴏᴛ, ʏᴏᴜ ᴄᴀɴ sᴀғᴇʟʏ sʜᴀʀᴇ ʟɪɴᴋs ᴀɴᴅ ᴋᴇᴇᴘ ʏᴏᴜʀ ᴄʜᴀɴɴᴇʟs �ᴘʀᴏᴛᴇᴄᴛᴇᴅ ғʀᴏᴍ ᴄᴏᴘʏʀɪɢʜᴛ ɪssᴜᴇs.

✦ ғᴇᴀᴛᴜʀᴇs:
• ғᴀsᴛ ᴀɴᴅ ᴇᴀsʏ ʟɪɴᴋ ᴘʀᴏᴄᴇssɪɴɢ
• ᴘᴇʀᴍᴀɴᴇɴᴛ ʟɪɴᴋs ᴡɪᴛʜ ᴛᴇᴍᴘᴏʀᴀʀʏ ᴀᴄᴄᴇss ғᴏʀ sᴀғᴇᴛʏ
• ᴘʀɪᴠᴀᴛᴇ, sᴇᴄᴜʀᴇ, ᴀɴᴅ ғᴜʟʟʏ ᴘʀᴏᴛᴇᴄᴛᴇᴅ ᴄᴏɴᴛᴇɴᴛ
✦ ᴇɴᴊᴏʏ ᴀ sᴍᴀʀᴛᴇʀ, sᴀғᴇʀ, ᴀɴᴅ ᴍᴏʀᴇ ᴘᴏᴡᴇʀғᴜʟ ᴡᴀʏ ᴛᴏ sʜᴀʀᴇ ʟɪɴᴋs!""",
            "image": "photo_2025-08-31_23-17-37.jpg",
            "buttons": [
                [{"text": "ᴀʙᴏᴜᴛ", "url": "callback:about"}],
                [{"text": "ᴄʟᴏsᴇ", "url": "callback:close"}]
            ]
        },
        "help": {
            "text": """✦ ʙᴏᴛ ʜᴇʟᴘ ɢᴜɪᴅᴇ

┌─ ᴜsᴇʀ ᴄᴏᴍᴍᴀɴᴅs ─┐
• /start – sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ ᴀɴᴅ ᴠɪᴇᴡ ᴡᴇʜᴄᴏᴍᴇ ᴍᴇssᴀɢᴇ  
• /help – sʜᴏᴡ ᴛʜɪs ʜᴇʟᴘ ɢᴜɪᴅᴇ   
• /id – ɢᴇᴛ ʏᴏᴜʀ ɪᴅ
• /settings - ᴄᴏɴꜰɪɢᴜʀᴇ ʙᴏᴛ ꜱᴇᴛᴛɪɴɢꜱ

┌─ ᴀᴅᴍɪɴ ᴄᴏᴍᴍᴀɴᴅs ─┐
• /gen_link <channel_link/id> – ɢᴇɴᴇʀᴀᴛᴇ ᴀ ᴘᴇʀᴍᴀɴᴇɴᴛ ʙᴏᴛ ʟɪɴᴋ �ᴡɪᴛʜ ᴀ 5-ᴍɪɴᴜᴛᴇ ᴛᴇᴍᴘᴏʀᴀʀʏ ɪɴᴠɪᴛᴇ  
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
• /demote – ʀᴇᴠᴏᴋᴇ ᴀᴅᴍɪɴ ʀɪɢʜᴛs ꜰʀᴏᴍ ᴀ �ᴜsᴇʀ  
• /ban – ʙᴀɴ ᴀ �ᴜsᴇʀ ꜰʀᴏᴍ ᴜsɪɴɢ ᴛʜᴇ ʙᴏᴛ  
• /unban – ᴜɴʙᴀɴ ᴀ ᴜsᴇʀ  
• /restart – ʀᴇsᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ  
• /broadcast – sᴇɴᴅ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ᴀʟʟ ᴜsᴇʀs  
• /update - ᴜᴘᴅᴀᴛᴇ ʙᴏᴛ ꜰʀᴏᴍ ɢɪᴛʜᴜʙ""",
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

def save_settings(settings):
    """Save settings to JSON file."""
    with open(SETTINGS_STORAGE, 'w') as f:
        json.dump(settings, f, indent=2)

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
        data = load_data()
        
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
        
        save_data(data)
        
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
        data = load_data()
        
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
            
            save_data(data)
            logger.info(f"✅ Auto-regenerated link for {channel_name}")
            
            # Schedule next regeneration
            asyncio.create_task(regenerate_channel_link(context, channel_id, channel_name, file_id))
                
    except Exception as e:
        logger.error(f"Error regenerating link for {channel_id}: {e}")

async def get_active_link(file_id):
    """Get active link for a file_id, regenerating if expired."""
    data = load_data()
    
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
            [InlineKeyboardButton("Click here to join now", url=new_invite_link)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"Join the channel '{channel_name}' by clicking the button below:",
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

1. ɪғ ʙᴏᴛ ɪs ɴᴏᴛ ᴡᴏʀᴋɪɴɢ, ᴇɴsᴜʀᴇ ɪᴛ ɪs ᴀᴅᴍɪɴ ɪɴ ᴛᴀʀɢᴇᴛ ᴄʜᴀɴɴᴇʟs.  
2. ᴠᴇʀɪғʏ ʙᴏᴛ ʜᴀs ᴘᴇʀᴍɪssɪᴏɴ ᴛᴏ ᴄʀᴇᴀᴛᴇ ɪɴᴠɪᴛᴇ ʟɪɴᴋs.  
3. ᴜsᴇ ᴄʜᴀɴɴᴇʟ ɪᴅ ɪɴsᴛᴇᴀᴅ ᴏғ ᴄʜᴀɴɴᴇʟ ʟɪɴᴋ 
4. ᴄʜᴇᴄᴋ ɪɴᴛᴇʀɴᴇᴛ ᴄᴏɴɴᴇᴄᴛɪᴏɴ ɪғ ʙᴏᴛ ғᴀɪʟs ᴛᴏ ʀᴇsᴘᴏɴᴅ.  
5. ᴜsᴇ /debug <channel_link/id> ᴛᴏ ᴄʜᴇᴄᴋ ᴘᴇʀᴍɪssɪᴏɴ ɪssᴜᴇs.  

ғᴏʀ ғᴜʀᴛʜᴇʀ ᴀssɪsᴛᴀɴᴄᴇ, ᴄᴏɴᴛᴀᴄᴛ [ᴏᴡɴᴇʀ](https://t.me/Quarel7)."""
        
        keyboard = [
            [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="back_help"),
            InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=troubleshoot_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
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
        settings = load_settings()
        
        # Remove the button
        row_idx = button_index // 10
        col_idx = button_index % 10
        
        if row_idx < len(settings["start"]["buttons"]):
            if col_idx < len(settings["start"]["buttons"][row_idx]):
                del settings["start"]["buttons"][row_idx][col_idx]
                
                # Remove empty rows
                settings["start"]["buttons"] = [row for row in settings["start"]["buttons"] if row]
                
                save_settings(settings)
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
        settings = load_settings()
        
        # Remove the button
        row_idx = button_index // 10
        col_idx = button_index % 10
        
        if row_idx < len(settings["help"]["buttons"]):
            if col_idx < len(settings["help"]["buttons"][row_idx]):
                del settings["help"]["buttons"][row_idx][col_idx]
                
                # Remove empty rows
                settings["help"]["buttons"] = [row for row in settings["help"]["buttons"] if row]
                
                save_settings(settings)
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
    
    settings = load_settings()
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
    settings = load_settings()
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
    
    settings = load_settings()
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
    
    settings = load_settings()
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
    
    settings = load_settings()
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
    
    save_settings(settings)
    return ConversationHandler.END

async def settings_image_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle image settings updates."""
    user_id = update.effective_user.id
    if not is_owner(user_id):
        return
    
    if not update.message.photo:
        await update.message.reply_text("Please send an image.")
        return
    
    settings = load_settings()
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
    
    save_settings(settings)
    return ConversationHandler.END

async def settings_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button settings updates."""
    user_id = update.effective_user.id
    if not is_owner(user_id):
        return
    
    button_text = update.message.text
    settings = load_settings()
    
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
        
        save_settings(settings)
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
        # Check if this is a deep link
        if context.args:
            file_id = context.args[0]
            data = load_data()
            
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
                    save_data(data)
                    
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
                f"Note: This invite link expires in 5 minutes. If it expires, just click the post link again to get a new one.",
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
        data = load_data()
        
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
        
        save_data(data)
        
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
        data = load_data()
        
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
                keyboard.append([InlineKeyboardButton("⬅️ Previous", callback_data=f"list_channels_{page-1}")])
            if page < total_pages:
                if keyboard:
                    keyboard[0].append(InlineKeyboardButton("Next ➡️", callback_data=f"list_channels_{page+1}"))
                else:
                    keyboard.append([InlineKeyboardButton("Next ➡️", callback_data=f"list_channels_{page+1}")])
        
        keyboard.append([InlineKeyboardButton(f"Page {page}/{total_pages}", callback_data="page_info")])
        keyboard.append([InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(message, reply_markup=reply_markup)
                
    except Exception as e:
        logger.error(f"Error listing channels: {e}")
        await update.message.reply_text(f"Error retrieving channel list: {str(e)}")

async def list_channels_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle list channels pagination callbacks."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith("list_channels_"):
        page = int(data.split("_")[2])
        context.args = [str(page)]
        await list_channels(update, context)
        await query.delete_message()

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
    
    if not is_admin(user_id):
        await update.message.reply_text("You are not authorized to use this bot.")
        return
    
    troubleshoot_text = """✦ ᴛʀᴏᴜʙʟᴇsʜᴏᴏᴛ

1. ɪғ ʙᴏᴛ ɪs ɴᴏᴛ ᴡᴏʀᴋɪɴɢ, ᴇɴsᴜʀᴇ ɪᴛ ɪs ᴀᴅᴍɪɴ ɪɴ ᴛᴀʀɢᴇᴛ ᴄʜᴀɴɴᴇʟs.  
2. ᴠᴇʀɪғʏ ʙᴏᴛ ʜᴀs ᴘᴇʀᴍɪssɪᴏɴ ᴛᴏ ᴄʀᴇᴀᴛᴇ ɪɴᴠɪᴛᴇ ʟɪɴᴋs.  
3. ᴜsᴇ ᴄʜᴀɴɴᴇʟ ɪᴅ ɪɴsᴛᴇᴀᴅ ᴏғ ᴄʜᴀɴɴᴇʟ ʟɪɴᴋ 
4. ᴄʜᴇᴄᴋ ɪɴᴛᴇʀɴᴇᴛ ᴄᴏɴɴᴇᴄᴛɪᴏɴ ɪғ ʙᴏᴛ ғᴀɪʟs ᴛᴏ ʀᴇsᴘᴏɴᴅ.  
5. ᴜsᴇ /debug <channel_link/id> ᴛᴏ ᴄʜᴇᴄᴋ ᴘᴇʀᴍɪssɪᴏɴ ɪssᴜᴇs.  

ғᴏʀ ғᴜʀᴛʜᴇʀ ᴀssɪsᴛᴀɴᴄᴇ, ᴄᴏɴᴛᴀᴄᴛ [ᴏᴡɴᴇʀ](https://t.me/Quarel7)."""
    
    keyboard = [
        [InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(troubleshoot_text, reply_markup=reply_markup, parse_mode="Markdown")

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
    
    data = load_data()
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
    
    data = load_data()
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
        
        data = load_data()
        
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
        
        save_data(data)
        
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
        
        data = load_data()
        
        if "users" in data and str(user_id) in data["users"]:
            del data["users"][str(user_id)]
            save_data(data)
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
            data = load_data()
            if "admins" not in data:
                data["admins"] = []
            
            if user_id not in data["admins"]:
                data["admins"].append(user_id)
                save_data(data)
            
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
            data = load_data()
            if "admins" in data and user_id in data["admins"]:
                data["admins"].remove(user_id)
                save_data(data)
            
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
        
        data = load_data()
        
        # Initialize banned users list if it doesn't exist
        if "banned_users" not in data:
            data["banned_users"] = []
        
        if user_id not in data["banned_users"]:
            data["banned_users"].append(user_id)
            save_data(data)
            
            # Also remove from admins and authorized users if present
            if user_id in ADMIN_IDS and user_id != OWNER_ID:
                ADMIN_IDS.remove(user_id)
            
            if "admins" in data and user_id in data["admins"]:
                data["admins"].remove(user_id)
            
            if "users" in data and str(user_id) in data["users"]:
                del data["users"][str(user_id)]
            
            save_data(data)
            
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
        
        data = load_data()
        
        if "banned_users" in data and user_id in data["banned_users"]:
            data["banned_users"].remove(user_id)
            save_data(data)
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
    
    await update.message.reply_text("Restarting bot...")
    
    # Save current state
    data = load_data()
    data["restart"] = {
        "chat_id": update.effective_chat.id,
        "message_id": update.effective_message.message_id,
        "time": datetime.utcnow().isoformat()
    }
    save_data(data)
    
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
    data = load_data()
    
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
            await context.bot.send_message(user_id, f"📢 Broadcast:\n\n{message_text}")
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to send broadcast to {user_id}: {e}")
            fail_count += 1
    
    await update.message.reply_text(
        f"Broadcast completed.\nSuccess: {success_count}\nFailed: {fail_count}"
    )

async def update_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update the bot from GitHub."""
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    status_msg = await update.message.reply_text("𖡡 ᴩᴜʟʟɪɴɢ ʟᴀᴛᴇꜱᴛ ᴜᴩᴅᴀᴛᴇ ꜰʀᴏᴍ ɢɪᴛʜᴜʙ...")
    
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

# Main Application
def main():
    """Start the bot."""
    # Load admin IDs from data file for persistence
    data = load_data()
    if "admins" in data:
        for admin_id in data["admins"]:
            if admin_id not in ADMIN_IDS:
                ADMIN_IDS.append(admin_id)
    
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

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
    
    # Button handlers
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^(about|help_requirements|help_how|help_troubleshoot|back_start|back_help|close|settings_main|settings_start|settings_start_text|settings_start_image|settings_start_buttons|settings_start_add_button|settings_start_remove_button|settings_help|settings_help_text|settings_help_image|settings_help_buttons|settings_help_add_button|settings_help_remove_button|remove_button_confirm_.*|remove_help_button_confirm_.*|remove_button_cancel_.*|remove_help_button_cancel_.*)$"))
    
    # List channels pagination
    application.add_handler(CallbackQueryHandler(list_channels_callback, pattern="^list_channels_"))
    
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
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Initialize and run
    async def run():
        logger.info("Bot started successfully!")
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        
        # Check if we need to send restart confirmation
        data = load_data()
        if "restart" in data:
            restart_data = data["restart"]
            try:
                await application.bot.edit_message_text(
                    chat_id=restart_data["chat_id"],
                    message_id=restart_data["message_id"],
                    text="✅ ʙᴏᴛ ʀᴇꜱᴛᴀʀᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟy!"
                )
            except:
                pass
            
            # Remove restart data
            del data["restart"]
            save_data(data)
        
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






