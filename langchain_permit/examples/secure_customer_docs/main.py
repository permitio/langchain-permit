from config import PERMIT_API_KEY, PERMIT_PDP_URL, JWKS_URL
from langchain_permit.tools import LangchainJWTValidationTool, LangchainPermissionsCheckTool
from permit import Permit, User
# from langchain.docstore.document import Document
# from langchain_community.vectorstores import Chroma
from langchain_openai.llms import OpenAI
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_permit.retrievers import PermitSelfQueryRetriever,PermitEnsembleRetriever
PermitSelfQueryRetriever.model_rebuild()
import os
from langchain_community.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import asyncio
from langchain_community.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
# from langchain_community.chat_models import ChatOpenAI
from langchain.schema import Document


# Initialize embeddings and documents
llm = ChatOpenAI(temperature=0)
embeddings = OpenAIEmbeddings()

# Example documents - replace with your actual documents
sample_documents = [
    Document(
        page_content="Example document 1 content",
        metadata={
            "id": "doc1",
            "resource_type": "document"
        }
    ),
    Document(
        page_content="Example document 2 content",
        metadata={
            "id": "doc2",
            "resource_type": "document"
        }
    )
]

# Create vector store
vectorstore = Chroma.from_documents(
    documents=sample_documents,
    embedding=embeddings
)

async def retrieve_documents(user_claims, query: str):
    """Retrieve documents using PermitSelfQueryRetriever."""
    try:
        # Create Permit User object from claims
        # permit_user = User(
        #     key=user_claims['sub'],
        #     name=user_claims['name']
        # )
        
        user_dict = {
            "key": user_claims['sub'],
            "name": user_claims['name']
        }

        # Initialize retriever
        retriever = PermitSelfQueryRetriever(
            llm=llm,
            vectorstore=vectorstore,
            user=user_dict, 
            resource_type="document",
            action="read",
            api_key=PERMIT_API_KEY,
            pdp_url=PERMIT_PDP_URL
        )

        # Get relevant documents
        docs = retriever.get_relevant_documents(query)
        
        print(f"Retrieved {len(docs)} permitted documents:")
        for doc in docs:
            print(f"- Document ID: {doc.metadata.get('id')}")
            print(f"  Content: {doc.page_content[:100]}...")
            
        return docs
        
    except Exception as e:
        print(f"Error retrieving documents: {str(e)}")
        return []

# Initialize JWT validation tool
jwt_validator = LangchainJWTValidationTool(
    jwks_url=JWKS_URL
)

permit_client = Permit(
    token=PERMIT_API_KEY,
    pdp=PERMIT_PDP_URL
)

permissions_checker = LangchainPermissionsCheckTool(
    name="permission_check",
    description="Check user permissions for documents",
    permit=permit_client,
)

llm = ChatOpenAI(
    temperature=0,
    model="gpt-3.5-turbo"
)
            
async def validate_jwt_token(token: str):
    """Test JWT token validation using our validator."""
    try:
        claims = await jwt_validator._arun(token)
        print("Token validated successfully!")
        print("Claims:", claims)
        return claims
    except Exception as e:
        print("Token validation failed:", str(e))
        return None

async def check_permissions(user_claims):
    """Test permission checking using validated claims."""
    try:
        print("permit client", permit_client)
        # Create a Permit User object from JWT claims
        user = {
            "key": user_claims['sub'],
            "name": user_claims['name']
        }
        print("User object created:", user)
        
        # Test permission check
        result = await permissions_checker._arun(
            user=user,
            action="read",
            resource="document"
        )
        print("Permission check result:", result)
        return result
    except Exception as e:
        print("Permission check failed:", str(e))
        return None
        
if __name__ == "__main__":
    test_token = os.getenv("TEST_TOKEN")
    # asyncio.run(validate_jwt_token(test_token))
    # async def main():
    #     claims = await validate_jwt_token(test_token)
    #     if claims:
    #         await check_permissions(claims)
    
    # asyncio.run(main())
    async def main():
        # First validate JWT token
        claims = await validate_jwt_token(test_token)
        if claims:
            # Check permissions
            has_permission = await check_permissions(claims)
            if not has_permission:
                # Perform document retrieval
                query = "Find me documents about example content"
                docs = await retrieve_documents(claims, query)
                
                # You can now use these documents for your RAG pipeline
                if docs:
                    print("\nSuccessfully retrieved permitted documents!")
                else:
                    print("\nNo permitted documents found.")
            else:
                print("\nUser does not have permission to access documents.")
        else:
            print("\nFailed to validate JWT token.")

    asyncio.run(main())
    
