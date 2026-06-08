import os
import re
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from rag_engine import generate_response, LLM_MODEL

app = FastAPI(
    title="Mutual Fund FAQ Assistant API",
    description="REST API for facts-only Mutual Fund Q&A using Groww data."
)

# Enable CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    query: str
    response: str
    citation: Optional[str] = None
    model_metadata: dict

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    query_text = request.query.strip()
    if not query_text:
        raise HTTPException(status_code=400, detail="Query text cannot be empty")
        
    try:
        # Generate final response (including safety refuse checks, formatting, and fallback)
        bot_response = generate_response(query_text)
        
        # Extract the markdown source citation link, if present
        citation = None
        match = re.search(r'\[([^\]]+)\]\((https?://[^\)]+)\)', bot_response)
        if match:
            citation = match.group(2)
            
        return ChatResponse(
            query=query_text,
            response=bot_response,
            citation=citation,
            model_metadata={
                "model": LLM_MODEL,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG Engine Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
