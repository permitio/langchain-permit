import pytest
from unittest.mock import AsyncMock
from permit import Permit, Action, Context, User
from langchain_core.documents import Document
from langchain_permit.retrievers import PermitUserPermissionRetriever, PermitFilterObjectsRetriever

# @pytest.fixture
# def mock_permit_client():
#     """Creates a mock Permit.io client."""
#     permit_client = AsyncMock(spec=Permit)
#     return permit_client

@pytest.fixture
def mock_permit_client():
    """Creates a mock Permit.io client."""
    permit_client = AsyncMock(spec=Permit)
    permit_client.get_user_permissions = AsyncMock()  # Explicitly mock the method
    permit_client.filter_objects = AsyncMock()  # Explicitly mock the method
    return permit_client


# @pytest.fixture
# def test_user():
#     """Creates a mock User as a dictionary."""
#     return {"keys": "test_user"}

@pytest.fixture
def test_user():
    """Creates a mock User."""
    return User(key="test_user") 

@pytest.fixture
def test_action():
    """Creates a mock Action."""
    return "read"

@pytest.fixture
def test_resource_type():
    """Returns a mock resource type."""
    return "document"

@pytest.mark.asyncio
async def test_permit_user_permission_retriever(mock_permit_client, test_user, test_resource_type):
    """Test that PermitUserPermissionRetriever correctly retrieves permitted document IDs."""
    # Mock Permit.io response
    mock_permit_client.get_user_permissions.return_value = {
        "tenant_1": {
            "document": [
                {"id": "doc_1", "actions": ["read", "write"]},
                {"id": "doc_2", "actions": ["read"]},
            ]
        }
    }

    retriever = PermitUserPermissionRetriever(
        permit_client=mock_permit_client,
        user=test_user,
        resource_type=test_resource_type,
        action="read",
        k=2
    )

    results = await retriever._aget_relevant_documents(query="test query", run_manager=AsyncMock())

    assert len(results) == 2
    assert all(isinstance(doc, Document) for doc in results)
    assert results[0].metadata["id"] == "doc_1"
    assert results[1].metadata["id"] == "doc_2"

@pytest.mark.asyncio
async def test_permit_filter_objects_retriever(mock_permit_client, test_user, test_action, test_resource_type):
    """Test that PermitFilterObjectsRetriever correctly filters document IDs."""
    # Mock input and Permit.io response
    document_ids = ["doc_1", "doc_2", "doc_3"]
    mock_permit_client.filter_objects.return_value = [
        {"id": "doc_1"},
        {"id": "doc_3"},
    ]

    retriever = PermitFilterObjectsRetriever(
        permit_client=mock_permit_client,
        user=test_user,
        action=test_action,
        resource_type=test_resource_type,
        document_ids=document_ids,
        k=2
    )

    results = await retriever._aget_relevant_documents(query="test query", run_manager=AsyncMock())

    assert len(results) == 2
    assert all(isinstance(doc, Document) for doc in results)
    assert results[0].metadata["id"] == "doc_1"
    assert results[1].metadata["id"] == "doc_3"
