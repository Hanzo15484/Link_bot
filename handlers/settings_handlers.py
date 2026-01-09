from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import json
import logging

from config import *
from database.operations import SettingsOperations
from utils.helpers import is_owner

logger = logging.getLogger(__name__)

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

async def settings_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text settings updates."""
    user_id = update.effective_user.id
    if not is_owner(user_id):
        return
    
    settings = SettingsOperations.get_settings()
    new_text = update.message.text
    
    if context.user_data.get('settings_mode') == 'start_text':
        settings["start"]["text"] = new_text
        SettingsOperations.update_settings("start", settings["start"])
        await update.message.reply_text(
            "✅ Start text updated successfully!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="settings_start"),
                 InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]
            ])
        )
    elif context.user_data.get('settings_mode') == 'help_text':
        settings["help"]["text"] = new_text
        SettingsOperations.update_settings("help", settings["help"])
        await update.message.reply_text(
            "✅ Help text updated successfully!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="settings_help"),
                 InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]
            ])
        )
    
    return ConversationHandler.END

async def settings_image_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle image settings updates."""
    user_id = update.effective_user.id
    if not is_owner(user_id):
        return
    
    if not update.message.photo:
        await update.message.reply_text("Please send an image.")
        return
    
    settings = SettingsOperations.get_settings()
    photo = update.message.photo[-1]
    file_id = photo.file_id
    
    if context.user_data.get('settings_mode') == 'start_image':
        settings["start"]["image"] = file_id
        SettingsOperations.update_settings("start", settings["start"])
        await update.message.reply_text(
            "✅ Start image updated successfully!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="settings_start"),
                 InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]
            ])
        )
    elif context.user_data.get('settings_mode') == 'help_image':
        settings["help"]["image"] = file_id
        SettingsOperations.update_settings("help", settings["help"])
        await update.message.reply_text(
            "✅ Help image updated successfully!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="settings_help"),
                 InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]
            ])
        )
    
    return ConversationHandler.END

async def settings_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button settings updates."""
    user_id = update.effective_user.id
    if not is_owner(user_id):
        return
    
    button_text = update.message.text
    settings = SettingsOperations.get_settings()
    
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
        
        if context.user_data.get('settings_mode') == 'start_button':
            settings["start"]["buttons"] = buttons
            SettingsOperations.update_settings("start", settings["start"])
            await update.message.reply_text(
                "✅ Start buttons updated successfully!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="settings_start_buttons"),
                     InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]
                ])
            )
        elif context.user_data.get('settings_mode') == 'help_button':
            settings["help"]["buttons"] = buttons
            SettingsOperations.update_settings("help", settings["help"])
            await update.message.reply_text(
                "✅ Help buttons updated successfully!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="settings_help_buttons"),
                     InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]
                ])
            )
        
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
        SETTINGS_HELP: [CallbackQueryHandler(settings_start_callback, pattern="^settings_help$")],
        SETTINGS_HELP_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, settings_text_handler)],
        SETTINGS_HELP_IMAGE: [MessageHandler(filters.PHOTO, settings_image_handler)],
        SETTINGS_HELP_BUTTONS: [CallbackQueryHandler(settings_start_buttons_callback, pattern="^settings_help_buttons$")],
        SETTINGS_HELP_ADD_BUTTON: [MessageHandler(filters.TEXT & ~filters.COMMAND, settings_button_handler)],
    },
    fallbacks=[CommandHandler("cancel", lambda update, context: ConversationHandler.END)],
                   )

