import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.operations import UserOperations
from config import OWNER_ID

print(f"Fixing admin status for owner {OWNER_ID}...")

# Force promote owner to admin
success = UserOperations.promote_to_admin(OWNER_ID)

if success:
    print(f"✅ Owner {OWNER_ID} promoted to admin!")
    
    # Verify
    is_admin = UserOperations.is_admin(OWNER_ID)
    print(f"Verification: is_admin({OWNER_ID}) = {is_admin}")
else:
    print(f"❌ Failed to promote owner {OWNER_ID}")
    
# Also add owner to database if not exists
user = UserOperations.get_user(OWNER_ID)
if not user:
    print(f"Adding owner {OWNER_ID} to database...")
    UserOperations.add_or_update_user(OWNER_ID, "Quarel7", "ʜᴀɴᴢᴏ𒆜", None)
    UserOperations.promote_to_admin(OWNER_ID)
    print("✅ Owner added and promoted!")
