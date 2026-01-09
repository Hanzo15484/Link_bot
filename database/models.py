import sqlite3
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path="data/bot.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_admin INTEGER DEFAULT 0,
                is_banned INTEGER DEFAULT 0,
                authorized_until TIMESTAMP,
                authorized_by INTEGER
            )
        ''')
        
        # Channels table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS channels (
                channel_id TEXT PRIMARY KEY,
                channel_name TEXT NOT NULL,
                file_id TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Links table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS links (
                file_id TEXT PRIMARY KEY,
                channel_id TEXT NOT NULL,
                invite_link TEXT NOT NULL,
                expiry_time TIMESTAMP NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (channel_id) REFERENCES channels(channel_id)
            )
        ''')
        
        # Settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')
        
        # Insert default settings if not exist
        default_start = {
            "text": """✦ ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ ᴀᴅᴠᴀɴᴄᴇᴅ ʟɪɴᴋs sʜᴀʀɪɴɢ ʙᴏᴛ
• ᴡɪᴛʜ ᴛʜɪs ʙᴏᴛ, ʏᴏᴜ ᴄᴀɴ sᴀғᴇʟʏ sʜᴀʀᴇ ʟɪɴᴋs ᴀɴᴅ ᴋᴇᴇᴘ ʏᴏᴜʀ ᴄʜᴀɴɴᴇʟs ᴘʀᴏᴛᴇᴄᴛᴇᴅ ғʀᴏᴍ ᴄᴏᴘʏʀɪɢʜᴛ ɪssᴜᴇs.
✦ ғᴇᴀᴛᴜʀᴇs:
• ғᴀsᴛ ᴀɴᴅ ᴇᴀsʏ ʟɪɴᴋ ᴘʀᴏᴄᴇssɪɴɢ
• ᴘᴇʀᴍᴀɴᴇɴᴛ ʟɪɴᴋs ᴡɪᴛʜ ᴛᴇᴍᴘᴏʀᴀʀʏ ᴀᴄᴄᴇss ғᴏʀ sᴀғᴇᴛʏ
• ᴘʀɪᴠᴀᴛᴇ, sᴇᴄᴜʀᴇ, ᴀɴᴅ ғᴜʟʟʏ ᴘʀᴏᴛᴇᴄᴛᴇᴅ ᴄᴏɴᴛᴇɴᴛ
✦ ᴇɴᴊᴏʏ ᴀ sᴍᴀʀᴛᴇʀ, sᴀғᴇʀ, ᴀɴᴅ ᴍᴏʀᴇ ᴘᴏᴡᴇʀғᴜʟ ᴡᴀʏ ᴛᴏ sʜᴀʀᴇ ʟɪɴᴋs!""",
            "image": "",
            "buttons": json.dumps([
                [{"text": "ᴀʙᴏᴜᴛ", "url": "callback:about"}],
                [{"text": "ᴄʟᴏsᴇ", "url": "callback:close"}]
            ])
        }
        
        default_help = {
            "text": """✦ ʙᴏᴛ ʜᴇʟᴘ ɢᴜɪᴅᴇ

┌─ ᴜsᴇʀ ᴄᴏᴍᴍᴀɴᴅs ─┐
• /start – sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ ᴀɴᴅ ᴠɪᴇᴡ ᴡᴇʟᴄᴏᴍᴇ ᴍᴇssᴀɢᴇ  
• /help – sʜᴏᴡ ᴛʜɪs ʜᴇʟᴘ ɢᴜɪᴅᴇ   
• /id – ɢᴇᴛ ʏᴏᴜʀ ɪᴅ
• /settings - ᴄᴏɴꜰɪɢᴜʀᴇ ʙᴏt ꜱᴇᴛᴛɪɴɢꜱ

┌─ ᴀᴅᴍɪɴ ᴄᴏᴍᴍᴀɴᴅs ─┐
• /gen_link <channel_link/id> – ɢᴇɴᴇʀᴀᴛᴇ ᴀ ᴘᴇʀᴍᴀɴᴇɴᴛ ʙᴏᴛ ʟɪɴᴋ ᴡɪᴛʜ ᴀ 5-ᴍɪɴᴜᴛᴇ ᴛᴇᴍᴘᴏʀᴀʀʏ ɪɴᴠɪᴛᴇ  
• /batch_link – ɢᴇɴᴇʀᴀᴛᴇ ʟɪɴᴋs ꜰᴏʀ ᴀʟʟ ᴄʜᴀɴɴᴇʟs ᴡʜᴇʀᴇ ᴛʜᴇ ʙᴏᴛ ɪs ᴀɴ ᴀᴅᴍɪɴ 
• /debug <channel_link/id> – ᴄʜᴇᴄᴋ ᴀɴᴅ ᴅᴇʙᴜɢ ᴄʜᴀɴɴᴇʟ ᴘᴇʀᴍɪssɪᴏɴs
• /list_channels – ʟɪsᴛ ᴀʟʟ ᴀᴄᴛɪᴠᴇ ᴄʜᴀɴɴᴇʟs ᴄᴏɴɴᴇᴄᴛᴇᴅ ᴛᴏ ᴛʜᴇ ʙᴏᴛ  
• /troubleshoot – ᴅɪᴀɢɴᴏsᴇ ᴀɴᴅ ꜰɪx ᴄᴏᴍᴍᴏɴ ɪssᴜᴇs ᴡɪᴛʜ ᴛʜᴇ ʙᴏᴛ  
• /admins - ʟɪꜱᴛ ᴀʟʟ ʙᴏᴛ ᴀᴅᴍɪɴꜱ
• /users - ꜱʜᴏᴡ ᴜꜱᴇʀ ꜱᴛᴀᴛꜱ

┌─ ᴏᴡɴᴇʀ ᴄᴏᴍᴍᴀɴᴅs ─┐
• /auth – ᴀᴜᴛʜᴏʀɪᴢᴇ ᴀ ᴜsᴇʀ ᴡɪᴛʜ ᴛᴇᴍᴘᴏʀᴀʀʏ ᴀᴄᴄᴇss ᴛᴏ ʟɪᴍɪᴛᴇᴅ ᴄᴏᴍᴍᴀɴᴅs  
• /deauth – ʀᴇᴍᴏᴠᴇ ᴀᴜᴛʜᴏʀɪᴢᴀᴛɪᴏɴ ꜰʀᴏᴍ ᴀ ᴜsᴇʀ  
• /promote – ᴘʀᴏᴍᴏᴛᴇ ᴀ ᴜsᴇʀ ᴛᴏ ᴀᴅᴍɪɴ ᴡɪᴛʜ ꜰᴜʟʟ ʙᴏᴛ ᴀᴄᴄᴇss (ᴇxᴄᴇᴘᴛ ᴏᴡɴᴇʀ-ᴏɴʟʏ ᴄᴏᴍᴍᴀɴᴅs)  
• /demote – ʀᴇᴠᴏᴋᴇ ᴀᴅᴍɪɴ ʀɪɢʜᴛs ꜰʀᴏᴍ ᴀ ᴜsᴇʀ  
• /ban – ʙᴀɴ ᴀ ᴜsᴇʀ ꜰʀᴏᴍ ᴜsɪɴɢ ᴛʜᴇ ʙᴏᴛ  
• /unban – ᴜɴʙᴀɴ ᴀ ᴜsᴇʀ  
• /restart – ʀᴇsᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ  
• /broadcast – sᴇɴᴅ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ᴀʟʟ ᴜsᴇʀs  
• /update - ᴜᴘᴅᴀᴛᴇ ʙᴏᴛ ꜰʀᴏᴍ ɢɪᴛʜᴜʙ""",
            "image": "",
            "buttons": json.dumps([
                [
                    {"text": "ʀᴇǫᴜɪʀᴇᴍᴇɴᴛs", "url": "callback:help_requirements"},
                    {"text": "ʜᴏᴡ ɪᴛs ᴡᴏʀᴋ?", "url": "callback:help_how"}
                ],
                [
                    {"text": "ᴛʀᴏᴜʙʟᴇsʜᴏᴏᴛ", "url": "callback:help_troubleshoot"}
                ],
                [
                    {"text": "ʙᴀᴄᴋ", "url": "callback:back_start"},
                    {"text": "ᴄʟᴏsᴇ", "url": "callback:close"}
                ]
            ])
        }
        
        # Insert default settings
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", 
                      ("start", json.dumps(default_start)))
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", 
                      ("help", json.dumps(default_help)))
        
        # Insert owner as admin
        from config import OWNER_ID, ADMIN_IDS
        for admin_id in ADMIN_IDS:
            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, is_admin)
                VALUES (?, ?)
            ''', (admin_id, 1))
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    
    def get_connection(self):
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
