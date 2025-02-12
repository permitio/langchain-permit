
# ========> TEST IMPLEMENTATION <=========

import os
import time
import json
import jwt
from typing import Type
from jwcrypto import jwk
import requests
from langchain_permit.tools import LangchainJWTValidationTool, LangchainPermissionsCheckTool, LangchainPermissionsCheckToolInput
from langchain_tests.integration_tests import ToolsIntegrationTests
from unittest.mock import Mock, patch

class TestJWTValidationToolIntegration(ToolsIntegrationTests):
    # Rename test key objects so they're not detected as extra tests.
    _test_key_obj = jwk.JWK.generate(kty="RSA", size=2048)
    _test_kid = "test-key"
    _test_key_obj["kid"] = _test_kid

    @property
    def tool_constructor(self) -> Type[LangchainJWTValidationTool]:
        return LangchainJWTValidationTool

    @property
    def tool_constructor_params(self) -> dict:
        # Provide the JWKS URL in the constructor parameters
        return {"jwks_url": "http://localhost:8000/test-jwks"}

    @property
    def tool_invoke_params_example(self) -> dict:
        """
        Create a test JWT token signed with our test RSA key.
        The token includes the 'kid' header so the tool can fetch the correct public key.
        """
        now = int(time.time())
        claims = {
            "sub": "test_user",
            "iat": now,
            "exp": now + 3600,
            "name": "Test User"
        }
        # Export the private key as PEM for signing
        private_pem = self._test_key_obj.export_to_pem(private_key=True, password=None).decode("utf-8")
        token = jwt.encode(claims, private_pem, algorithm="RS256", headers={"kid": self._test_kid})
        return {
            "jwt_token": token
        }

    def run_test(self, monkeypatch):
        """
        Override run_test to include JWKS JSON input test
        """
        # Run the standard integration tests first
        super().run_test(monkeypatch)
        
        # Add JWKS JSON input test
        self._test_jwks_json_input()

    def _test_jwks_json_input(self):
        """
        Test JWT validation with direct JWKS JSON input.
        """
        # Convert test key to JWKS JSON
        jwks_json = {"keys": [json.loads(self._test_key_obj.export_public())]}
        
        # Export the private key as PEM for signing
        private_pem = self._test_key_obj.export_to_pem(private_key=True, password=None).decode("utf-8")
        
        # Create a test JWT token
        now = int(time.time())
        claims = {
            "sub": "test_user_json",
            "iat": now,
            "exp": now + 3600,
            "name": "Test User JSON"
        }
        token = jwt.encode(claims, private_pem, algorithm="RS256", headers={"kid": self._test_kid})
        
        # Create tool with JWKS JSON
        tool = LangchainJWTValidationTool(jwks_json=jwks_json)
        
        # Validate token
        result = tool.run(token)
        
        # Assert key claims are correct
        assert result["sub"] == "test_user_json"
        assert result["name"] == "Test User JSON"

    def setup_method(self, method):
        """
        Monkeypatch requests.get so that any call to the JWKS URL returns our test JWKS.
        """
        import requests
        self._original_get = requests.get

        def fake_get(url, *args, **kwargs):
            if url == "http://localhost:8000/test-jwks":
                class FakeResponse:
                    def json(inner_self):
                        # Return the public key as JWKS.
                        return {"keys": [json.loads(self._test_key_obj.export_public())]}
                    
                    def raise_for_status(inner_self):
                        pass
                return FakeResponse()
            return self._original_get(url, *args, **kwargs)

        requests.get = fake_get

    def teardown_method(self, method):
        """
        Restore the original requests.get after each test.
        """
        import requests
        requests.get = self._original_get


class TestPermitToolIntegration(ToolsIntegrationTests):
    """Integration tests for the LangchainPermitTool."""

    @property
    def tool_constructor(self) -> Type[LangchainPermissionsCheckTool]:
        """Return the tool constructor."""
        return LangchainPermissionsCheckTool

    @property
    def tool_constructor_params(self) -> dict:
        """
        For testing, we'll use a dummy token
        """
        os.environ["PERMIT_API_KEY"] = "permit_key_FCmZ01owzYvQPXPg5KK1mdlzLdqvkV1CiqVGM6MZKqXHa9fq7CbmvC6eDnNOoYsci0oGL9WOCJ2ey1Ttznr8d5"
        return {}

    @property
    def tool_invoke_params_example(self) -> dict:
        """
        Return example parameters for tool invocation.
        Includes RBAC, ABAC, and tenant scenarios.
        """
        return {
            "user": {
                "key": "test_user",
                "attributes": {
                    "department": "engineering",
                    "role": "senior_engineer"
                }
            },
            "action": "read",
            "resource": {
                "key": "document_123",
                "type": "technical_doc",
                "attributes": {
                    "classification": "internal",
                    "department": "engineering"
                }
            },
            "tenant": "default_tenant",
            "context": {
                "environment": "production",
                "access_method": "internal"
            }
        }

    def setup_method(self, method):
        """Set up test environment."""
        # Monkeypatch can be added here if needed
        pass

    def teardown_method(self, method):
        """Clean up test environment."""
        # Cleanup can be added here if needed
        pass

