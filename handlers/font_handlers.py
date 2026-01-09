from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import asyncio
import logging

from config import FONTS
from utils.text_formatters import convert_font

logger = logging.getLogger(__name__)

# Temporary store user's selected font
user_font_selection = {}

async def font_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Font command handler."""
    keyboard = [
        [InlineKeyboardButton(name, callback_data=f"font_{name}")]
        for name in FONTS.keys()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "✨ *Choose a font style:*",
        parse_mode="MarkdownV2",
        reply_markup=reply_markup
    )

async def font_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Font callback handler."""
    query = update.callback_query
    await query.answer()

    style = query.data.replace("font_", "")
    user_font_selection[query.from_user.id] = style

    try:
        await query.message.delete()
    except:
        pass

    await update.callback_query.message.reply_text(
        f"✍️ Now send the text you want to convert into *{style}* font:",
        parse_mode="MarkdownV2"
    )

async def handle_font_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle font text conversion."""
    user_id = update.effective_user.id
    if user_id not in user_font_selection:
        return  # Ignore unrelated messages

    style = user_font_selection[user_id]
    del user_font_selection[user_id]  # Reset after use

    # Delete user's message and send "Please wait..."
    try:
        await update.message.delete()
    except:
        pass

    msg = await update.message.chat.send_message("⏳ Please wait...")
    await asyncio.sleep(1.5)
    await msg.delete()

    converted = convert_font(update.message.text, style)

    await update.message.chat.send_message(
        f"✅ Converted text:\n<code>{converted}</code>",
        parse_mode="HTML"
    )
