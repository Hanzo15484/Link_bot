from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import asyncio
from datetime import datetime, timedelta
import base64

from config import LINK_DURATION
from database.operations import UserOperations, ChannelOperations, LinkOperations, SettingsOperations
from utils.helpers import is_admin, is_owner, add_temporary_reaction, cleanup_message, generate_file_id
from features.link_generator import generate_single_link
import logging

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    if update.message.chat.type == "private":
        # Track user
        user = update.effective_user
        UserOperations.add_or_update_user(
            user.id, 
            user.username, 
            user.first_name, 
            user.last_name
        )
        
        # Check if this is a deep link
        if context.args:
            file_id = context.args[0]
            link_data = LinkOperations.get_link(file_id)
            
            if not link_data:
                await update.message.reply_text("Invalid or expired invite link.")
                return
            
            channel_data = ChannelOperations.get_channel(link_data["channel_id"])
            
            # Check if link is expired
            if datetime.utcnow() > link_data["expiry_time"]:
                # Link expired, create a new one
                try:
                    new_expiry = datetime.utcnow() + timedelta(seconds=LINK_DURATION)
                    new_invite_link = await context.bot.create_chat_invite_link(
                        chat_id=link_data["channel_id"],
                        expire_date=new_expiry,
                        creates_join_request=False
                    )
                    
                    # Update database with new link
                    LinkOperations.update_link(file_id, new_invite_link.invite_link, new_expiry)
                    link_data = LinkOperations.get_link(file_id)
                    logger.info(f"Regenerated expired link for {channel_data['channel_name']}")
                except Exception as e:
                    await update.message.reply_text("Error generating new invite link. Please try again.")
                    logger.error(f"Error regenerating link: {e}")
                    return
                    
            await add_temporary_reaction(update)
            wait_msg = await update.message.reply_text("ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ....")
            await asyncio.sleep(0.3)
            await wait_msg.delete()
            
            # Create inline button with the channel link
            keyboard = [
                [InlineKeyboardButton("• ᴄʟɪᴄᴋ ʜᴇʀᴇ ᴛᴏ ᴊᴏɪɴ ɴᴏᴡ •", url=link_data["invite_link"])]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
                
            message = await update.message.reply_text(
                f"ᴊᴏɪɴ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ʙʏ ᴄʟɪᴄᴋɪɴɢ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ:",
                reply_markup=reply_markup
            )
            
            note_message = await update.message.reply_text(
                "> *ɴᴏᴛᴇ\\:* ᴛʜɪs ɪɴᴠɪᴛᴇ ʟɪɴᴋ ᴇxᴘɪʀᴇs ɪɴ 5 ᴍɪɴᴜᴛᴇs\\. ɪғ ɪᴛ ᴇxᴘɪʀᴇs, ᴊᴜsᴛ ᴄʟɪᴄᴋ ᴛʜᴇ ᴘᴏsᴛ ʟɪɴᴋ ᴀɢᴀɪɴ ᴛᴏ ɢᴇᴛ ᴀ ɴᴇᴡ ᴏɴᴇ\\.",
                parse_mode="MarkdownV2"
            )

            # Schedule message cleanup
            asyncio.create_task(cleanup_message(context, update.effective_chat.id, note_message.message_id))
        else:
            # Call start_callback directly (will be defined below)
            await start_callback(update, context)
    else:
        await update.message.reply_text("Please use this bot in private messages.")

async def start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command callback for button navigation."""
    from telegram import InputMediaPhoto
    import json  # Add this import
    
    query = update.callback_query
    if query:
        await query.answer()
        message = query.message
    else:
        message = update.message
    
    settings = SettingsOperations.get_settings()
    start_settings = settings["start"]
    
    # Parse buttons from JSON string if needed
    buttons = start_settings["buttons"]
    if isinstance(buttons, str):
        buttons = json.loads(buttons)
    
    # Create inline keyboard from settings
    keyboard = []
    for row in buttons:
        keyboard_row = []
        for button in row:
            if isinstance(button, dict) and button.get("url", "").startswith("callback:"):
                callback_data = button["url"].replace("callback:", "")
                keyboard_row.append(InlineKeyboardButton(button["text"], callback_data=callback_data))
            elif isinstance(button, dict):
                keyboard_row.append(InlineKeyboardButton(button["text"], url=button["url"]))
        keyboard.append(keyboard_row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send message with image and buttons
    if query:
        try:
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
        await message.reply_text(
            text=start_settings["text"],
            reply_markup=reply_markup
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message with help information."""
    await help_command_callback(update, context)

async def help_command_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command callback for button navigation."""
    from telegram import InputMediaPhoto
    import json  # Add this import
    
    query = update.callback_query
    if query:
        await query.answer()
        message = query.message
    else:
        message = update.message
    
    user_id = update.effective_user.id
    settings = SettingsOperations.get_settings()
    help_settings = settings["help"]
    
    if is_admin(user_id):
        # Parse buttons from JSON string if needed
        buttons = help_settings["buttons"]
        if isinstance(buttons, str):
            buttons = json.loads(buttons)
        
        # Create inline keyboard from settings
        keyboard = []
        for row in buttons:
            keyboard_row = []
            for button in row:
                if isinstance(button, dict) and button.get("url", "").startswith("callback:"):
                    callback_data = button["url"].replace("callback:", "")
                    keyboard_row.append(InlineKeyboardButton(button["text"], callback_data=callback_data))
                elif isinstance(button, dict):
                    keyboard_row.append(InlineKeyboardButton(button["text"], url=button["url"]))
            keyboard.append(keyboard_row)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if query:
            await query.edit_message_text(text=help_settings["text"], reply_markup=reply_markup)
        else:
            await message.reply_text(text=help_settings["text"], reply_markup=reply_markup)
    else:
        # Inline keyboard for non-admins
        keyboard = [
            [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="back_start"), InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        help_text = """This bot generates permanent channel links with temporary invites for admins only.
    Contact the bot administrator for access."""
        if query:
            await query.edit_message_text(help_text, reply_markup=reply_markup)
        else:
            await message.reply_text(help_text, reply_markup=reply_markup)

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get user ID."""
    user_id = update.effective_user.id
    await update.message.reply_text(f"Your ID: `{user_id}`", parse_mode="Markdown")

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

