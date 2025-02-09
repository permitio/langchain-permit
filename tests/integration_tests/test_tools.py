# from typing import Type

# from langchain_permit.tools import LangchainPermitTool
# from langchain_tests.integration_tests import ToolsIntegrationTests


# class TestParrotMultiplyToolIntegration(ToolsIntegrationTests):
#     @property
#     def tool_constructor(self) -> Type[LangchainPermitTool]:
#         return LangchainPermitTool

#     @property
#     def tool_constructor_params(self) -> dict:
#         # if your tool constructor instead required initialization arguments like
#         # `def __init__(self, some_arg: int):`, you would return those here
#         # as a dictionary, e.g.: `return {'some_arg': 42}`
#         return {}

#     @property
#     def tool_invoke_params_example(self) -> dict:
#         """
#         Returns a dictionary representing the "args" of an example tool call.

#         This should NOT be a ToolCall dict - i.e. it should not
#         have {"name", "id", "args"} keys.
#         """
#         return {"a": 2, "b": 3}


# ========> TEST IMPLEMENTATION <=========

from typing import Type
from langchain_permit.tools import LangchainPermitTool
from langchain_tests.integration_tests import ToolsIntegrationTests

class TestPermitToolIntegration(ToolsIntegrationTests):
    @property
    def tool_constructor(self) -> Type[LangchainPermitTool]:
        return LangchainPermitTool

    @property
    def tool_constructor_params(self) -> dict:
        # We don't need any initialization parameters since 
        # the tool will use PERMIT_API_KEY from environment
        return {}

    @property
    def tool_invoke_params_example(self) -> dict:
        """
        Example permission check parameters.
        Tests if 'test_user' has 'read' permission on 'document'.
        """
        return {
            "user": "test_user",
            "action": "read",
            "resource": "document"
        }