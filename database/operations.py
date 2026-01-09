import sqlite3
import json
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Database singleton
_db_instance = None

def get_db():
    """Get database instance."""
    global _db_instance
    if _db_instance is None:
        from .models import Database
        _db_instance = Database()
    return _db_instance

def get_connection():
    """Get database connection."""
    return get_db().get_connection()

class UserOperations:
    @staticmethod
    def add_or_update_user(user_id, username=None, first_name=None, last_name=None):
        """Add or update user information."""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if user should be admin
            from config import ADMIN_IDS
            should_be_admin = int(user_id) in ADMIN_IDS
            
            cursor.execute('''
                INSERT OR REPLACE INTO users 
                (user_id, username, first_name, last_name, last_seen, is_admin)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, 
                COALESCE((SELECT is_admin FROM users WHERE user_id = ?), ?))
            ''', (user_id, username, first_name, last_name, user_id, 1 if should_be_admin else 0))
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding/updating user {user_id}: {e}")
            return False
        finally:
            conn.close()
    
    @staticmethod
    def get_user(user_id):
        """Get user by ID."""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    
    @staticmethod
    def is_admin(user_id):
        """Check if user is admin."""
        from config import ADMIN_IDS
        
        # First check config
        if int(user_id) in ADMIN_IDS:
            return True
        
        # Then check database
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT is_admin FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return row['is_admin'] == 1 if row else False
        finally:
            conn.close()
    
    @staticmethod
    def get_all_users():
        """Get all users."""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM users")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    @staticmethod
    def get_user_count():
        """Get total user count."""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT COUNT(*) as count FROM users")
            row = cursor.fetchone()
            return row['count'] if row else 0
        finally:
            conn.close()
    
    @staticmethod
    def get_all_admins():
        """Get all admin users."""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM users WHERE is_admin = 1")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    @staticmethod
    def get_all_banned():
        """Get all banned users."""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM users WHERE is_banned = 1")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    @staticmethod
    def promote_to_admin(user_id):
        """Promote user to admin."""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("UPDATE users SET is_admin = 1 WHERE user_id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    @staticmethod
    def demote_admin(user_id):
        """Demote admin to regular user."""
        from config import OWNER_ID
        if user_id == OWNER_ID:
            return False  # Cannot demote owner
            
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("UPDATE users SET is_admin = 0 WHERE user_id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    @staticmethod
    def ban_user(user_id):
        """Ban a user."""
        from config import OWNER_ID
        if user_id == OWNER_ID:
            return False  # Cannot ban owner
            
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    @staticmethod
    def unban_user(user_id):
        """Unban a user."""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

class ChannelOperations:
    @staticmethod
    def add_channel(channel_id, channel_name, file_id):
        """Add a new channel."""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO channels (channel_id, channel_name, file_id)
                VALUES (?, ?, ?)
            ''', (str(channel_id), channel_name, file_id))
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding channel {channel_id}: {e}")
            return False
        finally:
            conn.close()
    
    @staticmethod
    def get_channel(channel_id):
        """Get channel by ID."""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM channels WHERE channel_id = ?", (str(channel_id),))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    
    @staticmethod
    def get_all_channels():
        """Get all channels."""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM channels ORDER BY channel_name")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    @staticmethod
    def delete_channel(channel_id):
        """Delete a channel."""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            # Delete associated links first
            cursor.execute("DELETE FROM links WHERE channel_id = ?", (str(channel_id),))
            # Delete channel
            cursor.execute("DELETE FROM channels WHERE channel_id = ?", (str(channel_id),))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

class LinkOperations:
    @staticmethod
    def add_link(file_id, channel_id, invite_link, expiry_time):
        """Add or update a link."""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO links 
                (file_id, channel_id, invite_link, expiry_time, is_active)
                VALUES (?, ?, ?, ?, 1)
            ''', (file_id, str(channel_id), invite_link, expiry_time.isoformat()))
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding link {file_id}: {e}")
            return False
        finally:
            conn.close()
    
    @staticmethod
    def get_link(file_id):
        """Get link by file ID."""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM links WHERE file_id = ?", (file_id,))
            row = cursor.fetchone()
            if row:
                link_dict = dict(row)
                link_dict['expiry_time'] = datetime.fromisoformat(link_dict['expiry_time'])
                return link_dict
            return None
        finally:
            conn.close()
    
    @staticmethod
    def update_link(file_id, invite_link, expiry_time):
        """Update a link."""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE links 
                SET invite_link = ?, expiry_time = ?, is_active = 1
                WHERE file_id = ?
            ''', (invite_link, expiry_time.isoformat(), file_id))
            
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

class SettingsOperations:
    @staticmethod
    def get_settings(key=None):
        """Get settings."""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            if key:
                cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
                row = cursor.fetchone()
                if row:
                    return json.loads(row['value'])
                return None
            else:
                cursor.execute("SELECT * FROM settings")
                settings = {}
                for row in cursor.fetchall():
                    try:
                        settings[row['key']] = json.loads(row['value'])
                    except:
                        settings[row['key']] = row['value']
                return settings
        finally:
            conn.close()
    
    @staticmethod
    def update_settings(key, value):
        """Update settings."""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO settings (key, value)
                VALUES (?, ?)
            ''', (key, json.dumps(value)))
            
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating settings {key}: {e}")
            return False
        finally:
            conn.close()
