from langchain_permit.validator import JWTValidator
# Test cases for get_claims
print("\nTesting get_claims method")

# Case 1: Valid token provided
print("\nCase 1: Valid token provided")
valid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
validator = JWTValidator()
try:
    claims = validator.get_claims(valid_token)
    print("Claims:", claims)
except ValueError as e:
    print("Error:", e)

# Case 2: Valid stored token (single session instance)
print("\nCase 2: Valid stored token")
validator_with_token = JWTValidator(token=valid_token)
try:
    claims = validator_with_token.get_claims()
    print("Claims from stored token:", claims)
except ValueError as e:
    print("Error:", e)

# Case 3: Invalid token provided
print("\nCase 3: Invalid token provided")
invalid_token = "invalid.token.here"
try:
    claims = validator.get_claims(invalid_token)
    print("Claims:", claims)
except ValueError as e:
    print("Error:", e)

# Case 4: No token provided or stored
print("\nCase 4: No token provided or stored")
validator_no_token = JWTValidator()
try:
    claims = validator_no_token.get_claims()
    print("Claims:", claims)
except ValueError as e:
    print("Error:", e)


# Case 5: Expired token (claims extraction only)
print("\nCase 5: Expired token")
expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjE1MTYyMzkwMjN9.XbPfbIHMI6arZ3Y922BhjWgQzWXcXNrz0ogtVhfEd2o"
try:
    claims = validator.get_claims(expired_token)
    print("Claims from expired token:", claims)
except ValueError as e:
    print("Error:", e)
