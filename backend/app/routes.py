from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.ingestion import clone_and_embed

router = APIRouter()

 
class RepoRequest(BaseModel):
    url:str


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