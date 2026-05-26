import os
import tempfile
import shutil
import stat
from git import Repo
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from git.exc import GitCommandError
from app.db import db
import logging
from typing import Tuple

from config import (
    CHUNK_SIZE, CHUNK_OVERLAP, BATCH_SIZE, MAX_FILE_SIZE,
    BLOCKED_DIRS, BINARY_EXTENSIONS
)

from exceptions import (
    InvalidRepositoryError,
    RepositoryCloneError,
    RepositoryEmptyError
)

logger = logging.getLogger(__name__)


# Handle read-only files during cleanup
def remove_readonly(func,path,excinfo):
    os.chmod(path,stat.S_IWRITE)
    func(path)



# Check if file is binary
def is_binary_file(file_path:str) -> bool:
    ext = os.path.splitext(file_path)[1].lower()
    if ext in BINARY_EXTENSIONS:
        return True
    
    try:
        with open(file_path, 'rb') as f:
            return b'\x00' in f.read(8192)
    except Exception:
        return True


# Clone repo to temp directory
def clone_repository(url:str) -> str:

    # Validate URL
    if not url:
        raise InvalidRepositoryError("Repository URL cannot be empty")
    
    if not isinstance(url, str):
        raise InvalidRepositoryError("Repository URL must be a string")

    db.delete_collection()
    db.create_collection()
    print("Cleared previous repo data!")


    temp_dir = tempfile.mkdtemp(prefix="devdocs_repo_")

    try:
        logger.info(f"Cloning: {url}")
        Repo.clone_from(url,temp_dir,depth=1)
        logger.info(f"Cloned to {temp_dir}")
        return temp_dir
    
    except GitCommandError as e:
        logger.error(f"Git error: {str(e)}")
        shutil.rmtree(temp_dir, onerror=remove_readonly)
        raise RepositoryCloneError(
            f"Failed to clone. Check URL is valid: {url}"
        )

    
    except Exception as e:
            logger.error(f"Clone error: {str(e)}")
            shutil.rmtree(temp_dir, onerror=remove_readonly)
            raise RepositoryCloneError(f"Failed to clone repository: {str(e)}. Check that the URL is a valid git repository.")


# Extract readable code files from repo
def extract_code_files(repo_path: str) -> list[Document]:
        docs = []

        try:
            for root,_,files in os.walk(repo_path):
                if any(blocked in root.split(os.sep) for blocked in BLOCKED_DIRS):
                    continue
                
                for file in files:

                    file_path = os.path.join(root,file)

                    # Skipping binary files
                    if is_binary_file(file_path):
                        continue

                    # skipping large files
                    try:
                        if os.path.getsize(file_path) > MAX_FILE_SIZE:
                            logger.debug(f"Skipping large file: {file}")
                            continue

                    except OSError:
                        continue

                    # Read file
                    try:
                        with open(file_path,'r',encoding='utf-8',errors='ignore') as f: # ensures it reads the code as standard human text,before encoding
                            content = f.read() 

                            if content.strip(): 
                                rel_path = os.path.relpath(file_path, repo_path)
                                docs.append(Document(
                                    page_content=content,
                                    metadata={"source":rel_path}
                                ))

                    except Exception as e:
                        logger.debug(f"Error reading {file_path}: {str(e)}")
                        continue


        except RepositoryEmptyError:
            raise
        except Exception as e:
            logger.error(f"Extraction error: {str(e)}")
            raise RepositoryEmptyError(f"Failed to extract files: {str(e)}")    


# Split docments into chunks
def chunk_documents(documents: list[Document]) -> list[Document]:
         
    try:
        logger.info(f"Chunking {len(documents)} documents...")
       

        # Splitting
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\nclass ", "\n\ndef ", "\n\n", "\n", " ", ""]
        )
        chunks = splitter.split_documents(documents)
        logger.info(f"Created {len(chunks)} chunks")
        return chunks

    except Exception as e:
        logger.error(f"Chunking error: {str(e)}")
        raise chunks




def clone_and_embed(url:str) -> Tuple[int,int]:
        
    repo_path = None

    try:
        # clear previos data
        db.delete_collection()

        # Clone
        repo_path = clone_repository(url)

        # Extract
        documents = extract_code_files(repo_path)
        num_files= len(documents)

        # Chunk
        chunks = chunk_documents(documents)



        # Embedding
        logger.info(f"Generating embeddings for {len(chunks)} chunks...")

    
        # Send chunks to HuggingFace/Neon in batches of 50 to avoid Payload limits
        
        for i in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[i : i + BATCH_SIZE]
            print(f"Uploading batch {(i//BATCH_SIZE) + 1}...")
            db.add_documents(batch)

        logger.info(f"Ingestion complete: {num_files} files, {len(chunks)} chunks")


        return len(documents),len(chunks)
    

    except(InvalidRepositoryError, RepositoryCloneError, RepositoryEmptyError):
        raise
    except Exception as e:
        logger.error(f"Ingestion error: {str(e)}")
        raise RepositoryEmptyError(f"Ingestion failed: {str(e)}")


    finally:
        # Clean up
        if repo_path and os.path.exists(repo_path):
            try:
                shutil.rmtree(repo_path,onexc=remove_readonly)
                logger.debug(f"Cleaned up {repo_path}")
            except Exception as e:
                logger.warning(f"Cleanup error: {str(e)}")
