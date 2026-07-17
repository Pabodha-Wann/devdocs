from fastapi import FastAPI
from app.routes import router
from dotenv import load_dotenv
import os
from fastapi.middleware.cors import CORSMiddleware
import logging
import logging.config

load_dotenv()


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("backend_errors.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="DevDocs RAG API",
    description="Chat with GitHub repositories using RAG",
    version="0.1.0"
)

ALLOWED_FRONTEND = os.getenv("FRONTEND_URL", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_FRONTEND],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect api endpoints
app.include_router(router,prefix="/api")

logger.info("DevDocs RAG API initialized")