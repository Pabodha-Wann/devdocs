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