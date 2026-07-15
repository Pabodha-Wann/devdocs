import os
import tempfile
import shutil
import stat
from git import Repo
from langchain_text_splitters import RecursiveCharacterTextSplitter,Language
from langchain_core.documents import Document
from git.exc import GitCommandError
from app.db import db
import logging
from typing import Tuple

from config import (
    CHUNK_SIZE, CHUNK_OVERLAP, BATCH_SIZE, MAX_FILE_SIZE,
    BLOCKED_DIRS, BINARY_EXTENSIONS,EXTENSION_TO_LANGUAGE,IGNORED_FILES
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


# Generate directory tree string
def generate_directory_tree(repo_path: str) -> str:
    tree_lines = ["[REPOSITORY DIRECTORY STRUCTURE AND FILE TREE]", "This document shows the complete folder and file structure of the repository.", ""]
    
    for root, dirs, files in os.walk(repo_path):
        # Filter blocked directories in-place to avoid walking them
        dirs[:] = [d for d in dirs if not any(blocked in os.path.join(root, d).split(os.sep) for blocked in BLOCKED_DIRS)]
        
        rel_path = os.path.relpath(root, repo_path)
        level = 0 if rel_path == '.' else rel_path.count(os.sep) + 1
            
        indent = ' ' * 4 * level
        if rel_path != '.':
            tree_lines.append(f"{indent}[DIR] {os.path.basename(root)}/")
        else:
            tree_lines.append("[ROOT]")
            
        sub_indent = ' ' * 4 * (level + 1)
        for f in sorted(files):
            if f not in IGNORED_FILES and not is_binary_file(os.path.join(root, f)):
                tree_lines.append(f"{sub_indent}{f}")
                
    return "\n".join(tree_lines)


# Extract readable code files from repo
def extract_code_files(repo_path: str) -> list[Document]:
        docs = []

        try:
            # Generate and add directory tree as the first document
            tree_content = generate_directory_tree(repo_path)
            docs.append(Document(
                page_content=tree_content,
                metadata={"source": "DIRECTORY_TREE.txt"}
            ))

            for root,_,files in os.walk(repo_path):
                if any(blocked in root.split(os.sep) for blocked in BLOCKED_DIRS):
                    continue
                
                for file in files:

                    if file in IGNORED_FILES:
                        continue

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
            
            return docs

        except RepositoryEmptyError:
            raise
        except Exception as e:
            logger.error(f"Extraction error: {str(e)}")
            raise RepositoryEmptyError(f"Failed to extract files: {str(e)}")    


# Split docments into chunks with metadata
def chunk_documents(documents: list[Document],url: str) -> list[Document]:
         
    try:
        logger.info(f"Chunking {len(documents)} documents...")
       
        all_chunks = []

        for doc in documents:
            file_path = doc.metadata["source"]

            # Extract folder info
            folders = os.path.dirname(file_path) # Get all folders except filename
            file_name = os.path.basename(file_path)
            ext = os.path.splitext(file_name)[1].lower()

            # Fix: Standardize folder path and correctly calculate depth
            folder_path = folders.replace(os.sep, "/") if folders else ""
            depth = len(folder_path.split("/")) if folder_path else 0

            # Create enhanced document with path info
            enhanced_doc = Document(
                page_content=f"FILE: {file_path}\nFOLDER: {folder_path}\n\n{doc.page_content}",
                metadata={
                    "source": file_path,
                    "folder": folder_path,
                    "file_name": file_name,
                    "depth": depth,  # How nested is this file
                    "repo_url": url
                }
            )

            # enhanced_docs.append(enhanced_doc)

            # Smart rotig engine
            if ext in EXTENSION_TO_LANGUAGE:
                target_lang = EXTENSION_TO_LANGUAGE[ext]
                logger.debug(f"Using smart language splitter ({target_lang}) for: {file_name}")

                splitter=RecursiveCharacterTextSplitter.from_language(
                    language=target_lang,
                    chunk_size = CHUNK_SIZE,
                    chunk_overlap=CHUNK_OVERLAP
                )
            
            else:
                logger.debug(f"Falling back to text splitter for: {file_name}")
                # Splitting
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=CHUNK_SIZE,
                    chunk_overlap=CHUNK_OVERLAP,
                    separators=["\n\nclass ", "\n\ndef ", "\n\n", "\n", " ", ""]
                )

            file_chunks = splitter.split_documents([enhanced_doc])
            all_chunks.extend(file_chunks)

        logger.info(f"Created total of {len(all_chunks)} smart code chunks")
        return all_chunks

    except Exception as e:
        logger.error(f"Chunking error: {str(e)}")
        raise e




def clone_and_embed(url:str) -> Tuple[int,int]:
        
    repo_path = None

    try:
        # Warm up the Neon serverless database before doing any real work.
        # Neon can take a few seconds to wake from a cold start, and without
        # this, the first ingestion attempt often fails with a timeout error.
        logger.info("Pinging database to ensure connection is warm...")
        try:
            db.similarity_search("warmup ping", repo_url="warmup", k=1)
        except Exception:
            pass  # Ignore errors — this is just a warm-up, not critical

        # Clone
        repo_path = clone_repository(url)

        # Extract
        documents = extract_code_files(repo_path)
        num_files= len(documents)

        # Chunk
        chunks = chunk_documents(documents,url)



        # Embedding
        logger.info(f"Generating embeddings for {len(chunks)} chunks...")

        logger.info(f"Checking for existing data for {url} to clear duplicates...")
        db.delete_by_repo(repo_url=url)

        # Send chunks to HuggingFace/Neon in batches of 50 to avoid Payload limits
        # db.recreate_collection()
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
