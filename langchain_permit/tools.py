# =============> LANGCHAIN IMPLEMENTATION <=============

"""LangchainPermit tools."""

from dotenv import load_dotenv
import os
from typing import Optional, Dict, Type, Any
from permit import Permit, PermitError
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, ConfigDict
import jwt
import asyncio
import requests
import json


class LangchainJWTValidationToolInput(BaseModel):
    jwt_token: str = Field(..., description="JWT token to validate")
    jwks_url: str = Field(..., description="URL of the JWKS endpoint")

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        from_attributes=True
    )

class LangchainJWTValidationTool(BaseTool):
    name: str = "jwt_validation"
    description: str = "Validate a JWT token using public keys from a JWKS endpoint and return its claims"
    args_schema: Type[BaseModel] = LangchainJWTValidationToolInput

    def _run(self, jwt_token: str, jwks_url: str, *, run_manager: Optional[CallbackManagerForToolRun] = None) -> Dict[str, Any]:
        return self.validate_jwt(jwt_token, jwks_url)

    async def _arun(self, jwt_token: str, jwks_url: str, *, run_manager: Optional[CallbackManagerForToolRun] = None) -> Dict[str, Any]:
        return self.validate_jwt(jwt_token, jwks_url)

    def validate_jwt(self, jwt_token: str, jwks_url: str) -> Dict[str, Any]:
        # Extract the unverified header to get the kid
        unverified_header = jwt.get_unverified_header(jwt_token)
        kid = unverified_header.get("kid")
        if not kid:
            raise ValueError("JWT token missing 'kid' header")

        # Fetch the JWKS from the endpoint
        jwks = requests.get(jwks_url).json()
        public_key = None
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                # Convert the JWK to an RSA public key object that PyJWT can use
                public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
                break
        if not public_key:
            raise ValueError(f"Public key not found for kid: {kid}")

        # Validate the token using the public key
        try:
            decoded = jwt.decode(jwt_token, public_key, algorithms=["RS256"])
            return decoded
        except Exception as e:
            raise ValueError(f"JWT validation failed: {e}")


class LangchainPermitToolInput(BaseModel):
    """Input schema for permission checking (authorization only)."""
    user: str = Field(
        ..., 
        description="User ID to check permission for"
    )
    action: str = Field(
        ..., 
        description="The action to check permission for (e.g., 'read', 'write')"
    )
    resource: str = Field(
        ..., 
        description="The resource to check permission against (e.g., 'document', 'file')"
    )
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        from_attributes=True
    )


class LangchainPermitTool(BaseTool):
    """Tool for checking permissions using Permit.io (authorization only)."""
    name: str = "permission_check"
    description: str = "Check if a user has permission to perform an action on a resource using Permit"
    args_schema: Type[BaseModel] = LangchainPermitToolInput
    permit: Optional[Permit] = None

    def __init__(self, permit_client: Optional[Permit] = None):
        """Initialize with an optional Permit client."""
        super().__init__()
        load_dotenv()
        if permit_client is None:
            token = os.getenv("PERMIT_API_KEY")
            self.permit = Permit(
                token=token,
                pdp="https://cloudpdp.api.permit.io",
                api_timeout=5
            )
        else:
            self.permit = permit_client
            
    def _run(
        self, 
        user: str,
        action: str,
        resource: str,
        *, 
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> bool:
        """Run permission check using the Permit client."""
        if not user:
            raise ValueError("User ID must be provided")
        # Use asyncio to run the async check method synchronously
        return asyncio.run(self.permit.check(user, action, resource))

    async def _arun(
        self, 
        user: str,
        action: str,
        resource: str,
        *, 
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> bool:
        """Asynchronous run method for permission check."""
        if not user:
            raise ValueError("User ID must be provided")
        # Directly await the check method
        return await self.permit.check(user, action, resource)
    
