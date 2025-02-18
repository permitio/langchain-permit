import os
import asyncio
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain_openai import OpenAIEmbeddings
from langchain_permit.retrievers import PermitEnsembleRetriever

# Feel free to tailor the policy model (RBAC, ABAC, ReBAC) in Permit for your real environment

USER = "user_abc"
RESOURCE_TYPE = "my_resource"
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

    # 3. Build a BM25 retriever from the same documents
    bm25_retriever = BM25Retriever.from_texts(
        [d.page_content for d in docs],
        metadatas=[d.metadata for d in docs],
        k=2,
    )

    # 4. Initialize the PermitEnsembleRetriever with both retrievers
    ensemble_retriever = PermitEnsembleRetriever(
        api_key=os.getenv("PERMIT_API_KEY", ""),  # or a hard-coded string for testing
        pdp_url=os.getenv("PERMIT_PDP_URL"),      # optional
        user=USER,
        action=ACTION,
        resource_type=RESOURCE_TYPE,
        retrievers=[bm25_retriever, vector_retriever],
        weights=None  # or [0.5, 0.5], etc. if you want weighting
    )

    # 5. Run a query
    query = "Tell me about cats"
    results = await ensemble_retriever._aget_relevant_documents(query, run_manager=None)

    # 6. Print out the results
    print(f"Query: {query}")
    for i, doc in enumerate(results, start=1):
        doc_id = doc.metadata.get("id")
        content = doc.page_content
        print(f"Result #{i} (doc id: {doc_id}): {content}")

if __name__ == "__main__":
    asyncio.run(main())
