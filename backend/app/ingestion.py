import os
import tempfile
import shutil
import stat
from git import Repo
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from app.db import db



def remove_readonly(func,path,excinfo):
    os.chmod(path,stat.S_IWRITE)
    func(path)

BLOCKED_DIRS = {
    'node_modules', '.git', '__pycache__',
    'dist', 'build', '.next', 'venv', '.venv', 'target'
}

BINARY_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.webp', '.bmp',
    '.mp4', '.mp3', '.wav', '.avi', '.mov',
    '.zip', '.tar', '.gz', '.rar', '.7z',
    '.exe', '.dll', '.so', '.pyc', '.class',
    '.woff', '.woff2', '.ttf', '.eot',
    '.pdf', '.bin', '.lock', '.map'
}


def is_binary_file(file_path:str) -> bool:
    ext = os.path.splitext(file_path)[1].lower()
    if ext in BINARY_EXTENSIONS:
        return True
    
    try:
        with open(file_path, 'rb') as f:
            return b'\x00' in f.read(8192)
    except Exception:
        return True



def clone_and_embed(url:str):

    db.delete_collection()
    db.create_collection()
    print("Cleared previous repo data!")


    temp_dir = tempfile.mkdtemp()

    try:
        print(f'Cloning {url}...')
        Repo.clone_from(url,temp_dir)

        # allowed_extensions = ['.js', '.jsx', '.ts', '.tsx', '.py', '.java','.md']


        docs = []

        for root,_,files in os.walk(temp_dir):
            if any(blocked in root.split(os.sep) for blocked in BLOCKED_DIRS):
                continue
            
            for file in files:

                file_path = os.path.join(root,file)

                if is_binary_file(file_path):
                    continue

                if os.path.getsize(file_path) > 500_000:
                    print(f"Skipping large file: {file}")
                    continue


                try:
                    with open(file_path,'r',encoding='utf-8',errors='ignore') as f: # ensures it reads the code as standard human text,before encoding
                        content = f.read() 

                        if content.strip(): 
                            docs.append(Document(
                                page_content=content,
                                metadata={"source":file}
                            ))

                except Exception:
                    continue

        shutil.rmtree(temp_dir,onexc=remove_readonly)

        # Procss all collected docs
        if not docs:
            raise Exception("No readable code files found in this repository.")
                    
        
        for doc in docs:
            print("Found file:", doc.metadata["source"])

        
        print(f"Found {len(docs)} files. Chunking....")

        # Splitting
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = splitter.split_documents(docs)


        # Embedding
        print(f"Generating embeddings for {len(chunks)} chunks...")
        

        db.add_documents(chunks)

        print("Vector database successfully created!")
        return len(docs),len(chunks)



    
    except Exception as e:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir,onexc=remove_readonly)
        raise Exception(f"Failed to ingest repo: {str(e)}")
