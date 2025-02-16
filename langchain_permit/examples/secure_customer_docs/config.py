from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Permit.io configurations
PERMIT_API_KEY = os.getenv("PERMIT_API_KEY")
PERMIT_PDP_URL = os.getenv("PERMIT_PDP_URL")

# JWT configurations
JWKS_URL = os.getenv("JWKS_URL")

# Ensure required environment variables are set
required_vars = {
    "PERMIT_API_KEY": PERMIT_API_KEY,
    "PERMIT_PDP_URL": PERMIT_PDP_URL,
    "JWKS_URL": JWKS_URL
}

for var_name, var_value in required_vars.items():
    if not var_value:
        raise ValueError(f"{var_name} must be set in environment variables")

# Basic configuration for the demo
RESOURCE_TYPE = "document"  # The type of resource we're protecting
DEFAULT_ACTION = "read"     # Default action for document access