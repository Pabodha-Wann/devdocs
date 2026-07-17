from app.db import db
from typing import List, Dict
from exceptions import InvalidQueryError, DatabaseError
import logging
logger = logging.getLogger(__name__)


def search_codebase(query:str,repo_url: str,k : int=5)-> List[Dict[str,str]]:
    print(f"Searching database for: `{query}`")

    if not query or len(query.strip()) < 3:
        raise InvalidQueryError("Query must be at least 3 characters")
    
    if len(query) > 500:
        raise InvalidQueryError("Query exceeds 500 characters")
    
    try:
        logger.debug(f"Searching: {query}")

        # Perform a mathemetical similarity
        results = db.similarity_search(query,repo_url=repo_url,k=k)

        # format
        formatted_results = []

        for doc in results:
            formatted_results.append({
                "source":doc.metadata.get("source","Unknown File"),
                "content":doc.page_content
            })


        logger.info(f"Found {len(formatted_results)} matching chunks!")
        return formatted_results
    
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise DatabaseError(f"Search failed: {str(e)}")


def get_directory_tree(repo_url: str) -> str:
    """Retrieve the full directory structure of the repository."""
    print(f"Fetching directory tree for {repo_url}...")
    try:
        # Use a dummy query but strict filter to get the exact file
        results = db.similarity_search("DIRECTORY TREE", repo_url=repo_url, k=20)
        
        # Filter strictly in Python just to be safe
        tree_chunks = [doc.page_content for doc in results if doc.metadata.get("source") == "DIRECTORY_TREE.txt"]
        
        if not tree_chunks:
            return "Directory tree not found. It might not have been ingested properly."
            
        return "\n".join(tree_chunks)
    except Exception as e:
        logger.error(f"Failed to fetch directory tree: {str(e)}")
        return f"Error fetching directory tree: {str(e)}"


def read_file_content(file_path: str, repo_url: str) -> str:
    """Retrieve the full contents of a specific file."""
    print(f"Reading file content for `{file_path}`...")
    try:
        results = db.similarity_search(file_path, repo_url=repo_url, k=50)
        
        # Filter strictly to the requested file
        file_chunks = [doc.page_content for doc in results if doc.metadata.get("source") == file_path]
        
        if not file_chunks:
            return f"File '{file_path}' not found in the repository. Please check the directory tree for the exact path."
            
        return "\n".join(file_chunks)
    except Exception as e:
        logger.error(f"Failed to read file {file_path}: {str(e)}")
        return f"Error reading file {file_path}: {str(e)}"