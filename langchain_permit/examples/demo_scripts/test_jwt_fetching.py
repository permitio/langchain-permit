from langchain_permit.validator import JWTValidator
from langchain_permit.tools import LangchainJWTValidationTool
import json

# Case 1: Fetch JWKs from URL
print("Testing Case 1: Fetch JWKs from URL")
validator_with_url = JWTValidator(
    jwks_url="http://localhost:3458/.well-known/jwks.json"
)
try:
    jwks_from_url = validator_with_url._fetch_jwks()
    print("JWKs from URL:", jwks_from_url)
except ValueError as e:
    print("Error fetching JWKs from URL:", e)


# Case 2: Use JWKs from JSON file
print("\nTesting Case 2: Use JWKs from JSON file")
try:
    with open("examples/config/jwks.json", "r") as f:
        jwks_from_file = json.load(f)
    validator_with_json = JWTValidator(jwks_json=jwks_from_file)
    jwks_from_json_result = validator_with_json._fetch_jwks()
    print("JWKs from JSON file:", jwks_from_json_result)
except FileNotFoundError:
    print("Error: jwks.json file not found")
except json.JSONDecodeError:
    print("Error: Invalid JSON format in jwks.json")
except ValueError as e:
    print("Error fetching JWKs from JSON:", e)


# Case 3: No JWKs source
print("\nTesting Case 3: No JWKs source")
validator_no_jwks = JWTValidator()
try:
    jwks_no_source = validator_no_jwks._fetch_jwks()
    print("JWKs from no source:", jwks_no_source)
except ValueError as e:
    print("Error:", e)


# Case 4: Invalid JWKs URL
print("\nTesting Case 4: Invalid JWKs URL")
validator_invalid_url = JWTValidator(
    jwks_url="http://invalid-url.example.com/jwks.json")
try:
    jwks_invalid_url = validator_invalid_url._fetch_jwks()
    print("JWKs from invalid URL:", jwks_invalid_url)
except ValueError as e:
    print("Error:", e)
