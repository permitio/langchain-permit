
# ========> TEST IMPLEMENTATION <=========

import time
import json
import jwt
from typing import Type
from jwcrypto import jwk
from langchain_permit.tools import LangchainJWTValidationTool, LangchainPermitTool
from langchain_tests.integration_tests import ToolsIntegrationTests
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic.typing")



class TestJWTValidationToolIntegration(ToolsIntegrationTests):
    # Rename test key objects so they're not detected as extra tests.
    _test_key_obj = jwk.JWK.generate(kty="RSA", size=2048)
    _test_kid = "test-kid"
    _test_key_obj["kid"] = _test_kid

    @property
    def tool_constructor(self) -> Type[LangchainJWTValidationTool]:
        return LangchainJWTValidationTool

    @property
    def tool_constructor_params(self) -> dict:
        # No special initialization parameters needed.
        return {}

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
            "jwt_token": token,
            "jwks_url": "http://localhost:8000/test-jwks"  # This URL is intercepted by our monkeypatch
        }

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
    @property
    def tool_constructor(self) -> Type[LangchainPermitTool]:
        return LangchainPermitTool

    @property
    def tool_constructor_params(self) -> dict:
        # We don't need any initialization parameters since 
        # the tool will use PERMIT_API_KEY from environment
        return {}

    @property
    def tool_invoke_params_example(self) -> dict:
        """
        Example permission check parameters.
        Tests if 'test_user' has 'read' permission on 'document'.
        """
        return {
            "user": "test_user",
            "action": "read",
            "resource": "document"
        }