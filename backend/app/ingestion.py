import os
import tempfile
import shutil
import stat
from git import Repo
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

DB_DIR = os.path.join(os.getcwd(),"chroma_store")

def remove_readonly(func,path,excinfo):
    os.chmod(path,stat.S_IWRITE)
    func(path)

def clone_and_embed(url:str):
    temp_dir = tempfile.mkdtemp()

    try:
        print(f'Cloning {url}...')
        Repo.clone_from(url,temp_dir)

        allowed_extensions = ['.js', '.jsx', '.ts', '.tsx', '.py', '.java']
        docs = []

        for root,dirs,files in os.walk(temp_dir):
            for file in files:
                if any(file.endswith(ext) for ext in allowed_extensions):
                    file_path = os.path.join(root,file)

                    try:
                        with open(file_path,'r',encoding='utf-8',errors='ignore') as f: # ensures it reads the code as standard human text,b encoding
                            content = f.read()  

                            docs.append(Document(page_content=content,metadata={"source":file}))

                    except Exception:
                        continue

        shutil.rmtree(temp_dir,onexc=remove_readonly)

        # Procss all collected docs
        if not docs:
            raise Exception("No readable code files found in this repository.")
                    
        # Add this line to see exactly what file it grabbed!
        for doc in docs:
            print("Found file:", doc.metadata["source"])

        
        print(f"Found {len(docs)} files. Chunking....")

        # Splitting
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000,chunk_overlap=200)
        chunks = splitter.split_documents(docs)


        # Embedding
        print(f"Generating embeddings for {len(chunks)} chunks...")
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

        Chroma.from_documents(chunks,embeddings,persist_directory=DB_DIR)

        print("Vector database successfully created!")
        return len(docs),len(chunks)



    
    except Exception as e:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir,onexc=remove_readonly)
        raise Exception(f"Failed to ingest repo: {str(e)}")
