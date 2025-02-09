# from typing import Type

# from langchain_permit.retrievers import LangchainPermitRetriever
# from langchain_tests.integration_tests import (
#     RetrieversIntegrationTests,
# )


# class TestLangchainPermitRetriever(RetrieversIntegrationTests):
#     @property
#     def retriever_constructor(self) -> Type[LangchainPermitRetriever]:
#         """Get an empty vectorstore for unit tests."""
#         return LangchainPermitRetriever

#     @property
#     def retriever_constructor_params(self) -> dict:
#         return {"k": 2}

#     @property
#     def retriever_query_example(self) -> str:
#         """
#         Returns a dictionary representing the "args" of an example retriever call.
#         """
#         return "example query"


from typing import Type

from langchain_permit.retrievers import LangchainPermitRetriever
from langchain_tests.integration_tests import RetrieversIntegrationTests

class TestLangchainPermitRetriever(RetrieversIntegrationTests):
    @property
    def retriever_constructor(self) -> Type[LangchainPermitRetriever]:
        """Get LangchainPermitRetriever for tests."""
        return LangchainPermitRetriever

    @property
    def retriever_constructor_params(self) -> dict:
        """Provide default parameters for retriever."""
        return {"k": 3}  # Match the default in the original implementation

    @property
    def retriever_query_example(self) -> str:
        """
        Provide a generic query that will match something.
        """
        return "example"  # A query that will match something in mock documents