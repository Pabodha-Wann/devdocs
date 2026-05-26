import os
from langchain_postgres.vectorstores import PGVector
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEndpointEmbeddings
import logging
from langchain_core.documents import Document
from typing import List
from exceptions import DatabaseError
from config import DATABASE_URL, HUGGINGFACE_TOKEN, EMBEDDING_MODEL

logger = logging.getLogger(__name__)

class VectorDB:
    def __init__(self):
        try:
            self.embeddings = HuggingFaceEndpointEmbeddings(
                model=EMBEDDING_MODEL,
                huggingfacehub_api_token=HUGGINGFACE_TOKEN
            )

            self.client = PGVector(
                embeddings=self.embeddings,
                collection_name="code_collection",
                connection=DATABASE_URL,
                pre_delete_collection=False
            )

            logger.info("Vector DB initialized")

        except Exception as e:
            logger.error(f"Vector DB init failed: {str(e)}")
            raise DatabaseError(f"Database initialization failed: {str(e)}")
    


    """Add documents to vector DB"""
    def add_documents(self,documents:List[Document])->None:
        try:
            self.client.add_documents(documents)
            logger.info(f"Added {len(documents)} documents")
        except Exception as e:
            logger.error(f"Failed to add documents: {str(e)}")
            raise DatabaseError(f"Failed to store documents:{str(e)}")
    

    """Search for similar documents"""
    def similarity_search(self,query:str,repo_url:str,k:int=5) -> List[Document]:
        try:
            logger.debug("Searching:{query} in {repo_url}")

            # This forces pgvector to ONLY scan items belonging repository
            search_filter = {"repo_url": repo_url}

            results = self.client.similarity_search(query,k=k)
            logger.info(f"Found {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise DatabaseError(f"Vector search failed: {str(e)}")

    """Delete only a specific repository's records (NEW METHOD)"""
    def delete_by_repo(self, repo_url: str) -> None:
        try:
            # filter by metadata fields using dictionary format
            self.client.delete(filter={"repo_url": repo_url})
            logger.info(f"Successfully cleared old chunks for: {repo_url}")
        except Exception as e:
            # If the entire collection table was dropped,
            # catch it here and force PGVector to rebuild the empty table structure!
            if "Collection not found" in str(e) or "relation" in str(e):
                logger.info("Collection table missing. Re-initializing empty collection structures...")
                self.client.create_collection()
            else:
                logger.error(f"Failed to delete records for {repo_url}: {str(e)}")


    """Delete collection for re-ingestion"""
    def delete_collection(self) -> None:
        try:
            self.client.delete_collection()
            logger.info("Collection deleted")
        except Exception as e:
            logger.error(f"Failed to delete collection: {str(e)}")
            raise DatabaseError(f"Failed to clear collection: {str(e)}")

    """Recreate collection after deletion"""
    def recreate_collection(self) -> None:
        try:
            self.client = PGVector(
                embeddings=self.embeddings,
                collection_name="code_collection",
                connection=DATABASE_URL,
                pre_delete_collection=True
            )
            logger.info("Collection recreated")
        except Exception as e:
            logger.error(f"Failed to recreate collection: {str(e)}")
            raise DatabaseError(f"Failed to recreate collection: {str(e)}")


db = VectorDB()

