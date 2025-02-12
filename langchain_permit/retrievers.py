"""Permit.io integration retrievers for Langchain."""
from typing import Any, List, Optional, Dict
from itertools import islice
from pydantic import BaseModel, Field
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from permit import Permit, User, Action, Context
from permit.exceptions import PermitConnectionError  # Assuming this exists

class PermitUserPermissionRetriever(BaseRetriever, BaseModel):
    """Retriever that uses Permit.io's get_user_permissions to fetch allowed document IDs."""
    
    permit_client: Permit = Field(..., description="Initialized Permit.io client")
    user: User = Field(..., description="User to check permissions for")
    resource_type: str = Field(..., description="Type of resource being accessed")
    action: str = Field(..., description="Action being performed")
    k: int = Field(default=3, description="Maximum number of documents to return")

    class Config:
        arbitrary_types_allowed = True

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
        **kwargs: Any
    ) -> List[Document]:
        """Synchronous retrieval is not supported - use async version."""
        raise NotImplementedError(
            "This retriever only supports async operations. Please use aget_relevant_documents."
        )

    async def _aget_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
        **kwargs: Any
    ) -> List[Document]:
        """Get documents based on user permissions."""
        run_manager.on_retriever_start(
            query,
            {"user": self.user.key, "resource_type": self.resource_type, "action": self.action, "retriever_type": self.__class__.__name__}
        )
        
        try:
            permissions = await self.permit_client.get_user_permissions(
                user=self.user,
                resource_types=[self.resource_type]
            )
        except PermitConnectionError as e:
            run_manager.on_retriever_error(f"Permit.io connection error: {str(e)}")
            raise
        except Exception as e:
            run_manager.on_retriever_error(f"Unexpected error: {str(e)}")
            raise
        
        allowed_ids = []
        for tenant_perms in permissions.values():
            if self.resource_type in tenant_perms:
                allowed_ids.extend(
                    resource["id"] 
                    for resource in tenant_perms[self.resource_type]
                    if self.action in resource.get("actions", [])
                )
        
        k = kwargs.get('k', self.k)
        allowed_ids = list(islice(allowed_ids, k))
        
        documents = [
            Document(
                page_content="",
                metadata={
                    "id": doc_id,
                    "resource_type": self.resource_type,
                    "permitted": True
                }
            )
            for doc_id in allowed_ids
        ]
        
        run_manager.on_retriever_end(documents)
        return documents

class PermitFilterObjectsRetriever(BaseRetriever, BaseModel):
    """Retriever that uses Permit.io's filter_objects to filter existing documents."""
    
    permit_client: Permit = Field(..., description="Initialized Permit.io client")
    user: User = Field(..., description="User to check permissions for")
    action: Action = Field(..., description="Action being performed")
    resource_type: str = Field(..., description="Type of resource being accessed")
    document_ids: List[str] = Field(..., description="List of document IDs to filter")
    k: int = Field(default=3, description="Maximum number of documents to return")

    class Config:
        arbitrary_types_allowed = True

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
        **kwargs: Any
    ) -> List[Document]:
        """Synchronous retrieval is not supported - use async version."""
        raise NotImplementedError(
            "This retriever only supports async operations. Please use aget_relevant_documents."
        )

    async def _aget_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
        **kwargs: Any
    ) -> List[Document]:
        """Filter documents based on permissions."""
        run_manager.on_retriever_start(
            query,
            {"user": self.user.key, "document_count": len(self.document_ids), "retriever_type": self.__class__.__name__}
        )
        
        try:
            resources = [
                {"id": doc_id, "type": self.resource_type}
                for doc_id in self.document_ids
            ]
            
            context = Context()
            
            filtered_resources = await self.permit_client.filter_objects(
                user=self.user,
                action=self.action,
                context=context,
                resources=resources
            )
        except PermitConnectionError as e:
            run_manager.on_retriever_error(f"Permit.io connection error: {str(e)}")
            raise
        except Exception as e:
            run_manager.on_retriever_error(f"Unexpected error: {str(e)}")
            raise
        
        k = kwargs.get('k', self.k)
        allowed_ids = [r["id"] for r in islice(filtered_resources, k)]
        
        documents = [
            Document(
                page_content="",
                metadata={
                    "id": doc_id,
                    "resource_type": self.resource_type,
                    "permitted": True
                }
            )
            for doc_id in allowed_ids
        ]
        
        run_manager.on_retriever_end(documents)
        return documents
