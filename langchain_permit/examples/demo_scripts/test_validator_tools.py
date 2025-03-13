from langchain_permit.tools import LangchainJWTValidationTool
import json


tool_with_url = LangchainJWTValidationTool(
    jwks_url="http://localhost:3458/.well-known/jwks.json",
    token="#your-test-token-here"
)

# Validate a token
try:
    validated_claims = tool_with_url.validate()
    print("Validated claims:", validated_claims)
except ValueError as e:
    print("Validation error:", e)

# Get claims (without signature check)
try:
    claims = tool_with_url.get_claims()
    print("Extracted claims:", claims)
except ValueError as e:
    print("Claims extraction error:", e)
