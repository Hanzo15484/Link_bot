import re

def is_valid_channel_input(input_str):
    """Validate channel input format."""
    patterns = [
        r'^-100\d+$',  # Channel ID
        r'^@[\w]+$',  # Username
        r'^https://t\.me/[\w]+$',  # Public link
        r'^https://t\.me/\+[\w]+$',  # Private link
        r'^[\w]+$',  # Just username without @
    ]
    
    for pattern in patterns:
        if re.match(pattern, input_str.strip()):
            return True
    return False

def is_valid_user_id(input_str):
    """Validate user ID."""
    return input_str.strip().isdigit()

def is_valid_days(input_str):
    """Validate days input."""
    try:
        days = int(input_str)
        return 1 <= days <= 365
    except ValueError:
        return False

def validate_button_config(text):
    """Validate button configuration."""
    try:
        lines = text.strip().split('\n')
        for line in lines:
            buttons = line.split('|')
            for button in buttons:
                if ' - ' not in button.strip():
                    return False
        return True
    except:
        return False
