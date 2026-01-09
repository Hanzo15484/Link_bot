from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import asyncio
from datetime import datetime, timedelta
import logging

from config import LINK_DURATION, LIST_CHANNELS_PAGE_SIZE
from database.operations import UserOperations, ChannelOperations, LinkOperations, SettingsOperations
from utils.helpers import is_admin, extract_channel_info, generate_file_id
from features.link_generator import generate_single_link, regenerate_channel_link
from time import time

logger = logging.getLogger(__name__)

async def batch_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate links for all channels where bot is admin."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    status_msg = await update.message.reply_text("Fetching all channels...")
    
    try:
        channels = ChannelOperations.get_all_channels()
        
        if not channels:
            await status_msg.edit_text("No channels found in database. Use /gen_link to add channels first.")
            return
        
        count = 0
        bot_username = (await context.bot.get_me()).username
        message = "Generated links for all channels:\n\n"
        
        for channel in channels:
            file_id = channel['file_id']
            link_data = LinkOperations.get_link(file_id)
            
            if link_data:
                expiry_time = link_data['expiry_time']
                
                # If link is expired or about to expire, regenerate it
                if datetime.utcnow() > expiry_time - timedelta(minutes=1):
                    try:
                        new_expiry = datetime.utcnow() + timedelta(seconds=LINK_DURATION)
                        new_invite_link = await context.bot.create_chat_invite_link(
                            chat_id=channel['channel_id'],
                            expire_date=new_expiry,
                            creates_join_request=False
                        )
                        
                        LinkOperations.update_link(file_id, new_invite_link.invite_link, new_expiry)
                        count += 1
                        logger.info(f"Regenerated link for {channel['channel_name']}")
                        
                        bot_link = f"https://t.me/{bot_username}?start={file_id}"
                        message += f"• {channel['channel_name']}: {bot_link}\n"
                    except Exception as e:
                        logger.error(f"Error regenerating link for {channel['channel_name']}: {e}")
                        message += f"• {channel['channel_name']}: Error - {str(e)}\n"
                else:
                    bot_link = f"https://t.me/{bot_username}?start={file_id}"
                    message += f"• {channel['channel_name']}: {bot_link}\n"
                    count += 1
        
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
    """List all active channels."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("You are not authorized to use this bot.")
        return
    
    try:
        channels = ChannelOperations.get_all_channels()
        
        if not channels:
            await update.message.reply_text("No active channels found.\n\nUse /gen_link to create channel links.")
            return
        
        # Get page number
        page = 1
        if context.args and context.args[0].isdigit():
            page = int(context.args[0])
        
        bot_username = (await context.bot.get_me()).username
        total_pages = (len(channels) + LIST_CHANNELS_PAGE_SIZE - 1) // LIST_CHANNELS_PAGE_SIZE
        page = max(1, min(page, total_pages))
        
        start_idx = (page - 1) * LIST_CHANNELS_PAGE_SIZE
        end_idx = min(start_idx + LIST_CHANNELS_PAGE_SIZE, len(channels))
        
        message = f"Active Channels (Page {page}/{total_pages}):\n\n"
        
        for i in range(start_idx, end_idx):
            channel = channels[i]
            file_id = channel['file_id']
            link_data = LinkOperations.get_link(file_id)
            
            if link_data:
                time_left = link_data['expiry_time'] - datetime.utcnow()
                minutes_left = max(0, int(time_left.total_seconds() / 60))
                bot_link = f"https://t.me/{bot_username}?start={file_id}"
                message += f"• {channel['channel_name']}:\n  Link: {bot_link}\n  Expires in: {minutes_left} minutes\n\n"
            else:
                message += f"• {channel['channel_name']}: Link expired or missing\n\n"
        
        message += f"Total: {len(channels)} channels"
        
        # Pagination buttons
        keyboard = []
        if total_pages > 1:
            row = []
            if page > 1:
                row.append(InlineKeyboardButton("《 Previous", callback_data=f"list_channels_{page-1}"))
            if page < total_pages:
                row.append(InlineKeyboardButton("Next 》", callback_data=f"list_channels_{page+1}"))
            if row:
                keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton(f"Page {page}/{total_pages}", callback_data="page_info")])
        keyboard.append([InlineKeyboardButton("Close", callback_data="close")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message, reply_markup=reply_markup)
                
    except Exception as e:
        logger.error(f"Error listing channels: {e}")
        await update.message.reply_text(f"Error retrieving channel list: {str(e)}")

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

1\\. ɪғ ʙᴏᴛ ɪs ɴᴏᴛ ᴡᴏʀᴋɪɴɢ, ᴇɴsᴜʀᴇ ɪᴛ ɪs ᴀᴅᴍɪɴ ɪɴ ᴛᴀʀɢᴇᴛ ᴄʜᴀɴɴᴇʟs\\.    
2\\. ᴠᴇʀɪғʏ ʙᴏᴛ ʜᴀs ᴘᴇʀᴍɪssɪᴏɴ ᴛᴏ ᴄʀᴇᴀᴛᴇ ɪɴᴠɪᴛᴇ ʟɪɴᴋs\\.  
3\\. ᴜsᴇ ᴄʜᴀɴɴᴇʟ ɪᴅ ɪɴsᴛᴇᴀᴅ ᴏғ ᴄʜᴀɴɴᴇʟ ʟɪɴᴋ\\.  
4\\. ᴄʜᴇᴄᴋ ɪɴᴛᴇʀɴᴇᴛ ᴄᴏɴɴᴇᴄᴛɪᴏɴ ɪғ ʙᴏᴛ ғᴀɪʟs ᴛᴏ ʀᴇsᴘᴏɴᴅ\\.  
5\\. ᴜsᴇ /debug \\<channel\\_link/id\\> ᴛᴏ ᴄʜᴇᴄᴋ ᴘᴇʀᴍɪssɪᴏɴ ɪssᴜᴇs\\.  

ғᴏʀ ғᴜʀᴛʜᴇʀ ᴀssɪsᴛᴀɴᴄᴇ\\, ᴄᴏɴᴛᴀᴄᴛ ᴏᴡɴᴇʀ\\."""
    
    keyboard = [[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(troubleshoot_text, reply_markup=reply_markup, parse_mode="MarkdownV2")

async def admins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all bot admins."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("You are not authorized to use this bot.")
        return
    
    admins = UserOperations.get_all_admins()
    
    message = "Bot Admins:\n\n"
    for i, admin in enumerate(admins, 1):
        username = admin.get('username', 'No username')
        first_name = admin.get('first_name', 'Unknown')
        message += f"{i}. {first_name} (@{username}) - {admin['user_id']}\n"
    
    keyboard = [[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user statistics."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("You are not authorized to use this bot.")
        return
    
    total_users = UserOperations.get_user_count()
    admins = UserOperations.get_all_admins()
    banned = UserOperations.get_all_banned()
    
    message = f"""User Statistics:

• Total Users: {total_users}
• Admins: {len(admins)}
• Banned Users: {len(banned)}"""

    keyboard = [[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(message, reply_markup=reply_markup)

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check bot uptime and responsiveness."""
    from config import BOT_START_TIME
    from datetime import timedelta
    
    start_time = time.time()
    
    # Send initial message
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
    except:
        pass

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            f"✅ **Pong!**\n"
            f"📡 Latency: `{latency_ms} ms`\n"
            f"⏱️ Uptime: `{uptime_str}`"
        ),
        parse_mode="Markdown"
    )

async def get_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get bot logs."""
    from config import OWNER_ID, LOG_FILE
    
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    import os
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

        # Send log file
        with open("log.txt", "rb") as f_doc:
            await update.message.reply_document(
                document=f_doc,
                filename="log.txt",
                caption="📄 Log file"
            )
    else:
        await update.message.reply_text("⚠️ Log file not found!")

