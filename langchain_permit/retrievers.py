# retrievers.py
"""Langchain retrievers with Permit.io integration for authorization."""

from typing import List, Dict, Optional, Any
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain.chains.query_constructor.base import AttributeInfo
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from permit import Permit
from permit import Permit
import os

# Initialize Permit client
permit_client = Permit(
    token=os.getenv("PERMIT_API_KEY"),
    pdp=os.getenv("PERMIT_PDP_URL")
)
class ReBACSelfQueryRetriever(SelfQueryRetriever):
    """A retriever that uses ReBAC (Relationship-Based Access Control) with self-query capabilities.
    
    This retriever extends the standard SelfQueryRetriever to include relationship-based
    access control through Permit.io integration. It allows querying documents based on
    both content and user relationships.
    
    Example:
        >>> retriever = ReBACSelfQueryRetriever(
        ...     llm=ChatOpenAI(),
        ...     vectorstore=vectorstore,
        ...     permit_client=permit_client
        ... )
        >>> # Query with relationship context
        >>> docs = retriever.get_relevant_documents(
        ...     "Find project proposals",
        ...     user_context={"user_id": "user-123", "relationships": ["team-a"]}
        ... )
    """

    def __init__(self, permit_client: Permit, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.permit_client = permit_client
        self.metadata_field_info = [
            AttributeInfo(
                name="owner",
                description="The owner of the document",
                type="string",
            ),
            AttributeInfo(
                name="relationships",
                description="List of users who have a relationship with this document",
                type="list[string]",
            ),
            AttributeInfo(
                name="resource_type",
                description="Type of resource - document, file, etc.",
                type="string",
            ),
        ]

    async def _aget_relevant_documents(self, query: str, user_context: Optional[Dict] = None) -> List[Document]:
        """Get documents relevant to the query while enforcing ReBAC policies.
        
        Args:
            query: User's query string
            user_context: Dictionary containing user information and relationships
            
        Returns:
            List of documents that the user has permission to access
        """
        # First get relevant documents based on query
        docs = await super()._aget_relevant_documents(query)
        
        if not user_context:
            return []
            
        # Filter based on relationships
        allowed_docs = []
        for doc in docs:
            allowed = await self.permit_client.check(
                user=user_context,
                action="read",
                resource={
                    "type": doc.metadata.get("resource_type", "document"),
                    "attributes": doc.metadata
                }
            )
            if allowed:
                allowed_docs.append(doc)
                
        return allowed_docs


class RBACEnsembleRetriever(EnsembleRetriever):
    """An ensemble retriever that combines semantic search with RBAC/ABAC policies.
    
    This retriever uses multiple underlying retrievers and applies role-based and 
    attribute-based access control through Permit.io.
    
    Example:
        >>> retriever = RBACEnsembleRetriever(
        ...     retrievers=[semantic_retriever, permission_retriever],
        ...     weights=[0.7, 0.3],
        ...     permit_client=permit_client
        ... )
        >>> # Query with role context
        >>> docs = retriever.get_relevant_documents(
        ...     "HR policies",
        ...     user_context={"roles": ["hr_staff"], "attributes": {"department": "HR"}}
        ... )
    """
    
    def __init__(self, permit_client: Permit, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.permit_client = permit_client

    async def _aget_relevant_documents(self, query: str, user_context: Optional[Dict] = None) -> List[Document]:
        """Get documents relevant to the query while enforcing RBAC/ABAC policies.
        
        Args:
            query: User's query string
            user_context: Dictionary containing user roles and attributes
            
        Returns:
            List of documents that the user has permission to access based on roles and attributes
        """
        # Get initial results from ensemble
        docs = await super()._aget_relevant_documents(query)
        
        if not user_context:
            return []
            
        # Filter based on RBAC/ABAC
        allowed_docs = []
        for doc in docs:
            allowed = await self.permit_client.check(
                user=user_context,
                action="read",
                resource={
                    "type": doc.metadata.get("resource_type", "document"),
                    "attributes": doc.metadata
                }
            )
            if allowed:
                allowed_docs.append(doc)
                
        return allowed_docs

# Usage Examples
async def demo_rebac_retriever():
    """Example usage of ReBAC retriever"""
    docs = [
        Document(
            page_content="Confidential project proposal for Project X",
            metadata={
                "owner": "user-123",
                "relationships": ["team-a", "managers"],
                "resource_type": "proposal"
            }
        ),
        Document(
            page_content="Public company announcement",
            metadata={
                "owner": "user-456",
                "relationships": ["all-employees"],
                "resource_type": "announcement"
            }
        )
    ]
    
    # Initialize components
    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma.from_documents(docs, embeddings)
    
    rebac_retriever = ReBACSelfQueryRetriever(
        llm=ChatOpenAI(temperature=0),
        vectorstore=vectorstore,
        permit_client=permit_client
    )
    
    # Example queries
    queries = [
        ("Find all project proposals", {"user_id": "user-123", "relationships": ["team-a"]}),
        ("Show me company announcements", {"user_id": "user-789", "relationships": ["all-employees"]})
    ]
    
    for query, context in queries:
        results = await rebac_retriever._aget_relevant_documents(query, context)
        print(f"\nQuery: {query}")
        print(f"Results: {[doc.page_content for doc in results]}")

async def demo_rbac_ensemble_retriever():
    """Example usage of RBAC/ABAC ensemble retriever"""
    docs = [
        Document(
            page_content="HR Policy: Work from home guidelines",
            metadata={
                "department": "HR",
                "classification": "internal",
                "required_role": "hr_staff"
            }
        ),
        Document(
            page_content="Employee handbook",
            metadata={
                "department": "HR",
                "classification": "public",
                "required_role": "employee"
            }
        )
    ]
    
    # Initialize retrievers and create ensemble
    semantic_retriever = Chroma.from_documents(docs, OpenAIEmbeddings()).as_retriever()
    permission_retriever = BM25Retriever.from_documents(docs)
    
    rbac_retriever = RBACEnsembleRetriever(
        retrievers=[semantic_retriever, permission_retriever],
        weights=[0.6, 0.4],
        permit_client=permit_client
    )
    
    # Example queries
    queries = [
        ("HR policies", {"roles": ["hr_staff"], "attributes": {"department": "HR"}}),
        ("Employee handbook", {"roles": ["employee"]})
    ]
    
    for query, context in queries:
        results = await rbac_retriever._aget_relevant_documents(query, context)
        print(f"\nQuery: {query}")
        print(f"Results: {[doc.page_content for doc in results]}")