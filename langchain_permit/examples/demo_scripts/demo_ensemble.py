import os
import asyncio
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_permit.retrievers import PermitEnsembleRetriever

# Permissions query configuration for the retriever
# The user ID we want to filter the results for (should be synced to Permit's PDP)
USER = "user_abc"
# The name of the resource in the policy we configured in Permit
RESOURCE_TYPE = "my_resource"
# The particular action we want to filter for (usually read, view, etc.)
ACTION = "view"

async def main():
    # 1. Create some sample documents
    texts = [
        ("doc_a", "Cats are wonderful creatures, often beloved by humans."),
        ("doc_b", "Dogs are quite loyal and friendly."),
        ("doc_c", "Birds can fly; interesting facts about cats and dogs too."),
        ("doc_d", "Random text about fish."),
    ]
    docs = [Document(page_content=txt, metadata={"id": idx}) for (idx, txt) in texts]

    # 2. Build an in-memory vector store for the vector-based retriever
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(docs, embedding=embeddings)
    vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 2})
    

    # 3. Initialize the PermitEnsembleRetriever with the relevant user/resource/action information for filtering
    ensemble_retriever = PermitEnsembleRetriever(
        api_key=os.getenv("PERMIT_API_KEY", ""),  # or a hard-coded string for testing
        pdp_url=os.getenv("PERMIT_PDP_URL"),   
        user=USER,
        action=ACTION,
        resource_type=RESOURCE_TYPE,
        retrievers=[vector_retriever],
        weights=None  # or [0.5, 0.5], etc. if you want weighting
    )

    # 4. Run a query to be performed with the filtering capabilties
    query = "Tell me about cats"
    results = await ensemble_retriever._aget_relevant_documents(query, run_manager=None)

    # 5. Print out the filtered results
    print(f"Query: {query}")
    for i, doc in enumerate(results, start=1):
        doc_id = doc.metadata.get("id")
        content = doc.page_content
        print(f"Result #{i} (doc id: {doc_id}): {content}")

if __name__ == "__main__":
    asyncio.run(main())
