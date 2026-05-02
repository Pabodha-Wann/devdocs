from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.ingestion import clone_and_embed
from app.retrieval import search_codebase
from app.generate import generate_answer
from typing import List,Dict

router = APIRouter()

 
class RepoRequest(BaseModel):
    url:str

class ChatRequest(BaseModel):
    messages:List[Dict[str,str]]

@router.post("/ingest-repo")
async def ingest_repo(request:RepoRequest):
    try:

        files_scanned,chunks_created = clone_and_embed(request.url)
        return{
            "message":"Repository successfully embedded into pgVector Store!",
            "files_scanned": files_scanned,
            "chunks_created": chunks_created

        }


    except Exception as e:
        raise HTTPException(status_code=400,detail=str(e))
    

@router.post("/chat")
async def chat_with_repo(request: ChatRequest):
    try:
        # exact the entire chat history sent
        chat_history = request.messages

        if not chat_history:
            raise HTTPException(status_code=400,detail="No messages provided")
        
        # get the very last message
        current_question = chat_history[-1]["content"]

        # search the database using ONLY current question
        results = search_codebase(current_question)

        if not results:
            return {
                "answer":"I couldn't find any code related to that question.",
                "sources": []
            }
        
        # pass the whole history
        final_answer = generate_answer(chat_history,results)
        
        return{
            "answer":final_answer,
            "sources":results
        }

    except Exception as e:
        raise HTTPException(status_code=400,detail=str(e))