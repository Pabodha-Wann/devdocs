from fastapi import FastAPI
from app.routes import router

app = FastAPI(title="DevDocs rag api")

# Connect api endpoints
app.include_router(router,prefix="/api")