# PERMIT INTEGRATION

"""LangchainPermit retrievers."""

from typing import Any, List, Optional
import os

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import BaseModel, Field

# Mock document store with metadata
MOCK_DOCUMENTS = [
    Document(
        page_content="Confidential financial report for Q1 2024",
        metadata={
            "doc_id": "doc_finance_1",
            "department": "finance",
            "sensitivity": "high"
        }
    ),
    Document(
        page_content="Marketing strategy for new product launch",
        metadata={
            "doc_id": "doc_marketing_1", 
            "department": "marketing",
            "sensitivity": "medium"
        }
    ),
    Document(
        page_content="HR policy manual",
        metadata={
            "doc_id": "doc_hr_1",
            "department": "hr",
            "sensitivity": "high"
        }
    ),
    Document(
        page_content="Engineering team quarterly objectives",
        metadata={
            "doc_id": "doc_engineering_1",
            "department": "engineering",
            "sensitivity": "medium"
        }
    )
]

class LangchainPermitRetriever(BaseRetriever):
    """
    Permit.io-enabled document retriever with permission filtering.
    """

    jwt_token: Optional[str] = None
    user_id: Optional[str] = None
    k: int = 3

    def _get_allowed_document_ids(self) -> List[str]:
        """
        Simulate Permit.io user permissions endpoint.
        """
        # (Keep the existing implementation)
        if not self.user_id:
            return [doc.metadata['doc_id'] for doc in MOCK_DOCUMENTS]
        
        # Simulated permission logic
        if self.user_id == 'finance_user':
            return ['doc_finance_1']
        elif self.user_id == 'marketing_user':
            return ['doc_marketing_1']
        elif self.user_id == 'hr_user':
            return ['doc_hr_1']
        elif self.user_id == 'engineering_user':
            return ['doc_engineering_1']
        
        return []  # No access if user not recognized

    def _get_relevant_documents(
        self, 
        query: str, 
        *, 
        run_manager: CallbackManagerForRetrieverRun, 
        **kwargs: Any
    ) -> List[Document]:
        """
        Retrieve and filter documents based on user permissions.
        """
        # Get number of documents to return
        k = kwargs.get('k', self.k)
        
        # Get allowed document IDs
        allowed_doc_ids = self._get_allowed_document_ids()
        
        # Filter documents based on allowed IDs
        filtered_docs = [
            doc for doc in MOCK_DOCUMENTS 
            if doc.metadata['doc_id'] in allowed_doc_ids
        ]
        
        # Simulate basic query relevance (very simple matching)
        relevant_docs = [
            doc for doc in filtered_docs 
            if query.lower() in doc.page_content.lower()
        ]
        
        # If not enough documents matching query, pad with other allowed docs
        if len(relevant_docs) < k:
            additional_docs = [
                doc for doc in filtered_docs 
                if doc not in relevant_docs
            ]
            relevant_docs.extend(additional_docs)
        
        # Return exactly k documents, or all if fewer than k
        return relevant_docs[:k]

    async def _aget_relevant_documents(
        self,
        query: str,
        *,
        run_manager: Any,
        **kwargs: Any
    ) -> List[Document]:
        """Async version of document retrieval."""
        return self._get_relevant_documents(query, run_manager=run_manager, **kwargs)