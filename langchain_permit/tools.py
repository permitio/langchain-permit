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



class LangchainPermitToolInput(BaseModel):
    """Input schema for permission checking.

    The Field descriptions are sent to the model when performing tool calling.
    """
    user: Optional[str] = Field(
        default=None, 
        description="User ID (optional if JWT token is provided)"
    )
    jwt_token: Optional[str] = Field(
        default=None, 
        description="JWT token for authentication and user identification"
    )
    action: str = Field(
        ..., 
        description="The action to check permission for (e.g., 'read', 'write')"
    )
    resource: str = Field(
        ..., 
        description="The resource to check permission against (e.g., 'document', 'file')"
    )
    jwt_secret_key: Optional[str] = Field(
        default=None, 
        description="Secret key for JWT validation"
    )
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        from_attributes=True
    )

class LangchainPermitTool(BaseTool):
    """Tool for checking permissions using Permit.io.
    """
    name: str = "permission_check"
    description: str = "Validate JWT and check if a user has permission to perform an action on a resource"
    args_schema: Type[BaseModel] = LangchainPermitToolInput
    permit: Optional[Permit] = None

    def __init__(self, permit_client: Optional[Permit] = None):
        """Initialize with optional Permit client."""
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
            
    def _validate_jwt(self, jwt_token: str, secret_key: Optional[str] = None) -> Dict[str, Any]:
        """Validate JWT token and return decoded payload."""
        try:
            # If secret key is not provided, try to get from environment
            if not secret_key:
                secret_key = os.getenv("JWT_SECRET_KEY")
            
            # Decode token
            decoded_token = jwt.decode(
                jwt_token, 
                secret_key, 
                algorithms=['HS256'],
                options={'verify_signature': secret_key is not None}
            )
            return decoded_token
        except jwt.PyJWTError as e:
            raise ValueError(f"JWT validation failed: {str(e)}")
    
    
    def _run(
        self, 
        user: Optional[str] = None,
        jwt_token: Optional[str] = None,
        action: str = None,
        resource: str = None,
        jwt_secret_key: Optional[str] = None,
        *, 
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> bool:
        """Run permission check with optional JWT validation."""
        # Validate JWT if token is provided
        if jwt_token:
            decoded_token = self._validate_jwt(jwt_token, jwt_secret_key)
            # Extract user from JWT if not explicitly provided
            user = user or decoded_token.get('sub') or decoded_token.get('user_id')

        # Ensure user is provided
        if not user:
            raise ValueError("User ID must be provided either through JWT or explicit input")

        # Use asyncio to run the async check method synchronously
        return asyncio.run(self.permit.check(user, action, resource))

    async def _arun(
        self, 
        user: Optional[str] = None,
        jwt_token: Optional[str] = None,
        action: str = None,
        resource: str = None,
        jwt_secret_key: Optional[str] = None,
        *, 
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> bool:
        """Async run method."""
        # Validate JWT if token is provided
        if jwt_token:
            decoded_token = self._validate_jwt(jwt_token, jwt_secret_key)
            # Extract user from JWT if not explicitly provided
            user = user or decoded_token.get('sub') or decoded_token.get('user_id')

        # Ensure user is provided
        if not user:
            raise ValueError("User ID must be provided either through JWT or explicit input")

        # Directly await the check method
        return await self.permit.check(user, action, resource)
    
