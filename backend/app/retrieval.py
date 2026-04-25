from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from app.db import db



def search_codebase(query:str,k : int=5):
    print(f"Searching database for: `{query}`")


    # Perform a mathemetical similarity
    results = db.similarity_search(query,k=k)

    formatted_results = []

    for doc in results:
        formatted_results.append({
            "source":doc.metadata.get("source","Unknown File"),
            "content":doc.page_content
        })


    print(f"Found {len(formatted_results)} matching chunks!")
    return formatted_results








    