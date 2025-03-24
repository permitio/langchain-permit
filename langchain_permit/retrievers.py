import os
from typing import Any, List, Optional, Dict, Callable
from pydantic import BaseModel, Field, field_validator, PrivateAttr, ConfigDict
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain.retrievers import SelfQueryRetriever, EnsembleRetriever
from permit import Permit, User, Action, Context
import asyncio
from langchain_core.language_models import BaseLanguageModel
from langchain_core.vectorstores import VectorStore
from langchain.chains.query_constructor.base import (
    StructuredQueryOutputParser,
    get_query_constructor_prompt,
)
from langchain.chains.query_constructor.schema import AttributeInfo


class PermitSelfQueryRetriever(SelfQueryRetriever, BaseModel):
    api_key: Optional[str] = Field(default=None, description="Permit.io API key")
    pdp_url: Optional[str] = Field(default=None, description="Optional PDP URL")
    id_field: str = Field(
        default="document_id",
        description="Field name for the document identifier in vector store matching the resource ID in Permit",
    )
    user: Dict[str, Any] = Field(..., description="User to check permissions for")
    resource_type: str = Field(..., description="Type of resource to query")
    action: str = Field(..., description="Action being performed")
    llm: BaseLanguageModel = Field(
        ..., description="Language model for query construction"
    )
    vectorstore: VectorStore = Field(
        ..., description="Vector store for document retrieval"
    )
    enable_limit: bool = Field(
        default=False, description="Whether to enable limit in queries"
    )

    query_constructor: Optional[Any] = Field(default=None, alias="llm_chain")
    search_type: str = "similarity"
    search_kwargs: dict = Field(default_factory=dict)
    structured_query_translator: Optional[Any] = None
    verbose: bool = False
    use_original_query: bool = False

    _permit_client: Optional[Permit] = PrivateAttr(default=None)
    _allowed_ids: List[str] = PrivateAttr(default=None)
    _allowed_ids_initialized: bool = PrivateAttr(default=False)

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    def __init__(self, **data):
        super().__init__(**data)

        if self._permit_client is None and self.api_key:
            self._permit_client = Permit(token=self.api_key, pdp=self.pdp_url)

        self._allowed_ids = None
        self._allowed_ids_initialized = False

        metadata_field_info = [
            AttributeInfo(
                name=self.id_field,
                description="The document identifier that must be in the allowed list",
                type="string",
                enum=self._allowed_ids,
            ),
            AttributeInfo(
                name="resource_type", description="The type of resource", type="string"
            ),
        ]

        if not self.query_constructor:
            prompt = get_query_constructor_prompt(
                document_contents=f"Document of type {self.resource_type}",
                attribute_info=metadata_field_info,
            )
            output_parser = StructuredQueryOutputParser.from_components()
            self.query_constructor = prompt | self.llm | output_parser

        # Create structured query translator if not provided
        if not self.structured_query_translator:
            self.structured_query_translator = self._create_translator()

    @classmethod
    async def from_permit_client(
        cls,
        permit_client: Permit,
        user: Dict[str, Any],
        resource_type: str,
        action: str,
        llm: BaseLanguageModel,
        vectorstore: VectorStore,
        enable_limit: bool = False,
    ) -> "PermitSelfQueryRetriever":

        incoming_payload = {
            "permit_client": permit_client,
            "user": user,
            "resource_type": resource_type,
            "action": action,
            "llm": llm,
            "vectorstore": vectorstore,
            "enable_limit": enable_limit,
        }

        instance = cls(
            user=user,
            resource_type=resource_type,
            action=action,
            llm=llm,
            vectorstore=vectorstore,
            enable_limit=enable_limit,
        )
        instance._permit_client = permit_client
        instance._allowed_ids = await instance._get_permitted_ids()
        instance._allowed_ids_initialized = True

        metadata_field_info = [
            AttributeInfo(
                name=instance.id_field,
                description="The document identifier that must be in the allowed list",
                type="string",
                enum=instance._allowed_ids,
            ),
            AttributeInfo(
                name="resource_type", description="The type of resource", type="string"
            ),
        ]

        prompt = get_query_constructor_prompt(
            document_contents=f"Document of type {instance.resource_type}",
            attribute_info=metadata_field_info,
        )
        output_parser = StructuredQueryOutputParser.from_components()
        instance.query_constructor = prompt | instance.llm | output_parser

        instance.structured_query_translator = instance._create_translator()

        return instance

    async def _get_permitted_ids(self) -> List[str]:
        if not self._permit_client:
            return []

        permissions = await self._permit_client.get_user_permissions(
            user=self.user, resource_types=[self.resource_type]
        )

        allowed_ids = []
        # Loop through each permission key in the format "resource_type:resource_id"
        for resource_key in permissions.keys():
            if ":" in resource_key:
                resource_type, resource_id = resource_key.split(":", 1)
                if resource_type == self.resource_type:
                    # Check if read permission exists
                    if f"{self.resource_type}:{self.action}" in permissions[
                        resource_key
                    ].get("permissions", []):
                        allowed_ids.append(resource_id)

        return allowed_ids

    def _create_translator(self):
        base_translator = self.vectorstore.as_query_transformer()

        class PermissionQueryTranslator:
            def __init__(self, retriever):
                self.retriever = retriever

            def visit_structured_query(self, structured_query):
                if not self.retriever._allowed_ids_initialized:
                    raise RuntimeError(
                        "Allowed IDs not initialized. Call initialize_allowed_ids() first."
                    )
                if self.retriever._allowed_ids:
                    if not structured_query.filter:
                        structured_query.filter = {
                            self.retriever.id_field: {
                                "$in": self.retriever._allowed_ids
                            }
                        }
                    else:
                        structured_query.filter = {
                            "$and": [
                                structured_query.filter,
                                {
                                    self.retriever.id_field: {
                                        "$in": self.retriever._allowed_ids
                                    }
                                },
                            ]
                        }

                new_kwargs = base_translator(structured_query)
                new_query = structured_query.query
                return new_query, new_kwargs

        return PermissionQueryTranslator(self)

    async def initialize_allowed_ids(self):
        """Initialize allowed_ids asynchronously if not already done."""
        if not self._allowed_ids_initialized:
            self._allowed_ids = await self._get_permitted_ids()
            self._allowed_ids_initialized = True

    async def _aget_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun, **kwargs: Any
    ) -> List[Document]:

        await self.initialize_allowed_ids()

        try:
            docs = await super()._aget_relevant_documents(
                query, run_manager=run_manager, **kwargs
            )

            run_manager.on_retriever_end(docs)
            return docs

        except Exception as e:
            run_manager.on_retriever_error(f"{e.__class__.__name__}: {str(e)}")
            raise

    async def invoke(self, query: str, **kwargs: Any) -> List[Document]:
        return await self._aget_relevant_documents(
            query,
            run_manager=CallbackManagerForRetrieverRun.get_noop_manager(),
            **kwargs,
        )

    def get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: Optional[CallbackManagerForRetrieverRun] = None,
        **kwargs: Any,
    ) -> List[Document]:
        raise RuntimeError(
            "get_relevant_documents should not be called directly in an async context. "
            "Use await retriever.invoke() instead."
        )


class PermitEnsembleRetriever(EnsembleRetriever, BaseModel):
    """
    Data protection retriever that uses the ensemble capabilities to process permissions filtering after receiving results. Use Permit's `filter_objects` to filter the RAG resources with fine-grained authorization.
    """

    # Instance configuration
    api_key: str = Field(
        default_factory=lambda: os.getenv("PERMIT_API_KEY", ""),
        description="Permit.io API key",
    )
    pdp_url: Optional[str] = Field(
        default_factory=lambda: os.getenv("PERMIT_PDP_URL"),
        description="Optional PDP URL",
    )
    user: str = Field(..., description="User to check permissions for")
    action: str = Field(..., description="Action being performed")
    resource_type: str = Field(..., description="Type of resource being accessed")
    retrievers: List[BaseRetriever] = Field(
        ..., description="List of retrievers to ensemble"
    )
    weights: Optional[List[float]] = Field(
        default=None, description="Optional weights for retrievers"
    )

    class Config:
        arbitrary_types_allowed = True

    @field_validator("api_key")
    def validate_api_key(cls, v):
        if not v:
            raise ValueError(
                "PERMIT_API_KEY must be provided either through environment variable or directly"
            )
        return v

    def __init__(self, **data):
        # Initialize base EnsembleRetriever first
        EnsembleRetriever.__init__(
            self, retrievers=data.get("retrievers", []), weights=data.get("weights")
        )
        # Initialize Pydantic BaseModel
        BaseModel.__init__(self, **data)

        # Create the Permit client
        self._permit_client = Permit(token=self.api_key, pdp=self.pdp_url)

    async def _filter_by_permissions(self, documents: List[Document]) -> List[Document]:
        """Filter documents by permissions."""
        # Extract document IDs
        doc_ids = [doc.metadata.get("id") for doc in documents if "id" in doc.metadata]

        if not doc_ids:
            return []

        try:
            # Prepare resources for permission check
            resources = [
                {"id": doc_id, "type": self.resource_type} for doc_id in doc_ids
            ]

            # Check permissions through Permit.io
            filtered_resources = await self._permit_client.filter_objects(
                user=self.user,
                action=self.action,
                context=Context(),
                resources=resources,
            )

            # Get allowed IDs
            allowed_ids = {r["id"] for r in filtered_resources}

            # Filter documents
            return [doc for doc in documents if doc.metadata.get("id") in allowed_ids]

        except Exception as e:
            raise RuntimeError(f"Permission filtering failed: {str(e)}")

    async def _aget_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun, **kwargs: Any
    ) -> List[Document]:
        """Get relevant documents from ensemble and filter by permissions."""
        # Start retrieval process
        run_manager.on_retriever_start(
            query,
            {
                "retriever_type": self.__class__.__name__,
                "num_retrievers": len(self.retrievers),
                "resource_type": self.resource_type,
                "action": self.action,
            },
        )

        try:
            # Get documents from ensemble retrievers
            docs = await super()._aget_relevant_documents(
                query, run_manager=run_manager, **kwargs
            )

            run_manager.on_event(
                "ensemble_retrieval_complete", {"retrieved_count": len(docs)}
            )

            # Apply permission filtering
            filtered_docs = await self._filter_by_permissions(docs)

            run_manager.on_retriever_end(
                filtered_docs,
                {
                    "initial_count": len(docs),
                    "permitted_count": len(filtered_docs),
                    "filtered_out": len(docs) - len(filtered_docs),
                },
            )

            return filtered_docs

        except Exception as e:
            run_manager.on_retriever_error(f"{e.__class__.__name__}: {str(e)}")
            raise

    def get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: Optional[CallbackManagerForRetrieverRun] = None,
        **kwargs: Any,
    ) -> List[Document]:
        """Synchronous entry point that wraps the async retrieval."""
        import asyncio

        try:
            # Attempt to use asyncio.run() if no event loop is running.
            return asyncio.run(self._aget_relevant_documents(query, **kwargs))
        except RuntimeError:
            # If there's an active event loop, fall back to get_event_loop().
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(
                self._aget_relevant_documents(query, **kwargs)
            )
