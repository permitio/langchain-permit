# LangChain Permit Integration

Access Control components for LangChain using Permit.io: authenticate users and agents, filter prompts, protect RAG access, secure API interactions, and enforce AI responses with robust, fine-grained permission management across your AI applications.

## Key Features

- 🔒 JWT Token Validation
- 🛡️ Fine-grained authorization checks
- 📄 RAG search filtering
- 🤖 Permissions-aware RAG retrieval

## Installation

```bash
pip install langchain-permit
```

## Configuration

Set up your access control credentials:

```bash
export PERMIT_API_KEY='your-permit-api-key'
export PERMIT_PDP_URL='a cloud or local address of your policy decision point'
export JWKS_URL='a .well-known URL with your JSON Web Keys'  # Optional
```

## AI Access Control Four-Perimeters Framework

The integration covers the four critical perimeters for access control in AI applications:

1. **Prompt Filtering**

   - Validate user permissions before processing AI prompts
   - Prevent unauthorized query generation

2. **RAG Data Protection**

   - Filter document retrieval based on user roles
   - Ensure users access only permitted documents

3. **Secure External Access**

   - Control API endpoint access
   - Implement approval workflows for sensitive actions

4. **Response Enforcement**
   - Filter and sanitize AI-generated responses
   - Prevent information leakage

## Usage Examples

### Permission Checking

```python
from langchain_permit import LangchainPermitTool

# Initialize permission tool
permit_tool = LangchainPermitTool(
    user_id='user123',
    jwt_token='user_jwt_token'
)

# Check permission
is_permitted = permit_tool.run(
    action='read',
    resource='financial_documents'
)
```

### RAG with Permission Filtering

```python
from langchain_permit import LangchainPermitRetriever

# Initialize retriever with user context
retriever = LangchainPermitRetriever(
    user_id='finance_user',
    jwt_token='finance_jwt_token'
)

# Retrieves only documents user is authorized to access
documents = retriever.invoke("Q1 financial summary")
```

## Advanced Configuration

### Custom PDP URL

```python
permit_tool = LangchainPermitTool(
    api_key='your-api-key',
    pdp_url='https://custom-pdp.permit.io'
)
```

## Requirements

- Python 3.8+
- LangChain
- Permit.io Account

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details.
