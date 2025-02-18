import os
import asyncio
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_permit.retrievers import PermitSelfQueryRetriever

# Example: Assume we have a user who wants to "view" a certain resource type
USER = {"key": "user_123"}  # or your actual user dict from Permit
RESOURCE_TYPE = "my_resource"
ACTION = "view"

async def main():
    # 1. Create some sample documents
    texts = [
        ("doc1", "Alpha document about cats"),
        ("doc2", "Beta file with info on dogs"),
        ("doc3", "Gamma text referencing birds and cats"),
    ]
    
    # Each doc has an "id" in its metadata to align with Permit checks
    docs = [Document(page_content=txt, metadata={"id": idx}) for (idx, txt) in texts]
    
    # 2. Build a small in-memory vector store
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(docs, embedding=embeddings)
    
    # 3. Initialize the PermitSelfQueryRetriever
    retriever = PermitSelfQueryRetriever(
        api_key=os.getenv("PERMIT_API_KEY", ""),  # or a hard-coded string for testing
        pdp_url=os.getenv("PERMIT_PDP_URL"),      # optional
        user=USER,
        resource_type=RESOURCE_TYPE,
        action=ACTION,
        llm=embeddings,  # In a real example, you'd use a chat model or LLM instance
        vectorstore=vectorstore,
        enable_limit=False,
    )
    
    # 4. Make a query
    query = "Tell me about cats"
    results = await retriever._aget_relevant_documents(query, run_manager=None)
    
    # 5. Print out results
    print(f"Query: {query}")
    for i, doc in enumerate(results, start=1):
        print(f"Result #{i} (doc id: {doc.metadata.get('id')}): {doc.page_content}")

if __name__ == "__main__":
    asyncio.run(main())