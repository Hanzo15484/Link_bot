import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.operations import UserOperations
from utils.helpers import is_admin
from config import OWNER_ID, ADMIN_IDS

print("=== DEBUG AUTH ===")
print(f"Owner ID: {OWNER_ID}")
print(f"Admin IDs from config: {ADMIN_IDS}")
print(f"Is owner in ADMIN_IDS: {OWNER_ID in ADMIN_IDS}")

# Check database
user = UserOperations.get_user(OWNER_ID)
print(f"\nDatabase user record: {user}")
print(f"is_admin field from DB: {user.get('is_admin') if user else 'No user'}")

# Check UserOperations.is_admin()
db_is_admin = UserOperations.is_admin(OWNER_ID)
print(f"UserOperations.is_admin({OWNER_ID}): {db_is_admin}")

# Check utils.helpers.is_admin()
helpers_is_admin = is_admin(OWNER_ID)
print(f"utils.helpers.is_admin({OWNER_ID}): {helpers_is_admin}")

# Test all admin IDs
print("\n=== Testing all admin IDs ===")
for admin_id in ADMIN_IDS:
    db_check = UserOperations.is_admin(admin_id)
    helpers_check = is_admin(admin_id)
    print(f"ID {admin_id}: DB={db_check}, Helpers={helpers_check}")
