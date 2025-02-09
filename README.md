# LangChain Permit Integration

Fine-grained authorization for LangChain using Permit.io: Seamlessly control document access, API interactions, and AI responses with robust, role-based permission management across your AI applications.

## Overview

This package provides a comprehensive authorization layer for LangChain applications, leveraging Permit.io's advanced permission management system. It enables developers to implement granular access controls across different stages of AI-powered workflows.

## Key Features

- 🔒 JWT Token Validation
- 🛡️ Role-Based Access Control
- 📄 Document Retrieval Filtering
- 🤖 AI Action Authorization

## Installation

```bash
pip install langchain-permit
```

## Configuration

Set up your Permit.io credentials:

```bash
export PERMIT_API_KEY='your-permit-api-key'
export JWT_SECRET_KEY='your-jwt-secret-key'  # Optional
```

## Authorization Perimeters

The integration covers four critical authorization domains:

1. **Prompt Protection**

   - Validate user permissions before processing AI prompts
   - Prevent unauthorized query generation

2. **RAG Data Filter**

   - Filter document retrieval based on user roles
   - Ensure users access only permitted documents

3. **AI Action Authorization**

   - Control API endpoint access
   - Implement approval workflows for sensitive actions

4. **Response Protection**
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
