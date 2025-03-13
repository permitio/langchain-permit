from langchain_permit.validator import JWTValidator


print("\nCase 1: Valid JWKS URL provided")
valid_token = "your-token-here"
valid_jwks_url = "http://localhost:3458/.well-known/jwks.json"
validator_valid_url = JWTValidator(
    jwks_url="http://localhost:3458/.well-known/jwks.json")
try:
    claims = validator_valid_url.validate(valid_token)
    print("Claims from valid JWKS URL:", claims)
except ValueError as e:
    print("Error:", e)


print("\nCase 2: Valid stored token")
validator_with_token = JWTValidator(jwks_url=valid_jwks_url, token=valid_token)
try:
    claims = validator_with_token.validate()
    print("Claims from stored token:", claims)
except ValueError as e:
    print("Error:", e)
