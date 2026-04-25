import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres.vectorstores import PGVector
from dotenv import load_dotenv


load_dotenv()



embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

CONNECTION_STRING = os.getenv("DATABASE_URL")

db = PGVector(
    embeddings=embeddings,
    collection_name="code_collection",
    connection=CONNECTION_STRING
)