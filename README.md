# LangChain Permit Integration

Combine [LangChain](https://github.com/hwchase17/langchain) and [Permit.io](https://permit.io/) to add robust access control and permission logic to your LLM applications. This package offers:

- **LangChain Tools** for JWT validation and direct permission checks
- **LangChain Retrievers** that automatically filter or retrieve only the documents your user is allowed to see (Self Query + Ensemble)
- Simple examples and demos to showcase usage

With this integration, you can:

- Validate user tokens and ensure only authorized requests get access
- Filter query results and documents by Permit’s policy logic (RBAC, ABAC, ReBAC)
- Seamlessly embed Permit checks in a RAG pipeline or a chain/agent-based workflow

---

## Features

1. **JWT Validation Tool**  
   Validate JSON Web Tokens against a JWKs endpoint or direct JWKs JSON.

2. **Permissions Check Tool**  
   Check user / resource / action with Permit’s PDP at runtime.

3. **PermitSelfQueryRetriever**  
   A self-querying retriever that uses an LLM to parse a user’s natural language query, obtains the permitted resource IDs from Permit, and filters the vector store accordingly.

4. **PermitEnsembleRetriever**  
   Combines multiple underlying retrievers (like BM25 + vector) and then calls Permit to filter out unauthorized results.

---

## Installation

```bash
pip install langchain-permit
```

You’ll also need the [Permit](https://docs.permit.io/sdk/python/quickstart-python/) package if not already installed:

```bash
pip install permit
```

## Environment Variables

```bash
PERMIT_API_KEY=your_api_key
PERMIT_PDP_URL=http://localhost:7766   # or your real PDP
JWKS_URL=http://localhost:3458/.well-known/jwks.json  # For JWT validation
OPENAI_API_KEY=sk-...                 # If using OpenAI embeddings or chat models
```

For usage, you’ll want to confirm your PDP is running, or you have Permit.io set up to match your policy configuration (resource types, roles, etc.). See [Permit Docs](https://docs.permit.io/concepts/pdp/overview/) for more on setting up the PDP container and writing policy rules.

## Basic Usage Examples

### JWT Validation Tool

The `LangchainJWTValidationTool` allows you to validate JSON Web Tokens (JWTs) using a JSON Web Key Set (JWKS) provided via a URL or direct JSON. It integrates with LangChain as a tool but also provides public methods (`validate` and `get_claims`) for standalone usage.

#### Features

- Validates JWTs with signature verification using a JWKS.
- Extracts JWT claims without signature verification.
- Supports both LangChain tool interface and direct method calls.
- Allows session-based usage with a stored token or dynamic token passing.

#### Installation

Ensure you have the required dependencies:

```bash
pip install langchain-permit requests pyjwt
```

### Usage

1. **Initialize the Tool**: Provide a JWKS source (either a URL or JSON). Optionally, provide a token for session-based use.
2. **Validate a Token**: Use the `validate` method to check the token’s validity with signature verification.
3. **Extract Claims**: Use the `get_claims` method to extract claims without verifying the signature.

#### Example 1: Using a JWKS URL with a Stored Token

```python
from langchain_permit.tools import LangchainJWTValidationTool

# Initialize with a JWKS URL and a token
tool = LangchainJWTValidationTool(
    jwks_url="http://localhost:3458/.well-known/jwks.json",
    token="eyJhbGciOiJSUzI1NiIsImtpZCI6InRhb2ZpcS1pZCJ9.eyJzdWIiOiIxMjMifQ.SignatureHere"
)

# Validate the stored token
try:
    validated_claims = tool.validate()
    print("Validated claims:", validated_claims)
except ValueError as e:
    print("Validation error:", e)

# Extract claims from the stored token
try:
    claims = tool.get_claims()
    print("Extracted claims:", claims)
except ValueError as e:
    print("Claims extraction error:", e)
```

#### Example 2: Using a JWKS JSON File with a Dynamic Token

```python
from langchain_permit.tools import LangchainJWTValidationTool
import json

# Load JWKS from a file
with open("jwks.json", "r") as f:
    jwks_data = json.load(f)

# Initialize with JWKS JSON (no stored token)
tool = LangchainJWTValidationTool(jwks_json=jwks_data)

# Validate a token dynamically
try:
    validated_claims = tool.validate("eyJhbGciOiJSUzI1NiIsImtpZCI6InRhb2ZpcS1pZCJ9.eyJzdWIiOiIxMjMifQ.SignatureHere")
    print("Validated claims:", validated_claims)
except ValueError as e:
    print("Validation error:", e)

# Extract claims dynamically
try:
    claims = tool.get_claims("eyJhbGciOiJSUzI1NiIsImtpZCI6InRhb2ZpcS1pZCJ9.eyJzdWIiOiIxMjMifQ.SignatureHere")
    print("Extracted claims:", claims)
except ValueError as e:
    print("Claims extraction error:", e)
```

### Notes

- **JWKS Requirement**: You must provide either a `jwks_url` or `jwks_json` when initializing the tool. The JWKS must contain a key matching the token's `kid` for `validate` to work.
- **Token Flexibility**: The `token` parameter is optional during initialization. If not provided, you must pass a token to `validate` or `get_claims`.
- **Validation vs. Claims Extraction**: `validate` verifies the token's signature, while `get_claims` extracts claims without verification (use with trusted tokens only).
- **Error Handling**: Always wrap calls in `try-except` blocks to handle `ValueError` exceptions (e.g., invalid token, unreachable JWKS URL).

### Permission Check Tool

```python
from permit import Permit
from langchain_permit.tools import LangchainPermissionsCheckTool

permit_client = Permit(
    token="permit_api_key_here",
    pdp="http://localhost:7766" # or your real deployment url
)

permissions_checker = LangchainPermissionsCheckTool(
    name="permission_check",
    permit=permit_client,
)

# In an async context:
# result = await permissions_checker._arun(
#     user={"key": "user123"},
#     action="read",
#     resource={"type": "Document", "key": "doc123", "tenant": "default"}
# )
# print("Permission check result:", result)
```

Check out `examples/demo_permissions_check.py` for a runnable demonstration.

### PermitSelfQueryRetriever

A custom retriever that:

1. Fetches permitted document IDs from Permit.
2. Uses an LLM to parse your user’s query into a structured filter (Self Query).
3. Applies that ID-based filter to the vector store search.

```python
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_permit.retrievers import PermitSelfQueryRetriever

# Suppose we have some documents
docs = [...]
embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_documents(docs, embeddings)

retriever = PermitSelfQueryRetriever(
    api_key="...",
    pdp_url="...",
    user={"key": "user_123"},
    resource_type="my_resource",
    action="view",
    llm=embeddings,                # or ChatOpenAI, for actual LLM-based query parsing
    vectorstore=vectorstore,
    enable_limit=False,
)

query = "Which docs talk about cats?"
docs = retriever.get_relevant_documents(query)
for doc in docs:
    print(doc.metadata.get("id"), doc.page_content)
```

See a complete script at `examples/demo_self_query.py`.

### PermitEnsembleRetriever

This retriever leverages EnsembleRetriever from LangChain, merging multiple child retrievers, and then uses Permit to filter out any unauthorized docs.

```python
import os
import asyncio
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_permit.retrievers import PermitEnsembleRetriever

async def main():
    # Sample documents
    texts = [
        ("doc_a", "Cats are wonderful creatures..."),
        ("doc_b", "Dogs are quite loyal..."),
    ]
    docs = [Document(page_content=txt, metadata={"id": idx}) for (idx, txt) in texts]

    # Vector store
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(docs, embedding=embeddings)
    vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

    # Ensemble with just one child retriever for simplicity
    ensemble_retriever = PermitEnsembleRetriever(
        api_key=os.getenv("PERMIT_API_KEY", ""),
        pdp_url=os.getenv("PERMIT_PDP_URL"),
        user="user_abc",
        action="view",
        resource_type="my_resource",
        retrievers=[vector_retriever],  # Or pass multiple retrievers
    )

    query = "tell me about cats"
    results = await ensemble_retriever._aget_relevant_documents(query, run_manager=None)

    for i, doc in enumerate(results, start=1):
        print(f"{i}. {doc.metadata.get('id')}: {doc.page_content}")

if __name__ == "__main__":
    asyncio.run(main())
```

Check out examples/demo_ensemble.py for a more complete version.

## Requirements

1. Python 3.8+
2. [Permit.io](https://app.permit.io/) Account
3. [LangChain](https://python.langchain.com/docs/introduction/)

## License

This project is MIT Licensed. See [Permit.io Docs](https://docs.permit.io/) for terms related to the Permit PDP and hosted services.
