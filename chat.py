import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from db import SessionLocal
from models import Chat
from llm import get_ai_response_stream

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    history: list[dict] = Field(default_factory=list)
    files: list[str] = Field(default_factory=list)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/chat")
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    messages = request.history + [{"role": "user", "content": request.message}]

    db.add(Chat(user_id=1, role="user", content=request.message))
    db.commit()

    async def stream_response():
        ai_text = ""
        for chunk in get_ai_response_stream(messages, request.files):
            if chunk.startswith("data:"):
                payload = chunk[len("data:"):].strip()
                if payload and payload != "[DONE]":
                    try:
                        entry = json.loads(payload)
                        ai_text += entry.get("text", "")
                    except json.JSONDecodeError:
                        pass
            yield chunk

        if ai_text:
            db.add(Chat(user_id=1, role="ai", content=ai_text))
            db.commit()

    return StreamingResponse(stream_response(), media_type="text/event-stream")