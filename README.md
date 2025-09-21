# Link Bot

A sophisticated Telegram bot for creating and managing permanent channel links with temporary invite security. This bot allows administrators to generate secure, time-limited invite links for Telegram channels while maintaining permanent access through the bot.

## Features

- **Permanent Bot Links**: Creates permanent links that never expire
- **Temporary Invites**: Channel invites expire after 5 minutes for security
- **Auto-Regeneration**: Automatically creates new invite links when old ones expire
- **Admin Control**: Full administrative controls for user and channel management
- **Customizable Interface**: Settings to customize start and help messages
- **User Management**: Ban, unban, promote, and demote users
- **Small Caps Text**: Converts regular text to small caps format
- **Broadcast System**: Send messages to all bot users

## Prerequisites

- Python 3.7+
- A Telegram Bot Token from [@BotFather](https://t.me/BotFather)
- Bot must be admin in target channels with "Create invite links" permission

## Installation

1. Clone or download the bot file
2. Install required dependencies:
```bash
pip install python-telegram-bot aiofiles aiosqlite requests
```

3. Edit the configuration in the bot file:
```python
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
OWNER_ID = YOUR_USER_ID
ADMIN_IDS = [YOUR_USER_ID, OTHER_ADMIN_IDS]
```

## Usage

### User Commands

- `/start` - Start the bot and view welcome message
- `/help` - Show help guide
- `/id` - Get your user ID

### Admin Commands

- `/gen_link <channel>` - Generate a permanent bot link for a channel
- `/batch_link` - Generate links for all connected channels
- `/debug <channel>` - Check and debug channel permissions
- `/list_channels` - List all active channels with pagination
- `/troubleshoot` - Diagnose and fix common issues
- `/admins` - List all bot admins
- `/users` - Show user statistics
- `/settings` - Configure bot settings (owner only)

### Owner Commands

- `/auth <user_id> <days>` - Authorize a user with temporary access
- `/deauth <user_id>` - Remove authorization from a user  
- `/promote <user_id>` - Promote a user to admin
- `/demote <user_id>` - Demote a user from admin
- `/ban <user_id>` - Ban a user from using the bot
- `/unban <user_id>` - Unban a user
- `/restart` - Restart the bot
- `/broadcast <message>` - Send a message to all users
- `/update` - Update bot from GitHub (requires git)

## How It Works

1. Bot generates a permanent link like: `https://t.me/YourBot?start=base64_code`
2. This permanent link points to a temporary channel invite that expires in 5 minutes
3. After expiration, the bot automatically creates a new channel invite
4. The bot link remains the same but points to the new channel invite
5. Users can always access the channel through the permanent bot link

## Configuration

The bot stores configuration in JSON files:

- `channel_data.json` - Channel and link information
- `bot_settings.json` - Customizable bot interface settings

### Settings Configuration

The bot allows customization of:
- Start message text and image
- Help message text and image  
- Button layouts and callbacks
- User interface elements

## File Structure

```
â”œâ”€â”€ link_bot-3.py          # Main bot file
â”œâ”€â”€ channel_data.json      # Channel and user data (auto-created)
â”œâ”€â”€ bot_settings.json      # Bot interface settings (auto-created)
â””â”€â”€ README.md             # This file
```

## Security Features

- **Time-Limited Access**: All channel invites expire after 5 minutes
- **Auto-Cleanup**: Messages are automatically deleted after 6 minutes
- **User Management**: Comprehensive ban/unban system
- **Admin Hierarchy**: Owner and admin permission levels
- **Secure Storage**: All data stored in encrypted JSON format

## Error Handling

The bot includes comprehensive error handling for:
- Channel permission issues
- Expired or invalid links
- Network connectivity problems
- User authorization errors
- Bot restart and recovery

## Troubleshooting

1. **Bot not working**: Ensure bot is admin in target channels
2. **Permission errors**: Verify bot has "Create invite links" permission
3. **Channel not found**: Use channel ID instead of channel link
4. **Connection issues**: Check internet connection
5. **Debug tool**: Use `/debug @channelname` to check permissions

## Support

For support and updates, contact the bot administrator t.me/Quarel7 or visit the project repository.

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
