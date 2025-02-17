"""Integration tests for Langchain Permit tools."""
from typing import Type
import os
from dotenv import load_dotenv
from permit import Permit
from langchain_core.tools import BaseTool
from langchain_tests.integration_tests import ToolsIntegrationTests
from langchain_permit.tools import (
    LangchainJWTValidationTool,
    LangchainPermissionsCheckTool
)

# Load test environment variables
load_dotenv()

class TestJWTValidationToolIntegration(ToolsIntegrationTests):
    """Test class for JWT Validation tool integration tests."""
    
    @property
    def tool_constructor(self) -> Type[BaseTool]:
        """Get the tool constructor."""
        return LangchainJWTValidationTool
    
    @property
    def tool_constructor_params(self) -> dict:
        """Get the parameters for tool initialization."""
        return {
            "jwks_url": os.getenv("JWKS_URL")
        }
    
    @property
    def tool_invoke_params_example(self) -> dict:
        """Example parameters for tool invocation."""
        return {
            # ensure to pass your jwt token here before running the test 
            "jwt_token": "eyJxxxx........"
        }

class TestPermitPermissionsToolIntegration(ToolsIntegrationTests):
    """Test class for Permit.io Permissions tool integration tests."""
    
    @property
    def tool_constructor(self) -> Type[BaseTool]:
        """Get the tool constructor."""
        return LangchainPermissionsCheckTool
    
    @property
    def tool_constructor_params(self) -> dict:
        """Get the parameters for tool initialization."""
        permit_client = Permit(
            token=os.getenv("PERMIT_API_KEY"),
            pdp=os.getenv("PERMIT_PDP_URL")
        )
        return {
            "name": "permission_check",
            "description": "Check user permissions for documents",
            "permit": permit_client
        }
    
    @property
    def tool_invoke_params_example(self) -> dict:
        """Example parameters for tool invocation."""
        return {
            "user": {
                "key": "user-123",
                "name": "Harry"
            },
            "action": "read",
            "resource": {
                "type": "Document",
                "tenant": "techcorp"
            }
        }