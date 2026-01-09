# settings.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
import json
import logging
from database.operations import SettingsOperations
from utils.helpers import is_owner
from config import *

logger = logging.getLogger(__name__)

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Settings command handler."""
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    await show_settings_menu(update, context)

async def show_settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show settings main menu."""
    query = update.callback_query
    
    # Get current settings
    settings = SettingsOperations.get_settings()
    start_settings = settings.get("start", {})
    help_settings = settings.get("help", {})
    
    # Prepare menu text
    text = "⚙️ **Bot Settings**\n\n"
    text += f"• Start Image: {'✅ Set' if start_settings.get('image') else '❌ Not Set'}\n"
    text += f"• Start Text: {'✅ Set' if start_settings.get('text') else '❌ Not Set'}\n"
    text += f"• Start Buttons: {'✅ Set' if start_settings.get('buttons') else '❌ Not Set'}\n"
    text += f"• Help Image: {'✅ Set' if help_settings.get('image') else '❌ Not Set'}\n"
    text += f"• Help Text: {'✅ Set' if help_settings.get('text') else '❌ Not Set'}\n"
    text += f"• Help Buttons: {'✅ Set' if help_settings.get('buttons') else '❌ Not Set'}\n"
    
    # Create menu buttons
    keyboard = [
        [
            InlineKeyboardButton("🖼️ Start Image", callback_data="settings_start_img"),
            InlineKeyboardButton("📝 Start Text", callback_data="settings_start_text")
        ],
        [
            InlineKeyboardButton("🔘 Start Buttons", callback_data="settings_start_buttons"),
            InlineKeyboardButton("🖼️ Help Image", callback_data="settings_help_img")
        ],
        [
            InlineKeyboardButton("📝 Help Text", callback_data="settings_help_text"),
            InlineKeyboardButton("🔘 Help Buttons", callback_data="settings_help_buttons")
        ],
        [
            InlineKeyboardButton("❌ Close", callback_data="settings_close")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        try:
            await query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        except:
            await query.edit_message_caption(
                caption=text,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
    else:
        await update.message.reply_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

async def settings_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle settings button callbacks."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if not is_owner(query.from_user.id):
        await query.answer("You are not authorized!", show_alert=True)
        return
    
    # START IMAGE
    if data == "settings_start_img":
        await query.edit_message_text(
            "🖼️ **Start Image Settings**\n\n"
            "Please send me the image you want to use for the /start command.\n\n"
            "Send /cancel to go back.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Back", callback_data="settings_back")]
            ])
        )
        context.user_data['waiting_for'] = 'start_image'
    
    # HELP IMAGE
    elif data == "settings_help_img":
        await query.edit_message_text(
            "🖼️ **Help Image Settings**\n\n"
            "Please send me the image you want to use for the /help command.\n\n"
            "Send /cancel to go back.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Back", callback_data="settings_back")]
            ])
        )
        context.user_data['waiting_for'] = 'help_image'
    
    # START TEXT
    elif data == "settings_start_text":
        await query.edit_message_text(
            "📝 **Start Text Settings**\n\n"
            "Please send me the new text for the /start command.\n\n"
            "Send /cancel to go back.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Back", callback_data="settings_back")]
            ])
        )
        context.user_data['waiting_for'] = 'start_text'
    
    # HELP TEXT
    elif data == "settings_help_text":
        await query.edit_message_text(
            "📝 **Help Text Settings**\n\n"
            "Please send me the new text for the /help command.\n\n"
            "Send /cancel to go back.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Back", callback_data="settings_back")]
            ])
        )
        context.user_data['waiting_for'] = 'help_text'
    
    # START BUTTONS
    elif data == "settings_start_buttons":
        await show_start_buttons_menu(query, context)
    
    # HELP BUTTONS
    elif data == "settings_help_buttons":
        await show_help_buttons_menu(query, context)
    
    # ADD START BUTTON
    elif data == "settings_start_add_button":
        await query.edit_message_text(
            "🔘 **Add Start Button**\n\n"
            "Please send button configuration in this format:\n\n"
            "**Single button per line:**\n"
            "Button Text - https://example.com\n\n"
            "**Multiple buttons in one row (separated by |):**\n"
            "Button 1 - https://example1.com | Button 2 - https://example2.com\n\n"
            "**Callback buttons (for navigation):**\n"
            "Back - callback:back_start | Close - callback:close\n\n"
            "Send /cancel to go back.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Back", callback_data="settings_start_buttons")]
            ]),
            parse_mode="Markdown"
        )
        context.user_data['waiting_for'] = 'start_button'
    
    # ADD HELP BUTTON
    elif data == "settings_help_add_button":
        await query.edit_message_text(
            "🔘 **Add Help Button**\n\n"
            "Please send button configuration in this format:\n\n"
            "**Single button per line:**\n"
            "Button Text - https://example.com\n\n"
            "**Multiple buttons in one row (separated by |):**\n"
            "Button 1 - https://example1.com | Button 2 - https://example2.com\n\n"
            "**Callback buttons (for navigation):**\n"
            "Back - callback:back_help | Close - callback:close\n\n"
            "Send /cancel to go back.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Back", callback_data="settings_help_buttons")]
            ]),
            parse_mode="Markdown"
        )
        context.user_data['waiting_for'] = 'help_button'
    
    # REMOVE START BUTTON
    elif data == "settings_start_remove_button":
        await show_remove_start_buttons(query, context)
    
    # REMOVE HELP BUTTON
    elif data == "settings_help_remove_button":
        await show_remove_help_buttons(query, context)
    
    # REMOVE BUTTON CONFIRMATION
    elif data.startswith("remove_button_confirm_"):
        button_index = int(data.split("_")[-1])
        settings = SettingsOperations.get_settings()
        start_settings = settings.get("start", {})
        
        # Parse buttons
        buttons = start_settings.get("buttons", [])
        if isinstance(buttons, str):
            buttons = json.loads(buttons)
        
        # Remove the button
        if 0 <= button_index < len(buttons):
            del buttons[button_index]
            
            # Update settings
            start_settings["buttons"] = buttons
            SettingsOperations.update_settings("start", start_settings)
            
            await query.answer("✅ Button removed successfully!", show_alert=True)
            await show_remove_start_buttons(query, context)
    
    # REMOVE HELP BUTTON CONFIRMATION
    elif data.startswith("remove_help_button_confirm_"):
        button_index = int(data.split("_")[-1])
        settings = SettingsOperations.get_settings()
        help_settings = settings.get("help", {})
        
        # Parse buttons
        buttons = help_settings.get("buttons", [])
        if isinstance(buttons, str):
            buttons = json.loads(buttons)
        
        # Remove the button
        if 0 <= button_index < len(buttons):
            del buttons[button_index]
            
            # Update settings
            help_settings["buttons"] = buttons
            SettingsOperations.update_settings("help", help_settings)
            
            await query.answer("✅ Help button removed successfully!", show_alert=True)
            await show_remove_help_buttons(query, context)
    
    # REMOVE BUTTON CANCEL
    elif data.startswith("remove_button_cancel_"):
        await show_start_buttons_menu(query, context)
    
    # REMOVE HELP BUTTON CANCEL
    elif data.startswith("remove_help_button_cancel_"):
        await show_help_buttons_menu(query, context)
    
    # BACK TO SETTINGS
    elif data == "settings_back":
        context.user_data.pop('waiting_for', None)
        await show_settings_menu(update, context)
    
    # CLOSE SETTINGS
    elif data == "settings_close":
        try:
            await query.delete_message()
        except:
            await query.edit_message_text("✅ Settings closed")
    
    # BACK TO START BUTTONS MENU
    elif data == "settings_start_buttons_back":
        await show_start_buttons_menu(query, context)
    
    # BACK TO HELP BUTTONS MENU
    elif data == "settings_help_buttons_back":
        await show_help_buttons_menu(query, context)

async def show_start_buttons_menu(query, context):
    """Show start buttons menu."""
    settings = SettingsOperations.get_settings()
    start_settings = settings.get("start", {})
    
    # Parse buttons
    buttons = start_settings.get("buttons", [])
    if isinstance(buttons, str):
        buttons = json.loads(buttons)
    
    text = "🔘 **Start Buttons Settings**\n\n"
    
    if buttons:
        text += "Current buttons:\n"
        for i, row in enumerate(buttons):
            text += f"\nRow {i + 1}: "
            for j, button in enumerate(row):
                text += f"'{button.get('text', 'No text')}'"
                if j < len(row) - 1:
                    text += ", "
    else:
        text += "No buttons configured yet."
    
    keyboard = [
        [
            InlineKeyboardButton("➕ Add Button", callback_data="settings_start_add_button"),
            InlineKeyboardButton("➖ Remove Button", callback_data="settings_start_remove_button")
        ],
        [
            InlineKeyboardButton("◀️ Back", callback_data="settings_back"),
            InlineKeyboardButton("❌ Close", callback_data="settings_close")
        ]
    ]
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_help_buttons_menu(query, context):
    """Show help buttons menu."""
    settings = SettingsOperations.get_settings()
    help_settings = settings.get("help", {})
    
    # Parse buttons
    buttons = help_settings.get("buttons", [])
    if isinstance(buttons, str):
        buttons = json.loads(buttons)
    
    text = "🔘 **Help Buttons Settings**\n\n"
    
    if buttons:
        text += "Current buttons:\n"
        for i, row in enumerate(buttons):
            text += f"\nRow {i + 1}: "
            for j, button in enumerate(row):
                text += f"'{button.get('text', 'No text')}'"
                if j < len(row) - 1:
                    text += ", "
    else:
        text += "No buttons configured yet."
    
    keyboard = [
        [
            InlineKeyboardButton("➕ Add Button", callback_data="settings_help_add_button"),
            InlineKeyboardButton("➖ Remove Button", callback_data="settings_help_remove_button")
        ],
        [
            InlineKeyboardButton("◀️ Back", callback_data="settings_back"),
            InlineKeyboardButton("❌ Close", callback_data="settings_close")
        ]
    ]
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_remove_start_buttons(query, context):
    """Show remove start buttons menu."""
    settings = SettingsOperations.get_settings()
    start_settings = settings.get("start", {})
    
    # Parse buttons
    buttons = start_settings.get("buttons", [])
    if isinstance(buttons, str):
        buttons = json.loads(buttons)
    
    if not buttons:
        await query.answer("No buttons to remove!", show_alert=True)
        await show_start_buttons_menu(query, context)
        return
    
    text = "➖ **Remove Start Buttons**\n\n"
    text += "Select a button to remove:\n\n"
    
    keyboard = []
    for i, row in enumerate(buttons):
        for j, button in enumerate(row):
            text += f"{i * len(row) + j + 1}. {button.get('text', 'No text')}\n"
            keyboard.append([
                InlineKeyboardButton(
                    f"Remove: {button.get('text', 'No text')}",
                    callback_data=f"remove_button_confirm_{i * len(row) + j}"
                )
            ])
    
    keyboard.append([
        InlineKeyboardButton("◀️ Back", callback_data="settings_start_buttons_back"),
        InlineKeyboardButton("❌ Close", callback_data="settings_close")
    ])
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_remove_help_buttons(query, context):
    """Show remove help buttons menu."""
    settings = SettingsOperations.get_settings()
    help_settings = settings.get("help", {})
    
    # Parse buttons
    buttons = help_settings.get("buttons", [])
    if isinstance(buttons, str):
        buttons = json.loads(buttons)
    
    if not buttons:
        await query.answer("No buttons to remove!", show_alert=True)
        await show_help_buttons_menu(query, context)
        return
    
    text = "➖ **Remove Help Buttons**\n\n"
    text += "Select a button to remove:\n\n"
    
    keyboard = []
    for i, row in enumerate(buttons):
        for j, button in enumerate(row):
            text += f"{i * len(row) + j + 1}. {button.get('text', 'No text')}\n"
            keyboard.append([
                InlineKeyboardButton(
                    f"Remove: {button.get('text', 'No text')}",
                    callback_data=f"remove_help_button_confirm_{i * len(row) + j}"
                )
            ])
    
    keyboard.append([
        InlineKeyboardButton("◀️ Back", callback_data="settings_help_buttons_back"),
        InlineKeyboardButton("❌ Close", callback_data="settings_close")
    ])
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def settings_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle settings messages (text/images)."""
    if not is_owner(update.effective_user.id):
        return
    
    waiting_for = context.user_data.get('waiting_for')
    
    if not waiting_for:
        return
    
    settings = SettingsOperations.get_settings()
    
    # Handle image uploads
    if waiting_for in ['start_image', 'help_image']:
        if update.message.photo:
            # Get the largest photo
            photo = update.message.photo[-1]
            file_id = photo.file_id
            
            # Update settings
            if waiting_for == 'start_image':
                start_settings = settings.get("start", {})
                start_settings["image"] = file_id
                SettingsOperations.update_settings("start", start_settings)
                success_message = "✅ Start image updated successfully!"
            else:  # help_image
                help_settings = settings.get("help", {})
                help_settings["image"] = file_id
                SettingsOperations.update_settings("help", help_settings)
                success_message = "✅ Help image updated successfully!"
            
            # Clear waiting state
            context.user_data.pop('waiting_for', None)
            
            # Send success message
            await update.message.reply_text(
                success_message,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Back to Settings", callback_data="settings_back")]
                ])
            )
        else:
            await update.message.reply_text("❌ Please send a valid image!")
    
    # Handle text updates
    elif waiting_for in ['start_text', 'help_text']:
        new_text = update.message.text
        
        # Update settings
        if waiting_for == 'start_text':
            start_settings = settings.get("start", {})
            start_settings["text"] = new_text
            SettingsOperations.update_settings("start", start_settings)
            success_message = "✅ Start text updated successfully!"
        else:  # help_text
            help_settings = settings.get("help", {})
            help_settings["text"] = new_text
            SettingsOperations.update_settings("help", help_settings)
            success_message = "✅ Help text updated successfully!"
        
        # Clear waiting state
        context.user_data.pop('waiting_for', None)
        
        # Send success message
        await update.message.reply_text(
            success_message,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Back to Settings", callback_data="settings_back")]
            ])
        )
    
    # Handle button configuration
    elif waiting_for in ['start_button', 'help_button']:
        button_text = update.message.text
        
        try:
            # Parse button configuration
            buttons = []
            rows = button_text.split('\n')
            
            for row in rows:
                row = row.strip()
                if not row:
                    continue
                    
                row_buttons = []
                button_configs = row.split('|')
                
                for config in button_configs:
                    config = config.strip()
                    if ' - ' in config:
                        text, url = config.split(' - ', 1)
                        text = text.strip()
                        url = url.strip()
                        
                        # Handle callback buttons
                        if url.lower() in ['callback:back_start', 'callback:back_help', 'callback:close']:
                            url = url.lower()
                        
                        row_buttons.append({"text": text, "url": url})
                
                if row_buttons:
                    buttons.append(row_buttons)
            
            # Update settings
            if waiting_for == 'start_button':
                start_settings = settings.get("start", {})
                start_settings["buttons"] = buttons
                SettingsOperations.update_settings("start", start_settings)
                success_message = "✅ Start buttons updated successfully!"
                back_callback = "settings_start_buttons"
            else:  # help_button
                help_settings = settings.get("help", {})
                help_settings["buttons"] = buttons
                SettingsOperations.update_settings("help", help_settings)
                success_message = "✅ Help buttons updated successfully!"
                back_callback = "settings_help_buttons"
            
            # Clear waiting state
            context.user_data.pop('waiting_for', None)
            
            # Send success message
            await update.message.reply_text(
                success_message,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Back", callback_data=back_callback)]
                ])
            )
            
        except Exception as e:
            logger.error(f"Error parsing button configuration: {str(e)}")
            await update.message.reply_text(
                f"❌ Error parsing button configuration!\n\n"
                f"Please use the correct format:\n"
                f"Button Text - URL\n"
                f"Multiple buttons: Button1 - URL1 | Button2 - URL2",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Back", 
                     callback_data="settings_start_buttons" if waiting_for == 'start_button' else "settings_help_buttons")]
                ])
            )

# Settings conversation handler
settings_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("settings", settings_command)],
    states={
        # Message handlers for text and images
        "WAITING_FOR_INPUT": [
            MessageHandler(filters.PHOTO, settings_message_handler),
            MessageHandler(filters.TEXT & ~filters.COMMAND, settings_message_handler),
        ]
    },
    fallbacks=[
        CommandHandler("cancel", lambda update, context: show_settings_menu(update, context)),
        CallbackQueryHandler(settings_button_handler, pattern="^settings_back$"),
    ],
    allow_reentry=True
)

# Register callback query handler for settings buttons
settings_callback_handler = CallbackQueryHandler(
    settings_button_handler, 
    pattern="^(settings_|remove_button_|remove_help_button_)"
)

