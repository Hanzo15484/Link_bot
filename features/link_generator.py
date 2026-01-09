from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import asyncio
from datetime import datetime, timedelta
import logging

from config import LINK_DURATION
from database.operations import ChannelOperations, LinkOperations
from utils.helpers import extract_channel_info, generate_file_id

logger = logging.getLogger(__name__)

async def generate_single_link(update, context, channel_input):
    """Generate a link for a single channel."""
    status_msg = await update.message.reply_text("ᴘʀᴏᴄᴇssɪɴɢ...")
    
    try:
        # Extract channel info from the input
        channel_info = await extract_channel_info(context, channel_input)
        if not channel_info:
            await status_msg.edit_text("Invalid channel link or bot is not admin in this channel.\n\nPlease check:\n• Channel link format\n• Bot is admin with invite permissions\n\nTry: /debug @channelname to check permissions")
            return
        
        channel_id, channel_name, chat = channel_info
        
        # Create a permanent file_id for this channel
        file_id = generate_file_id(channel_id)
        
        # Create a 5-minute invite link
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
        
        # Store in database
        ChannelOperations.add_channel(channel_id, channel_name, file_id)
        LinkOperations.add_link(file_id, channel_id, invite_link.invite_link, expiry_date)
        
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
        
        # Update database with new link
        LinkOperations.update_link(file_id, invite_link.invite_link, expiry_date)
        logger.info(f"✅ Auto-regenerated link for {channel_name}")
        
        # Schedule next regeneration
        asyncio.create_task(regenerate_channel_link(context, channel_id, channel_name, file_id))
            
    except Exception as e:
        logger.error(f"Error regenerating link for {channel_id}: {e}")
