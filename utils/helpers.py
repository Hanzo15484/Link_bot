import re
import base64
import asyncio
import random
import time
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import logging
from config import OWNER_ID
from database.operations import UserOperations

logger = logging.getLogger(__name__)

def is_admin(user_id):
    """Check if user is an admin."""
    return UserOperations.is_admin(user_id)

def is_owner(user_id):
    """Check if user is the owner."""
    return user_id == OWNER_ID

def to_small_caps(text: str) -> str:
    """Convert text to small caps."""
    small_caps_map = {
        "a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ", "e": "ᴇ", "f": "ғ", "g": "ɢ",
        "h": "ʜ", "i": "ɪ", "j": "ᴊ", "k": "ᴋ", "l": "ʟ", "m": "ᴍ", "n": "ɴ",
        "o": "ᴏ", "p": "ᴘ", "q": "ǫ", "r": "ʀ", "s": "s", "t": "ᴛ", "u": "ᴜ",
        "v": "ᴠ", "w": "ᴡ", "x": "x", "y": "ʏ", "z": "ᴢ"
    }
    return "".join(small_caps_map.get(ch.lower(), ch) for ch in text)

async def add_temporary_reaction(update):
    """Add a temporary reaction to message."""
    reactions = ["🎉", "😎", "🥰", "⚡", "❤‍🔥", "🤩"]
    reaction = random.choice(reactions)
    try:
        await update.message.set_reaction(reaction)
    except:
        pass

async def cleanup_message(context, chat_id, message_id, delay=180):
    """Clean up message after timeout."""
    await asyncio.sleep(delay)
    try:
        await context.bot.delete_message(chat_id, message_id)
        logger.info(f"Message {message_id} cleaned up")
    except Exception as e:
        logger.error(f"Error deleting message: {e}")

def generate_file_id(channel_id):
    """Generate a unique file ID for a channel."""
    unique_string = f"{channel_id}_permanent"
    return base64.urlsafe_b64encode(unique_string.encode()).decode('utf-8').replace('=', '')

async def extract_channel_info(context, input_str):
    """Extract channel info from input and verify bot is admin."""
    try:
        chat = None
        logger.info(f"Extracting channel info from: {input_str}")
        
        cleaned_input = input_str.strip()
        formats_to_try = []
        
        # Different input formats
        if cleaned_input.startswith('-100') and cleaned_input[1:].isdigit():
            formats_to_try.append(cleaned_input)
        elif cleaned_input.replace('@', '').replace('-', '').isalnum():
            if not cleaned_input.startswith('@'):
                formats_to_try.append(f"@{cleaned_input}")
            formats_to_try.append(cleaned_input)
        elif 't.me/' in cleaned_input:
            if 't.me/+' in cleaned_input:
                match = re.search(r't\.me/\+(.+)', cleaned_input)
                if match:
                    formats_to_try.append(f"+{match.group(1)}")
            else:
                match = re.search(r't\.me/([a-zA-Z0-9_]+)', cleaned_input)
                if match:
                    formats_to_try.append(f"@{match.group(1)}")
        
        formats_to_try.append(cleaned_input)
        
        logger.info(f"Trying formats: {formats_to_try}")
        
        for format_to_try in formats_to_try:
            try:
                chat = await context.bot.get_chat(format_to_try)
                logger.info(f"Successfully got chat: {chat.title} ({chat.id})")
                break
            except Exception:
                continue
        
        if not chat:
            logger.error("All format attempts failed")
            return None
            
        # Verify bot is admin
        try:
            admins = await context.bot.get_chat_administrators(chat.id)
            bot_id = (await context.bot.get_me()).id
            
            bot_admin = next((admin for admin in admins if admin.user.id == bot_id), None)
            
            if not bot_admin:
                logger.error(f"❌ Bot is NOT admin in {chat.title}")
                return None
            
            # Check permissions
            can_invite = False
            if hasattr(bot_admin, 'can_invite_users'):
                can_invite = bot_admin.can_invite_users
            elif hasattr(bot_admin, 'permissions') and hasattr(bot_admin.permissions, 'can_invite_users'):
                can_invite = bot_admin.permissions.can_invite_users
            
            if not can_invite:
                logger.error(f"❌ Bot cannot create invite links in {chat.title}")
                try:
                    test_link = await context.bot.create_chat_invite_link(
                        chat_id=chat.id,
                        expire_date=datetime.utcnow() + timedelta(minutes=5),
                        creates_join_request=False
                    )
                    logger.info(f"✅ Actually can create links despite permission check")
                    can_invite = True
                except Exception:
                    logger.error(f"❌ Confirmed cannot create links")
                    return None
                
            logger.info(f"✅ Bot verified as admin with invite permissions in {chat.title}")
            return str(chat.id), chat.title, chat
            
        except Exception as e:
            logger.error(f"Error checking admin status: {e}")
            # Try direct link creation
            try:
                test_link = await context.bot.create_chat_invite_link(
                    chat_id=chat.id,
                    expire_date=datetime.utcnow() + timedelta(seconds=60),
                    creates_join_request=False
                )
                logger.info(f"✅ Can create links directly")
                return str(chat.id), chat.title, chat
            except Exception:
                logger.error(f"❌ Cannot create links")
                return None
            
    except Exception as e:
        logger.error(f"Error in extract_channel_info: {e}")
        return None

def get_wait_image():
    """Get wait image file ID."""
    try:
        with open("config.json", "r") as f:
            import json
            data = json.load(f)
            return data.get("wait_image")
    except FileNotFoundError:
        return None

def save_wait_image(file_id):
    """Save wait image file ID."""
    try:
        with open("config.json", "w") as f:
            import json
            json.dump({"wait_image": file_id}, f)
    except Exception as e:
        logger.error(f"Error saving wait image: {e}")
