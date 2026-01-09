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

    if not getattr(message, "forward_origin", None):
        await message.reply_text("⚠️ This message is not forwarded from a channel!")
        return

    origin = message.forward_origin

    if origin.type == "channel":
        channel_id = str(origin.chat.id)
        channel_title = origin.chat.title

        # Escape MarkdownV2 special characters
        channel_title_safe = re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', channel_title)
        channel_id_safe = re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', channel_id)

        await message.reply_text(
            f"📢 Forwarded Channel:\nTitle: {channel_title_safe}\nID: `{channel_id_safe}`",
            parse_mode="MarkdownV2"
        )
    else:
        await message.reply_text("⚠️ This forwarded message is not from a channel.")
