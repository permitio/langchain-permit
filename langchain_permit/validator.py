from typing import Optional, Dict, Any
import jwt
import json
import requests


class JWTValidator:

    def __init__(
        self,
        jwks_url: Optional[str] = None,
        jwks_json: Optional[Dict] = None,
        token: Optional[str] = None
    ):

        self.jwks_url = jwks_url
        self.jwks_json = jwks_json
        self.token = token

    def _fetch_jwks(self) -> Dict:
        if self.jwks_url:
            try:
                response = requests.get(self.jwks_url)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                raise ValueError(f"Failed to fetch JWKs from URL: {e}")

        if self.jwks_json:
            return self.jwks_json

        raise ValueError(
            "No JWKS source provided: both jwks_url and jwks_json are None")

    def validate(self, token: Optional[str] = None, algorithms: Optional[list] = ["RS256"]) -> Dict[str, Any]:
        token_to_validate = token or self.token
        if not token_to_validate:
            raise ValueError("No token provided for validation")

        try:
            unverified_header = jwt.get_unverified_header(token_to_validate)
            kid = unverified_header.get("kid")

            jwks = self._fetch_jwks()

            public_key = None
            for key_dict in jwks.get("keys", []):
                if key_dict.get("kid") == kid:
                    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(
                        json.dumps(key_dict))
                    break

            return jwt.decode(token_to_validate, public_key, algorithms=algorithms)

        except jwt.InvalidTokenError as e:
            raise ValueError(f"JWT validation failed: Invalid token - {e}")
        except jwt.DecodeError as e:
            raise ValueError(f"JWT validation failed: Decode error - {e}")
        except ValueError as e:
            raise
        except Exception as e:
            raise ValueError(f"JWT validation failed: Unexpected error - {e}")

    def get_claims(self, token: Optional[str] = None) -> Dict[str, Any]:
        token_to_decode = token or self.token
        if not token_to_decode:
            raise ValueError("No token provided for claims extraction")

        try:
            return jwt.decode(token_to_decode, options={"verify_signature": False})
        except jwt.DecodeError as e:
            raise ValueError(
                f"Failed to decode token: Invalid token format - {e}")
        except Exception as e:
            raise ValueError(f"Failed to decode token: Unexpected error - {e}")
