"""Test LangchainPermit embeddings."""

from typing import Type

from langchain_permit.embeddings import LangchainPermitEmbeddings
from langchain_tests.integration_tests import EmbeddingsIntegrationTests


class TestParrotLinkEmbeddingsIntegration(EmbeddingsIntegrationTests):
    @property
    def embeddings_class(self) -> Type[LangchainPermitEmbeddings]:
        return LangchainPermitEmbeddings

    @property
    def embedding_model_params(self) -> dict:
        return {"model": "nest-embed-001"}
