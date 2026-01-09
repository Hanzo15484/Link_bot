import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.operations import SettingsOperations

# Test database connection
print("Testing database...")
settings = SettingsOperations.get_settings()
print(f"Settings keys: {list(settings.keys())}")

start_settings = settings.get("start", {})
print(f"Start settings type: {type(start_settings)}")
print(f"Start buttons type: {type(start_settings.get('buttons'))}")
print(f"Start buttons: {start_settings.get('buttons')}")

# Try to parse buttons
import json
buttons = start_settings.get('buttons', '[]')
if isinstance(buttons, str):
    print("Buttons is a string, parsing...")
    try:
        parsed = json.loads(buttons)
        print(f"Parsed successfully: {parsed}")
        print(f"Type of parsed: {type(parsed)}")
        print(f"First button: {parsed[0] if parsed else 'Empty'}")
    except Exception as e:
        print(f"Error parsing: {e}")
