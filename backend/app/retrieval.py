from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
import os

DB_DIR = os.path.join(os.getcwd(),"chroma_store")

def search_codebase(query:str,k : int=5):
    print(f"Searching database for: `{query}`")


    
    embedding_model = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

    # load the Chroma store
    vectorstore = Chroma(
        persist_directory=DB_DIR,
        embedding_function=embedding_model
    )

    # Perform a mathemetical similarity
    results = vectorstore.similarity_search(query,k=k)

    formatted_results = []

    for doc in results:
        formatted_results.append({
            "source":doc.metadata.get("source","Unknown File"),
            "content":doc.page_content
        })


    print(f"Found {len(formatted_results)} matching chunks!")
    return formatted_results








    