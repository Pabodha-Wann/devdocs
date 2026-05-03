from fastapi import FastAPI
from app.routes import router
from dotenv import load_dotenv
import os
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI(title="DevDocs rag api")

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