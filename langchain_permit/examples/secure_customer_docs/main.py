from config import PERMIT_API_KEY, PERMIT_PDP_URL, JWKS_URL
from langchain_permit.tools import LangchainJWTValidationTool, LangchainPermissionsCheckTool
from permit import Permit
import asyncio

# Initialize JWT validation tool
jwt_validator = LangchainJWTValidationTool(
    jwks_url=JWKS_URL
)

permit_client = Permit(
    token=PERMIT_API_KEY,
    pdp=PERMIT_PDP_URL
)

permissions_checker = LangchainPermissionsCheckTool(
    name="permission_check",
    description="Check user permissions for documents",
    permit=permit_client,
)
       
async def validate_jwt_token(token: str):
    """Test JWT token validation using our validator."""
    try:
        claims = await jwt_validator._arun(token)
        print("Token validated successfully!")
        print("Claims:", claims)
        return claims
    except Exception as e:
        print("Token validation failed:", str(e))
        return None

async def check_permissions(user_claims):
    """Test permission checking using validated claims."""
    try:
        print("permit client", permit_client)
        # Create a Permit User object from JWT claims
        user = {
            "key": user_claims['sub'],
            "name": user_claims['first_name']
        }
        print("User object created:", user)
        
        # Tenant should come from claim or default to "default"
        resource = {
            "type": "Document",
            "tenant": user_claims.get('tenant', 'default')
        }
        # Test permission check
        result = await permissions_checker._arun(
            user=user,
            action="read",
            resource=resource
        )
        print("resource result", resource)
        print("Permission check result:", result)
        return result
    except Exception as e:
        print("Permission check failed:", str(e))
        return None
        
if __name__ == "__main__":
    test_token = "eyJhbGciOiJSUzI1NiIsImtpZCI6InRhb2ZpcS1pZCJ9.eyJlbWFpbCI6ImhhcnJ5dG9mZm9sb0BleGFtcGxlLmNvbSIsImZpcnN0X25hbWUiOiJIYXJyeSIsImlhdCI6MTczOTczOTMwNiwibGFzdF9uYW1lIjoiVG9mZm9sbyIsInN1YiI6InVzZXItMTIzIiwidGVuYW50IjoidGVjaGNvcnAifQ.mIQtPt8Vv70cbtsm2SxlP82adfR7WUjbQvndxY-3wlpgTbAE1rqldlhOlmrhiissEeLgHvXFvVTsfA57W5zZ9ROB2LtQpnIuJ0GXKC0eIlkKNB3e-2YjEkp6eppomUtYKtvjH6Q-D-SVHG4Sh1_e3PZB36IZ0rlFbqNUkMPrg6fD4eoYeENQJ2ksCb9ocZPgXcdp7qXUtIRLwx1L5wLR5fWngdZMh3GH7_Vqw7I8faBM2LCKs2sclO1o1Bzf_eFuCY1B1DSO6ZCqFO8IZSP8k6AVP3WbYcUggpFVWVbJO4wVA_n-bCgoSOaWSebv3YUbPgb8JzpQj7cl6-QB9rtOmg"
    # asyncio.run(validate_jwt_token(test_token))
    async def main():
        claims = await validate_jwt_token(test_token)
        if claims:
            await check_permissions(claims)
    
    asyncio.run(main())
    
