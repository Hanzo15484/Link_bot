import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.models import Database
from config import OWNER_ID, ADMIN_IDS

# Initialize database
db = Database()

conn = db.get_connection()
cursor = conn.cursor()

print(f"Force fixing admin status for {OWNER_ID}...")

# Direct SQL update
cursor.execute('''
    UPDATE users 
    SET is_admin = 1 
    WHERE user_id = ?
''', (OWNER_ID,))

conn.commit()

# Verify
cursor.execute("SELECT is_admin FROM users WHERE user_id = ?", (OWNER_ID,))
result = cursor.fetchone()
print(f"Updated is_admin to: {result['is_admin'] if result else 'No record'}")

conn.close()

# Also update all ADMIN_IDS
print(f"\nUpdating all admin IDs: {ADMIN_IDS}")
conn = db.get_connection()
cursor = conn.cursor()

for admin_id in ADMIN_IDS:
    cursor.execute('''
        UPDATE users 
        SET is_admin = 1 
        WHERE user_id = ?
    ''', (admin_id,))

conn.commit()
conn.close()

print("✅ All admin IDs updated!")
