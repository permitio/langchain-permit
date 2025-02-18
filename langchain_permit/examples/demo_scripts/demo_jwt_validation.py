import os
import asyncio

from langchain_permit.tools import LangchainJWTValidationTool

# Load your JWT token from environment variables (e.g., .env)
TEST_JWT_TOKEN = os.getenv("TEST_JWT_TOKEN")
JWKS_URL = os.getenv("JWKS_URL", "")

async def main():
    
    print("Test Token JWt =====>", JWKS_URL)
    # 1. Initialize the JWT validation tool
    jwt_validator = LangchainJWTValidationTool(
        jwks_url=JWKS_URL
    )
    
    # 2. Validate the token
    try:
        # _arun calls the async JWT validation logic
        claims = await jwt_validator._arun(TEST_JWT_TOKEN)
        print("✅ Token validated successfully!")
        print("Decoded Claims:", claims)
    except Exception as e:
        print("❌ Token validation failed:", str(e))


if __name__ == "__main__":
    asyncio.run(main())
