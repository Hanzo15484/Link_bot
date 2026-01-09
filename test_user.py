import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.operations import UserOperations
from config import OWNER_ID, ADMIN_IDS

print(f"Owner ID from config: {OWNER_ID}")
print(f"Admin IDs from config: {ADMIN_IDS}")

# Check if you exist in database
user = UserOperations.get_user(OWNER_ID)
print(f"\nUser from database: {user}")

# Check is_admin function
is_admin = UserOperations.is_admin(OWNER_ID)
print(f"Is admin from database: {is_admin}")

# Check all admins
all_admins = UserOperations.get_all_admins()
print(f"\nAll admins in database: {all_admins}")

# Add yourself if not exists
if not user:
    print("\nAdding owner to database...")
    UserOperations.add_or_update_user(OWNER_ID, "owner", "Owner", "User")
    UserOperations.promote_to_admin(OWNER_ID)
    print("Owner added and promoted to admin.")
    
    # Check again
    user = UserOperations.get_user(OWNER_ID)
    print(f"User after adding: {user}")
    is_admin = UserOperations.is_admin(OWNER_ID)
    print(f"Is admin after adding: {is_admin}")
