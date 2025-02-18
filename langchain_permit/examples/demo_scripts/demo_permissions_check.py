# examples/demo_permissions_check.py

import os
import asyncio

from permit import Permit
from langchain_permit.tools import LangchainPermissionsCheckTool

PERMIT_API_KEY = os.getenv("PERMIT_API_KEY", "")
PERMIT_PDP_URL = os.getenv("PERMIT_PDP_URL", "")
DEFAULT_ACTION = "read"
RESOURCE_TYPE = "Document"

async def main():
    # 1. Create a Permit client
    permit_client = Permit(
        token=PERMIT_API_KEY,
        pdp=PERMIT_PDP_URL
    )

    # 2. Initialize the permission-check tool
    permissions_checker = LangchainPermissionsCheckTool(
        name="permission_check",
        description="Checks if a user can read a document",
        permit=permit_client,
    )
    
    # 3. Mock a user object and resource
    user = {
        "key": "user-123",
        "firstName": "Harry",
        "attributes": {"role": "basic_user"}
    }
    resource = {
        "type": RESOURCE_TYPE,
        "key": "doc123",
        "tenant": "techcorp"
    }

    # 4. Use the async _arun to avoid nested event loops
    try:
        allowed_result = await permissions_checker._arun(
            user=user,
            action=DEFAULT_ACTION,
            resource=resource
        )
        print(f"✅ Permission check result: {allowed_result}")
    except Exception as e:
        print(f"❌ Permission check failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
