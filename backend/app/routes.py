from fastapi import APIRouter, HTTPException
from pydantic import BaseModel,field_validator,Field
from typing import List,Dict
import re
import logging
from uuid import uuid4

from config import GITHUB_URL_PATTERN
from exceptions import DevDocsError,ERROR_STATUS_CODES
from app.ingestion import clone_and_embed
from app.retrieval import search_codebase
from app.llm import llm


logger = logging.getLogger(__name__)
router = APIRouter()

 
class IngestRepoRequest(BaseModel):
    url:str = Field(...,max_length=200)

    @field_validator('url')
    @classmethod
    def validate_url(cls,v:str) -> str:
        v = v.strip()
        if not re.match(GITHUB_URL_PATTERN,v):
            raise ValueError(
                'Invalid GitHub URL. Use: https://github.com/owner/repo'
            )
        return v.strip('/')


class ChatMessage(BaseModel):
    role:str
    content: str = Field(..., min_length=1, max_length=5000)

    @field_validator('role')
    @classmethod
    def validate_role(cls,v:str)->str:
        if v not in ('user','assistant'):
            raise ValueError("Role must be 'user' or 'assistant'")
        return v
    


class ChatWithRepoRequest(BaseModel):
    repo_url: str = Field(..., max_length=200)
    messages: List[ChatMessage] = Field(...,min_items=1)

    @field_validator('repo_url')
    @classmethod
    def validate_repo_url(cls, v: str) -> str:
        v = v.strip()
        if not re.match(GITHUB_URL_PATTERN, v):
            raise ValueError('Invalid GitHub URL context.')
        return v.strip('/')

    @field_validator('messages')
    @classmethod
    def validate_last_message(cls,v:List[ChatMessage])->  List[ChatMessage]:
        if v[-1].role != 'user':
            raise ValueError("Last message must be from user")
        return v




# Response models
class CodeChunk(BaseModel):
    source: str
    content: str

class IngestRepoResponse(BaseModel):
    message: str
    files_scanned: int
    chunks_created: int
    status: str = "success"

class ChatResponse(BaseModel):
    answer: str
    sources : List[CodeChunk]
    status: str = "success"

class ErrorResponse(BaseModel):
    status: str = "error"
    error_code: str
    message: str
    request_id: str




@router.post("/ingest-repo",response_model=IngestRepoResponse)
async def ingest_repo(request:IngestRepoRequest):

    request_id = str(uuid4())[:8]

    try:
        logger.info(f"[{request_id}] Ingest:{request.url}")

    
        files_scanned,chunks_created = clone_and_embed(request.url)

        return IngestRepoResponse(
            message ="Repository successfully embedded into pgVector Store!",
            files_scanned = files_scanned,
            chunks_created =  chunks_created,
            status = "success"
        )
    
    except DevDocsError as e:
        logger.warning(f"[{request_id}] {e.code}")
        raise HTTPException(
            status_code=ERROR_STATUS_CODES.get(type(e),400),
            detail=e.message
        )
    


    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error: {str(e)}",exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
    

@router.post("/chat",response_model=ChatResponse)
async def chat_with_repo(request: ChatWithRepoRequest):

    request_id = str(uuid4())[:8]

    try:
        logger.info(f"[{request_id}] Chat request")

        # Convert Pydantic models to dicts
        messages = [msg.model_dump() for msg in request.messages]

        current_question = messages[-1]["content"]
        sources = search_codebase(query=current_question,repo_url=request.repo_url)

        if not sources:
            return ChatResponse(
                answer="I couldn't find any code related to that question.",
                sources= []
            )

     
        final_answer = llm.generate_answer(messages,sources)

        logger.info(f"[{request_id}] Success")
        
        return ChatResponse(
            answer = final_answer,
            sources =[
                CodeChunk(source=s["source"], content=s["content"])
                for s in sources
            ]
        )

    except DevDocsError as e:
        logger.warning(f"[{request_id}] {e.code}")

        raise HTTPException(
            status_code=ERROR_STATUS_CODES.get(type(e),400),
            detail=e.message
        )

    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error: {str(e)}", exc_info=True)

        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.get("/health")
async def health_check():
    """Health check"""
    return {"status": "ok"}


@router.delete("/clear-database-completely")
async def clear_database():
    try:
        from app.db import db
        db.delete_collection()
        return {"message": "Neon database wiped clean successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))