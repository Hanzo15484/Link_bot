from telegram import Update
from telegram.ext import ContextTypes
import asyncio
import logging

from utils.text_formatters import to_small_caps

logger = logging.getLogger(__name__)

async def smallcaps_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle small caps conversion for messages."""
    if update.effective_chat.type != "private":
        return
    
    text = update.message.text or ""
    
    # Skip commands
    if text.startswith("/") or context.user_data.get('skip_smallcaps'):
        return

    transformed = to_small_caps(text)

    # Send bot reply
    bot_msg = await update.message.reply_text(transformed)

    # Wait 2 seconds and delete
    await asyncio.sleep(2)
    try:
        await bot_msg.delete()
    except Exception as e:
        logger.error(f"Failed to delete message: {e}")
