import logging
import time
import sys
import os

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes,
    ConversationHandler, MessageHandler, filters
)

from config import BOT_TOKEN, BOT_START_TIME, logger
from database.models import Database

# Import handlers
from handlers.user_handlers import start, help_command, get_id, gen_link
from handlers.admin_handlers import (
    batch_link, list_channels, debug_channel, troubleshoot,
    admins_command, users_command, ping, get_log
)
from handlers.owner_handlers import (
    auth_user, deauth_user, promote_user, demote_user,
    ban_user, unban_user, restart_bot, broadcast_message,
    update_bot, channels
)
# Import maintenance from maintenance_handlers
from handlers.maintenance_handlers import maintenance
from handlers.button_handlers import button_handler, button_handler_channels
from handlers.settings_handlers import settings_conv_handler, settings_command
from handlers.maintenance_handlers import (
    maintenance_callback, alert_callback, custom_alert,
    maintenance_guard, broadcast_cancel_callback
)
from handlers.font_handlers import font_command, font_callback, handle_font_text
from features.smallcaps import smallcaps_handler
from features.forward_handler import forwarded_channel_id

def main():
    """Start the bot."""
    global BOT_START_TIME
    BOT_START_TIME = time.time()
    
    # Initialize database
    db = Database()
    
    # Create the Application
    application = (Application.builder()
        .token(BOT_TOKEN)
        .read_timeout(15)
        .write_timeout(25)  
        .connect_timeout(20)
        .pool_timeout(20)
        .concurrent_updates(True)
        .build()
    )

    # User command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("id", get_id))
    
    # Admin command handlers
    application.add_handler(CommandHandler("gen_link", gen_link))
    application.add_handler(CommandHandler("batch_link", batch_link))
    application.add_handler(CommandHandler("list_channels", list_channels))
    application.add_handler(CommandHandler("debug", debug_channel))
    application.add_handler(CommandHandler("troubleshoot", troubleshoot))
    application.add_handler(CommandHandler("admins", admins_command))
    application.add_handler(CommandHandler("users", users_command))
    application.add_handler(CommandHandler("ping", ping))
    application.add_handler(CommandHandler("log", get_log))
    
    # Owner command handlers
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
    application.add_handler(CommandHandler("maintenance", maintenance))  # Fixed import
    
    # Font command handler
    application.add_handler(CommandHandler("font", font_command))
    
    # Settings handler
    application.add_handler(settings_conv_handler)
    
    # Button handlers
    application.add_handler(CallbackQueryHandler(button_handler, pattern="^(about|help_requirements|help_how|help_troubleshoot|back_start|back_help|close|settings_main|settings_start|settings_start_text|settings_start_image|settings_start_buttons|settings_start_add_button|settings_start_remove_button|settings_help|settings_help_text|settings_help_image|settings_help_buttons|settings_help_add_button|settings_help_remove_button|remove_button_confirm_.*|remove_help_button_confirm_.*|remove_button_cancel_.*|remove_help_button_cancel_.*|list_channels_.*|page_info)$"))
    
    # Channels button handlers
    application.add_handler(CallbackQueryHandler(button_handler_channels, pattern="^(get_channels|get_settings|back_channels|close_channels)$"))
    
    # Maintenance handlers
    application.add_handler(CallbackQueryHandler(maintenance_callback, pattern="^maint_"))
    application.add_handler(CallbackQueryHandler(alert_callback, pattern="^alert_"))
    application.add_handler(CallbackQueryHandler(broadcast_cancel_callback, pattern="broadcast_cancel"))
    
    # Font handlers
    application.add_handler(CallbackQueryHandler(font_callback, pattern="^font_"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_font_text), group=3)
    
    # Message handlers
    application.add_handler(MessageHandler(filters.FORWARDED, forwarded_channel_id))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, smallcaps_handler), group=2)
    
    # Maintenance guard (must be last handler)
    application.add_handler(MessageHandler(filters.COMMAND, maintenance_guard), group=0)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, custom_alert), group=1)
    
    # Start the bot
    logger.info("Bot started successfully!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
