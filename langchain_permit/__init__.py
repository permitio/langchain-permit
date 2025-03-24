from importlib import metadata


from langchain_permit.retrievers import (
    PermitSelfQueryRetriever,
    PermitEnsembleRetriever,
)
from langchain_permit.tools import LangchainPermissionsCheckTool
from langchain_permit.tools import LangchainJWTValidationTool

# from langchain_permit.validator import JWTValidator

try:
    # __version__ = metadata.version(__package__)
    __version__ = metadata.version(__package__ or "langchain-permit")
except metadata.PackageNotFoundError:
    # Case where package metadata is not available.
    __version__ = "0.1.0"
del metadata  # optional, avoids polluting the results of dir(__package__)

__all__ = [
    "PermitSelfQueryRetriever",
    "PermitEnsembleRetriever",
    "LangchainPermissionsCheckTool",
    "LangchainJWTValidationTool",
    # "JWTValidator",
    "__version__",
]
