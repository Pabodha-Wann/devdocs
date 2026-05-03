import os
from langchain_postgres.vectorstores import PGVector
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEndpointEmbeddings

load_dotenv()

HF_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")
CONNECTION_STRING = os.getenv("DATABASE_URL")

embeddings = HuggingFaceEndpointEmbeddings(
    model="sentence-transformers/all-MiniLM-L6-v2",
    huggingfacehub_api_token=HF_TOKEN
)

db = PGVector(
    embeddings=embeddings,
    collection_name="code_collection",
    connection=CONNECTION_STRING
)