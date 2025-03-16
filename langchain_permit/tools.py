# =============> LANGCHAIN IMPLEMENTATION <=============

"""LangchainPermit tools."""
import os
from typing import Optional, Dict, Type, Any, Union
from permit import Permit
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, ConfigDict, field_validator
import jwt
import asyncio
import requests
import json
from .validator import JWTValidator


class LangchainJWTValidationToolInput(BaseModel):
    jwt_token: str = Field(..., description="JWT token to validate")

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        from_attributes=True,
        populate_by_name=True
    )


class LangchainJWTValidationTool(BaseTool):
    name: str = "jwt_validation"
    description: str = "Validate a JWT token using either a JWKs endpoint or direct JWKs"
    args_schema: Type[BaseModel] = LangchainJWTValidationToolInput
    validator: Optional[JWTValidator] = Field(default=None, exclude=True)

    def __init__(
        self,
        jwks_url: Optional[str] = None,
        jwks_json: Optional[Dict] = None,
        token: Optional[str] = None,
        **kwargs
    ):
        if not (jwks_url or jwks_json):
            raise ValueError(
                "Either JWKs URL or JSON must be provided for signature validation.")
        super().__init__(**kwargs)
        self.validator = JWTValidator(jwks_url, jwks_json, token)

    def _run(
        self,
        jwt_token: Optional[str] = None,
        *,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        token_to_validate = jwt_token or self.validator.token
        if not token_to_validate:
            raise ValueError("No token provided for validation")
        return self.validator.validate(token_to_validate)

    async def _arun(
        self,
        jwt_token: Optional[str] = None,
        *,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, Any]:
        token_to_validate = jwt_token or self.validator.token
        if not token_to_validate:
            raise ValueError("No token provided for validation")
        return self.validator.validate(token_to_validate)

    def validate(self, token: Optional[str] = None) -> Dict[str, Any]:
        return self.validator.validate(token)

    def get_claims(self, token: Optional[str] = None) -> Dict[str, Any]:
        return self.validator.get_claims(token)


class UserInput(BaseModel):
    """
    Represents a user object for permit.check() validation.
    Maps to IUser interface from Permit.io
    """
    key: str = Field(..., description="Customer-side ID of the user")
    firstName: Optional[str] = Field(
        None, description="First name of the user")
    lastName: Optional[str] = Field(None, description="Last name of the user")
    email: Optional[str] = Field(None, description="Email address of the user")
    attributes: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Custom attributes for ABAC"
    )


class ResourceInput(BaseModel):
    """
    Represents a resource object for permit.check() validation.
    Maps to IResource interface from Permit.io
    """
    type: str = Field(..., description="Resource type/namespace")
    key: Optional[str] = Field(
        None, description="Customer-side ID of the resource")
    tenant: Optional[str] = Field(
        None, description="Tenant under which resource is defined")
    attributes: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Custom attributes for ABAC"
    )


class LangchainPermissionsCheckTool(BaseTool):
    """Tool for checking permissions using Permit.io."""

   # 1. Declare permit as a field
    permit: Optional[Permit] = Field(default=None)

    # 2. Let pydantic know we allow arbitrary types
    class Config:
        arbitrary_types_allowed = True

    # def __init__(self, name: str = "permission_check", permit=None, **kwargs):
    #     super().__init__(name=name, **kwargs)
    #     # 3. Assign it in the constructor
    #     self.permit = permit

    def __init__(
        self,
        name: str = "permission_check",
        description: str = "Check user permissions with Permit.io",
        permit=None,
        **kwargs
    ):
        # Pass name and description to the BaseTool constructor
        super().__init__(name=name, description=description, **kwargs)
        self.permit = permit

    def _validate_inputs(
        self,
        user: Union[str, Dict[str, Any]],
        resource: Union[str, Dict[str, Any]]
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Validate user and resource inputs before sending to permit.check()

        Args:
            user: User identifier or object
            resource: Resource identifier or object

        Returns:
            Tuple of validated (user_dict, resource_dict)

        Raises:
            ValueError: If validation fails
        """
        # Validate user
        if isinstance(user, str):
            validated_user = UserInput(key=user).model_dump(exclude_none=True)
        else:
            try:
                validated_user = UserInput(
                    **user).model_dump(exclude_none=True)
            except Exception as e:
                raise ValueError(f"Invalid user object structure: {str(e)}")

        # Validate resource
        if isinstance(resource, str):
            validated_resource = ResourceInput(
                type=resource).model_dump(exclude_none=True)
        else:
            try:
                validated_resource = ResourceInput(
                    **resource).model_dump(exclude_none=True)
            except Exception as e:
                raise ValueError(
                    f"Invalid resource object structure: {str(e)}")

        return validated_user, validated_resource

    def _run(
        self,
        user: Union[str, Dict[str, Any]],
        action: str,
        resource: Union[str, Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
        *,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> Dict[str, bool]:
        """Run permission check using the Permit client."""
        # Validate inputs
        validated_user, validated_resource = self._validate_inputs(
            user, resource)

        # Prepare check parameters
        check_params = {
            "user": validated_user,
            "action": action,
            "resource": validated_resource
        }

        if context:
            check_params["context"] = context

        # Run the check
        # return asyncio.run(self.permit.check(**check_params))
        allowed = asyncio.run(self.permit.check(**check_params))
        return {"allowed": allowed}

    async def _arun(
        self,
        user: Union[str, Dict[str, Any]],
        action: str,
        resource: Union[str, Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
        *,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> bool:
        """Asynchronous run method."""
        # Validate inputs
        validated_user, validated_resource = self._validate_inputs(
            user, resource)

        # Prepare check parameters
        check_params = {
            "user": validated_user,
            "action": action,
            "resource": validated_resource
        }

        if context:
            check_params["context"] = context

        allowed = await self.permit.check(**check_params)
        return {"allowed": allowed}
        # # Run the check
        # return await self.permit.check(**check_params)
