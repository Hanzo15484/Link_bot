from telegram import Update
from telegram.ext import ContextTypes
import re
import logging

logger = logging.getLogger(__name__)

async def forwarded_channel_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get channel ID from forwarded message."""
    message = update.message

    if not message:
        return  

    # Restrict only to private chat (DM)
    if message.chat.type != "private":
        return  

    # Check if message is forwarded
    if not message.forward_from_chat:
        await message.reply_text("⚠️ This message is not forwarded from a channel!")
        return

    # Get the forwarded chat info
    forwarded_chat = message.forward_from_chat
    
    if forwarded_chat.type in ["channel", "supergroup"]:
        channel_id = str(forwarded_chat.id)
        channel_title = forwarded_chat.title
        channel_username = forwarded_chat.username
        
        # Create channel link
        if channel_username:
            channel_link = f"https://t.me/{channel_username}"
        else:
            channel_link = f"ID: {channel_id}"
        
        # Escape Markdown characters
        import html
        channel_title_safe = html.escape(channel_title)
        
        response = f"""
📢 <b>Forwarded Channel Info:</b>

🏷️ <b>Title:</b> {channel_title_safe}
🆔 <b>ID:</b> <code>{channel_id}</code>
🔗 <b>Link:</b> {channel_link}
👤 <b>Type:</b> {forwarded_chat.type}
        """
        
        # Add invite link if bot is admin
        try:
            # Check if bot is admin
            admins = await context.bot.get_chat_administrators(forwarded_chat.id)
            bot_id = (await context.bot.get_me()).id
            bot_admin = next((admin for admin in admins if admin.user.id == bot_id), None)
            
            if bot_admin:
                # Create a quick invite link
                expiry_date = datetime.utcnow() + timedelta(minutes=5)
                invite_link = await context.bot.create_chat_invite_link(
                    chat_id=forwarded_chat.id,
                    expire_date=expiry_date,
                    creates_join_request=False
                )
                
                response += f"\n🔗 <b>Quick Invite:</b> {invite_link.invite_link}"
                response += f"\n⏰ <b>Expires:</b> 5 minutes"
        except Exception as e:
            logger.error(f"Could not create invite link: {e}")
            response += f"\n⚠️ <i>Bot is not admin in this channel</i>"
        
        await message.reply_text(response, parse_mode="HTML")
        
        # Also suggest to generate link
        keyboard = [
            [InlineKeyboardButton("📎 Generate Bot Link", callback_data=f"genlink_{channel_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(
            f"Click below to generate a permanent bot link for this channel:",
            reply_markup=reply_markup
        )
    else:
        await message.reply_text("⚠️ This forwarded message is not from a channel or supergroup.")
