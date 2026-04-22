from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.ingestion import clone_and_embed
from app.retrieval import search_codebase

router = APIRouter()

 
class RepoRequest(BaseModel):
    url:str

class ChatRequest(BaseModel):
    question:str

@router.post("/ingest-repo")
async def ingest_repo(request:RepoRequest):
    try:

        files_scanned,chunks_created = clone_and_embed(request.url)
        return{
            "message":"Repository successfully embedded into Chroma Store!",
            "files_scanned": files_scanned,
            "chunks_created": chunks_created

        }


    except Exception as e:
        raise HTTPException(status_code=400,detail=str(e))
    

@router.post("/chat")
async def chat_with_repo(request: ChatRequest):
    try:
        results = search_codebase(request.question)

        if not results:
            return {"answer":"I couldn't find any code related to that question.","sources": []}
        
        return{
            
            "sources":results
        }

    except Exception as e:
        raise HTTPException(status_code=400,detail=str(e))