from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging
import json

from config import SETTINGS_MAIN, SETTINGS_START, SETTINGS_START_TEXT, SETTINGS_START_IMAGE, \
                  SETTINGS_START_BUTTONS, SETTINGS_START_ADD_BUTTON, SETTINGS_START_REMOVE_BUTTON, \
                  SETTINGS_HELP, SETTINGS_HELP_TEXT, SETTINGS_HELP_IMAGE, SETTINGS_HELP_BUTTONS, \
                  SETTINGS_HELP_ADD_BUTTON, SETTINGS_HELP_REMOVE_BUTTON, ABOUT, \
                  HELP_REQUIREMENTS, HELP_HOW, HELP_TROUBLESHOOT
from database.operations import SettingsOperations
from handlers.admin_handlers import list_channels
from utils.helpers import is_owner

logger = logging.getLogger(__name__)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    try:
        if data == "about":
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
            from handlers.user_handlers import start_callback
            await start_callback(update, context)
            return
            
        elif data == "back_help":
            from handlers.user_handlers import help_command_callback
            await help_command_callback(update, context)
            return
            
        elif data == "close":
            try:
                await query.delete_message()
            except:
                pass
            return
        
        # List channels pagination
        elif data.startswith("list_channels_"):
            page = int(data.split("_")[2])
            context.args = [str(page)]
            await list_channels(update, context)
            return
        
        # Page info
        elif data == "page_info":
            await query.answer("You are on the channels list page.", show_alert=True)
            return
            
    except Exception as e:
        logger.error(f"Error in button_handler: {e}")
        try:
            await query.answer(f"Error: {str(e)}", show_alert=True)
        except:
            pass

async def button_handler_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle channels button callbacks."""
    from config import OWNER_ID
    import os
    import tempfile
    
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id != OWNER_ID:
        await query.edit_message_text("❌ You are not authorized to use this bot.")
        return

    try:
        if query.data == "get_channels":
            # Send channels database
            if os.path.exists("data/bot.db"):
                with open("data/bot.db", "rb") as file:
                    await query.message.reply_document(
                        document=file,
                        filename="bot.db",
                        caption="📂 Here is your database file."
                    )
            else:
                await query.message.reply_text("⚠️ Database file not found!")
                
        elif query.data == "get_settings":
            # Send settings as JSON
            settings = SettingsOperations.get_settings()
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
                f.flush()
                with open(f.name, 'rb') as file:
                    await query.message.reply_document(
                        document=file,
                        filename="bot_settings.json",
                        caption="⚙️ Here is your bot settings."
                    )
            os.unlink(f.name)
                
        elif query.data == "close_channels":
            await query.delete_message()
            
    except Exception as e:
        logger.error(f"Error in button_handler_channels: {e}")
        await query.answer(f"Error: {str(e)}", show_alert=True)
