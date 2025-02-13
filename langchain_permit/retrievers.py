"""Permit.io integration retrievers for Langchain."""
import os
from typing import Any, List, Optional, Dict
from pydantic import BaseModel, Field, field_validator
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from permit import Permit, User, Action, Context

class PermitUserPermissionRetriever(BaseRetriever, BaseModel):
    """Retriever that uses Permit.io's get_user_permissions to fetch allowed document IDs."""
    
    api_key: str = Field(
        default_factory=lambda: os.getenv('PERMIT_API_KEY', ''),
        description="Permit.io API key"
    )
    pdp_url: Optional[str] = Field(
        default_factory=lambda: os.getenv('PERMIT_PDP_URL'),
        description="Optional PDP URL"
    )
    user: User = Field(..., description="User to check permissions for")
    resource_type: str = Field(..., description="Type of resource being accessed")
    action: str = Field(..., description="Action being performed")
    k: int = Field(default=3, description="Maximum number of documents to return")
    
    _permit_client: Optional[Permit] = None

    class Config:
        arbitrary_types_allowed = True
        
    @field_validator('api_key')
    def validate_api_key(cls, v):
        if not v:
            raise ValueError("PERMIT_API_KEY must be provided either through environment variable or directly")
        return v

    def __init__(self, **data):
        super().__init__(**data)
        self._permit_client = Permit(
            token=self.api_key,
            pdp=self.pdp_url
        )

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
    # Initial callback when retriever starts
    run_manager.on_retriever_start(
        query,
        {
            "user_id": self.user.key,
            "resource_type": self.resource_type,
            "action": self.action,
            "retriever_type": self.__class__.__name__
        }
    )
    
    try:
        # Get permissions
        permissions = await self._permit_client.get_user_permissions(
            user=self.user,
            resource_types=[self.resource_type]
        )
        
        # Callback after getting permissions
        run_manager.on_event(
            "permissions_retrieved",
            {"permissions_found": bool(permissions)}
        )
        
        # Get allowed IDs (simpler, no tenant iteration)
        allowed_ids = []
        for resource in permissions.get("default", {}).get(self.resource_type, []):
            if self.action in resource.get("actions", []):
                allowed_ids.append(resource["id"])
        
        # Callback after processing permissions
        run_manager.on_event(
            "permission_check_complete",
            {"allowed_count": len(allowed_ids)}
        )
        
        # Apply limit
        k = kwargs.get('k', self.k)
        allowed_ids = allowed_ids[:k]
        
        # Create documents
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
        
        # Final callback with results
        run_manager.on_retriever_end(
            documents,
            {
                "total_allowed": len(allowed_ids),
                "returned_count": len(documents)
            }
        )
        
        return documents
        
    except Exception as e:
        # Error callback with more context
        run_manager.on_retriever_error(
            f"{e.__class__.__name__}: {str(e)}"
        )
        raise

class PermitFilterObjectsRetriever(BaseRetriever, BaseModel):
    """Retriever that filters documents from a base retriever using Permit.io permissions."""
    
    api_key: str = Field(
        default_factory=lambda: os.getenv('PERMIT_API_KEY', ''),
        description="Permit.io API key"
    )
    pdp_url: Optional[str] = Field(
        default_factory=lambda: os.getenv('PERMIT_PDP_URL'),
        description="Optional PDP URL"
    )
    user: User = Field(..., description="User to check permissions for")
    action: Action = Field(..., description="Action being performed")
    resource_type: str = Field(..., description="Type of resource being accessed")
    base_retriever: BaseRetriever = Field(..., description="Base retriever to filter documents from")
    k: int = Field(default=3, description="Maximum number of documents to return")

    _permit_client: Optional[Permit] = None

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **data):
        super().__init__(**data)
        self._permit_client = Permit(
            token=self.api_key,
            pdp=self.pdp_url
        )

    async def _aget_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
        **kwargs: Any
    ) -> List[Document]:
        """Filter documents based on permissions."""
        # Start the retrieval process
        run_manager.on_retriever_start(
            query,
            {
                "user_id": self.user.key,
                "action": self.action.action,
                "resource_type": self.resource_type,
                "retriever_type": self.__class__.__name__
            }
        )
        
        try:
            # First get documents from base retriever
            docs = await self.base_retriever.aget_relevant_documents(
                query,
                run_manager=run_manager
            )
            
            run_manager.on_event(
                "base_retrieval_complete",
                {"fetched_count": len(docs)}
            )

            # Extract IDs to check permissions
            doc_ids = [doc.metadata.get("id") for doc in docs if "id" in doc.metadata]
            
            # Check permissions through Permit.io
            context = Context()
            resources = [
                {"id": doc_id, "type": self.resource_type}
                for doc_id in doc_ids
            ]
            
            filtered_resources = await self._permit_client.filter_objects(
                user=self.user,
                action=self.action,
                context=context,
                resources=resources
            )
            
            # Get allowed IDs
            allowed_ids = {r["id"] for r in filtered_resources}
            
            run_manager.on_event(
                "permission_check_complete",
                {
                    "checked_count": len(doc_ids),
                    "allowed_count": len(allowed_ids)
                }
            )
            
            # Filter documents
            filtered_docs = [
                doc for doc in docs 
                if doc.metadata.get("id") in allowed_ids
            ]
            
            # Apply k limit
            k = kwargs.get('k', self.k)
            filtered_docs = filtered_docs[:k]
            
            run_manager.on_retriever_end(
                filtered_docs,
                {
                    "initial_count": len(docs),
                    "filtered_count": len(filtered_docs)
                }
            )
            
            return filtered_docs
            
        except Exception as e:
            run_manager.on_retriever_error(
                f"{e.__class__.__name__}: {str(e)}"
            )
            raise