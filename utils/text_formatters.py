import re
from config import FONTS

def to_small_caps(text: str) -> str:
    """Convert text to small caps."""
    small_caps_map = {
        "a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ", "e": "ᴇ", "f": "ғ", "g": "ɢ",
        "h": "ʜ", "i": "ɪ", "j": "ᴊ", "k": "ᴋ", "l": "ʟ", "m": "ᴍ", "n": "ɴ",
        "o": "ᴏ", "p": "ᴘ", "q": "ǫ", "r": "ʀ", "s": "s", "t": "ᴛ", "u": "ᴜ",
        "v": "ᴠ", "w": "ᴡ", "x": "x", "y": "ʏ", "z": "ᴢ"
    }
    return "".join(small_caps_map.get(ch.lower(), ch) for ch in text)

def convert_font(text, style):
    """Convert text to different font styles."""
    base = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    font_map = FONTS.get(style, base)
    
    if len(font_map) < len(base):
        font_map += font_map[-1] * (len(base) - len(font_map))
    elif len(font_map) > len(base):
        font_map = font_map[:len(base)]
    
    trans = str.maketrans(base, font_map)
    return text.translate(trans)

def escape_markdown(text):
    """Escape special Markdown characters."""
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text

def format_time_delta(delta):
    """Format timedelta to human readable string."""
    total_seconds = int(delta.total_seconds())
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}s")
    
    return " ".join(parts)
