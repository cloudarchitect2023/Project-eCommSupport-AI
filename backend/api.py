from __future__ import annotations

from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from backend.agent import EcommerceSupportAgent
from backend.settings import (
    OPENAI_API_KEY,
    PINECONE_API_KEY,
    PINECONE_INDEX,
    UPSTASH_REDIS_URL,
)

app = FastAPI(title="eCommSupport AI API", version="1.0.0")
agent = EcommerceSupportAgent()


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    session_id: str = Field(min_length=1, max_length=100)
    customer_id: str = Field(min_length=1, max_length=40)
    retrieval_strategy: Literal["simple", "hyde", "multi_query"] = "simple"


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "openai_configured": bool(OPENAI_API_KEY),
        "pinecone_configured": bool(PINECONE_API_KEY and PINECONE_INDEX),
        "persistent_memory_configured": bool(UPSTASH_REDIS_URL),
    }


@app.post("/chat")
async def chat(request: ChatRequest) -> dict[str, object]:
    try:
        return await agent.respond(
            question=request.question,
            session_id=request.session_id,
            customer_id=request.customer_id,
            retrieval_strategy=request.retrieval_strategy,
        )
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
