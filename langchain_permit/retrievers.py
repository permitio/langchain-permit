"""Permit.io integration retrievers for Langchain."""
import os
from typing import Any, List, Optional, Dict, Callable
from pydantic import BaseModel, Field, field_validator
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain.retrievers import SelfQueryRetriever, EnsembleRetriever
from langchain.chains.query_constructor.base import AttributeInfo
from permit import Permit, User, Action, Context

class PermitSelfQueryRetriever(SelfQueryRetriever, BaseModel):
    """Retriever that uses natural language to query permitted documents."""

    api_key: str = Field(
        default_factory=lambda: os.getenv('PERMIT_API_KEY', ''),
        description="Permit.io API key"
    )
    pdp_url: Optional[str] = Field(
        default_factory=lambda: os.getenv('PERMIT_PDP_URL'),
        description="Optional PDP URL"
    )
    user: User = Field(..., description="User to check permissions for")
    resource_type: str = Field(..., description="Type of resource to query")
    action: str = Field(..., description="Action being performed")
    llm: Any = Field(..., description="Language model for query construction")
    vectorstore: Any = Field(..., description="Vector store for document retrieval")

    _permit_client: Optional[Permit] = None
    _allowed_ids: List[str] = []

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **data):
        super().__init__(**data)
        # Initialize Permit client
        self._permit_client = Permit(
            token=self.api_key,
            pdp=self.pdp_url
        )
        
        # Get allowed IDs at initialization
        self._allowed_ids = self._get_permitted_ids()
        
        # Define metadata fields with ID constraint
        metadata_field_info = [
            AttributeInfo(
                name="id",
                description="The document identifier that must be in the allowed list",
                type="string",
                enum=self._allowed_ids  # This constrains searches to allowed IDs
            ),
            AttributeInfo(
                name="resource_type",
                description="The type of resource",
                type="string"
            )
        ]
        
        # Initialize the base SelfQueryRetriever
        super(SelfQueryRetriever, self).__init__(
            llm=self.llm,
            vectorstore=self.vectorstore,
            document_content_description=f"Document of type {self.resource_type}",
            metadata_field_info=metadata_field_info,
            structured_query_translator=self._create_translator()
        )

    def _get_permitted_ids(self) -> List[str]:
        """Get list of permitted document IDs."""
        permissions = self._permit_client.get_user_permissions(
            user=self.user,
            resource_types=[self.resource_type]
        )
        
        allowed_ids = []
        for resource in permissions.get("default", {}).get(self.resource_type, []):
            if self.action in resource.get("actions", []):
                allowed_ids.append(resource["id"])
        
        return allowed_ids

    def _create_translator(self):
        """Create query translator that always includes ID filter."""
        base_translator = self.vectorstore.as_query_transformer()
        
        def wrapped_translator(structured_query):
            # Add ID constraint to every query
            if not structured_query.filter:
                structured_query.filter = {"id": {"$in": self._allowed_ids}}
            else:
                structured_query.filter = {
                    "$and": [
                        structured_query.filter,
                        {"id": {"$in": self._allowed_ids}}
                    ]
                }
            return base_translator.visit_structured_query(structured_query)
            
        return wrapped_translator

    async def _aget_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
        **kwargs: Any
    ) -> List[Document]:
        """Get relevant documents with permissions built into the query."""
        run_manager.on_retriever_start(
            query,
            {
                "user_id": self.user.key,
                "resource_type": self.resource_type,
                "action": self.action,
                "allowed_ids_count": len(self._allowed_ids)
            }
        )

        try:
            # Query is already constrained to allowed IDs via translator
            docs = await super()._aget_relevant_documents(
                query,
                run_manager=run_manager,
                **kwargs
            )
            
            run_manager.on_retriever_end(docs)
            return docs
            
        except Exception as e:
            run_manager.on_retriever_error(f"{e.__class__.__name__}: {str(e)}")
            raise

class PermitEnsembleRetriever(EnsembleRetriever, BaseModel):
    """Ensemble retriever with Permit.io permission filtering."""

    # Instance configuration
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
    retrievers: List[BaseRetriever] = Field(..., description="List of retrievers to ensemble")
    weights: Optional[List[float]] = Field(default=None, description="Optional weights for retrievers")

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
        # Initialize Permit client
        self._permit_client = Permit(
            token=self.api_key,
            pdp=self.pdp_url
        )
        # Initialize base EnsembleRetriever
        super(EnsembleRetriever, self).__init__(
            retrievers=self.retrievers,
            weights=self.weights
        )

    async def _filter_by_permissions(
        self,
        documents: List[Document]
    ) -> List[Document]:
        """Filter documents by permissions."""
        # Extract document IDs
        doc_ids = [doc.metadata.get("id") for doc in documents if "id" in doc.metadata]
        
        if not doc_ids:
            return []
        
        try:
            # Prepare resources for permission check
            resources = [
                {"id": doc_id, "type": self.resource_type}
                for doc_id in doc_ids
            ]
            
            # Check permissions through Permit.io
            filtered_resources = await self._permit_client.filter_objects(
                user=self.user,
                action=self.action,
                context=Context(),
                resources=resources
            )
            
            # Get allowed IDs
            allowed_ids = {r["id"] for r in filtered_resources}
            
            # Filter documents
            return [
                doc for doc in documents 
                if doc.metadata.get("id") in allowed_ids
            ]
            
        except Exception as e:
            raise RuntimeError(f"Permission filtering failed: {str(e)}")

    async def _aget_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
        **kwargs: Any
    ) -> List[Document]:
        """Get relevant documents from ensemble and filter by permissions."""
        # Start retrieval process
        run_manager.on_retriever_start(
            query,
            {
                "retriever_type": self.__class__.__name__,
                "num_retrievers": len(self.retrievers),
                "resource_type": self.resource_type,
                "action": self.action.action
            }
        )

        try:
            # Get documents from ensemble retrievers
            docs = await super()._aget_relevant_documents(
                query,
                run_manager=run_manager,
                **kwargs
            )
            
            run_manager.on_event(
                "ensemble_retrieval_complete",
                {"retrieved_count": len(docs)}
            )
            
            # Apply permission filtering
            filtered_docs = await self._filter_by_permissions(docs)
            
            run_manager.on_retriever_end(
                filtered_docs,
                {
                    "initial_count": len(docs),
                    "permitted_count": len(filtered_docs),
                    "filtered_out": len(docs) - len(filtered_docs)
                }
            )
            
            return filtered_docs
            
        except Exception as e:
            run_manager.on_retriever_error(f"{e.__class__.__name__}: {str(e)}")
            raise

    def get_relevant_documents(
        self,
        query: str,
        **kwargs: Any
    ) -> List[Document]:
        """Not implemented - use async version."""
        raise NotImplementedError(
            "This retriever only supports async operations. Please use aget_relevant_documents."
        )