from importlib import metadata

from langchain_permit.chat_models import ChatLangchainPermit
from langchain_permit.document_loaders import LangchainPermitLoader
from langchain_permit.embeddings import LangchainPermitEmbeddings
from langchain_permit.retrievers import LangchainPermitRetriever
from langchain_permit.toolkits import LangchainPermitToolkit
from langchain_permit.tools import LangchainPermitTool
from langchain_permit.vectorstores import LangchainPermitVectorStore

try:
    # __version__ = metadata.version(__package__)
     __version__ = metadata.version(__package__ or "langchain-permit")
except metadata.PackageNotFoundError:
    # Case where package metadata is not available.
    __version__ = "0.1.0"
del metadata  # optional, avoids polluting the results of dir(__package__)

__all__ = [
    "ChatLangchainPermit",
    "LangchainPermitVectorStore",
    "LangchainPermitEmbeddings",
    "LangchainPermitLoader",
    "LangchainPermitRetriever",
    "LangchainPermitToolkit",
    "LangchainPermitTool",
    "__version__",
]
