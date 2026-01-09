import sqlite3
import json
from datetime import datetime, timedelta
from .models import Database

db = Database()

class UserOperations:
    @staticmethod
    def add_or_update_user(user_id, username=None, first_name=None, last_name=None):
        """Add or update user information."""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO users 
            (user_id, username, first_name, last_name, last_seen)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, username, first_name, last_name))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_user(user_id):
        """Get user by ID."""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        
        conn.close()
        return dict(user) if user else None
    
    @staticmethod
    def is_admin(user_id):
        """Check if user is admin."""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT is_admin FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        
        conn.close()
        return result['is_admin'] == 1 if result else False
    
    @staticmethod
    def is_banned(user_id):
        """Check if user is banned."""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT is_banned FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        
        conn.close()
        return result['is_banned'] == 1 if result else False
    
    @staticmethod
    def get_all_users():
        """Get all users."""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users")
        users = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return users
    
    @staticmethod
    def get_user_count():
        """Get total user count."""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM users")
        result = cursor.fetchone()
        
        conn.close()
        return result['count'] if result else 0
    
    @staticmethod
    def get_all_admins():
        """Get all admin users."""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE is_admin = 1")
        admins = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return admins
    
    @staticmethod
    def get_all_banned():
        """Get all banned users."""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE is_banned = 1")
        banned = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return banned
    
    @staticmethod
    def promote_to_admin(user_id):
        """Promote user to admin."""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("UPDATE users SET is_admin = 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    
    @staticmethod
    def demote_admin(user_id):
        """Demote admin to regular user."""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("UPDATE users SET is_admin = 0 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    
    @staticmethod
    def ban_user(user_id):
        """Ban a user."""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    
    @staticmethod
    def unban_user(user_id):
        """Unban a user."""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    
    @staticmethod
    def authorize_user(user_id, days, authorized_by):
        """Authorize a user for temporary access."""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        expiry_date = datetime.utcnow() + timedelta(days=days)
        cursor.execute('''
            UPDATE users 
            SET authorized_until = ?, authorized_by = ?
            WHERE user_id = ?
        ''', (expiry_date.isoformat(), authorized_by, user_id))
        
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    
    @staticmethod
    def deauthorize_user(user_id):
        """Deauthorize a user."""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users 
            SET authorized_until = NULL, authorized_by = NULL
            WHERE user_id = ?
        ''', (user_id,))
        
        conn.commit()
        conn.close()
        return cursor.rowcount > 0

class ChannelOperations:
    @staticmethod
    def add_channel(channel_id, channel_name, file_id):
        """Add a new channel."""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO channels (channel_id, channel_name, file_id)
            VALUES (?, ?, ?)
        ''', (channel_id, channel_name, file_id))
        
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def get_channel(channel_id):
        """Get channel by ID."""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM channels WHERE channel_id = ?", (channel_id,))
        channel = cursor.fetchone()
        
        conn.close()
        return dict(channel) if channel else None
    
    @staticmethod
    def get_channel_by_file_id(file_id):
        """Get channel by file ID."""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM channels WHERE file_id = ?", (file_id,))
        channel = cursor.fetchone()
        
        conn.close()
        return dict(channel) if channel else None
    
    @staticmethod
    def get_all_channels():
        """Get all channels."""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM channels ORDER BY channel_name")
        channels = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return channels
    
    @staticmethod
    def get_channel_count():
        """Get total channel count."""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM channels")
        result = cursor.fetchone()
        
        conn.close()
        return result['count'] if result else 0
    
    @staticmethod
    def delete_channel(channel_id):
        """Delete a channel and its links."""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM links WHERE channel_id = ?", (channel_id,))
        cursor.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))
        
        conn.commit()
        conn.close()
        return cursor.rowcount > 0

class LinkOperations:
    @staticmethod
    def add_link(file_id, channel_id, invite_link, expiry_time):
        """Add or update a link."""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO links 
            (file_id, channel_id, invite_link, expiry_time, is_active)
            VALUES (?, ?, ?, ?, 1)
        ''', (file_id, channel_id, invite_link, expiry_time.isoformat()))
        
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def get_link(file_id):
        """Get link by file ID."""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM links WHERE file_id = ?", (file_id,))
        link = cursor.fetchone()
        
        conn.close()
        if link:
            link_dict = dict(link)
            link_dict['expiry_time'] = datetime.fromisoformat(link_dict['expiry_time'])
            return link_dict
        return None
    
    @staticmethod
    def get_active_links():
        """Get all active links."""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM links WHERE is_active = 1")
        links = cursor.fetchall()
        
        result = []
        for link in links:
            link_dict = dict(link)
            link_dict['expiry_time'] = datetime.fromisoformat(link_dict['expiry_time'])
            result.append(link_dict)
        
        conn.close()
        return result
    
    @staticmethod
    def update_link(file_id, invite_link, expiry_time):
        """Update a link."""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE links 
            SET invite_link = ?, expiry_time = ?, is_active = 1
            WHERE file_id = ?
        ''', (invite_link, expiry_time.isoformat(), file_id))
        
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    
    @staticmethod
    def deactivate_link(file_id):
        """Deactivate a link."""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("UPDATE links SET is_active = 0 WHERE file_id = ?", (file_id,))
        
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    
    @staticmethod
    def get_expired_links():
        """Get all expired links."""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM links WHERE expiry_time < ?", 
                      (datetime.utcnow().isoformat(),))
        links = cursor.fetchall()
        
        result = []
        for link in links:
            link_dict = dict(link)
            link_dict['expiry_time'] = datetime.fromisoformat(link_dict['expiry_time'])
            result.append(link_dict)
        
        conn.close()
        return result

class SettingsOperations:
    @staticmethod
    def get_settings(key=None):
        """Get settings."""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        if key:
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            result = cursor.fetchone()
            conn.close()
            return json.loads(result['value']) if result else None
        else:
            cursor.execute("SELECT * FROM settings")
            settings = {}
            for row in cursor.fetchall():
                settings[row['key']] = json.loads(row['value'])
            conn.close()
            return settings
    
    @staticmethod
    def update_settings(key, value):
        """Update settings."""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value)
            VALUES (?, ?)
        ''', (key, json.dumps(value)))
        
        conn.commit()
        conn.close()
        return True
