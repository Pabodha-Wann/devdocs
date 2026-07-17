import os
from dotenv import load_dotenv
from langchain_text_splitters import Language

load_dotenv()

# DB
DATABASE_URL = os.getenv("DATABASE_URL")

# LLM
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-3.1-flash-lite"


# Emedding
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")
EMBEDDING_MODEL= "sentence-transformers/all-MiniLM-L6-v2"

# API
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


# Ingestion settings
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
BATCH_SIZE = 50
MAX_FILE_SIZE = 500_000  # 500KB

BLOCKED_DIRS = {
    'node_modules', '.git', '__pycache__',
    'dist', 'build', '.next', 'venv', '.venv', 'target',
    '.pytest_cache', '.tox', 'htmlcov'
}


BINARY_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.webp',
    '.mp4', '.mp3', '.wav', '.zip', '.tar', '.gz',
    '.exe', '.dll', '.so', '.pyc', '.pdf', '.lock', '.map'
}

IGNORED_FILES = {
    "package-lock.json", 
    "yarn.lock", 
    "pnpm-lock.yaml", 
    ".env", 
    ".gitignore",
    "tsconfig.json"
}

GITHUB_URL_PATTERN = r'^https://github\.com/[\w-]+/[\w._-]+(?:\.git)?/?$'

EXTENSION_TO_LANGUAGE = {
    ".py": Language.PYTHON,
    ".js": Language.JS,
    ".jsx": Language.JS,
    ".ts": Language.TS,
    ".tsx": Language.TS,
    ".go": Language.GO,
    ".cpp": Language.CPP,
    ".html": Language.HTML,
    # Any extension not here fall back to normal text splitting
}