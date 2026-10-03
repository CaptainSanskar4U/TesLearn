from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from utils.llm import chat_reply, check_chat_message_guardrail

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=8000)


class ChatRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=500)
    messages: list[ChatMessage] = Field(min_length=1, max_length=40)


class ChatResponse(BaseModel):
    reply: str
    topic: str


@router.post("", response_model=ChatResponse)
def chat(body: ChatRequest):
    if body.messages[-1].role != "user":
        raise HTTPException(400, "last message must be from user")

    latest = body.messages[-1].content.strip()
    try:
        guard = check_chat_message_guardrail(latest)
    except Exception as exc:
        raise HTTPException(502, f"Guardrail generation failed: {exc}") from exc
    if not guard["allowed"]:
        raise HTTPException(400, guard["reason"])

    try:
        reply = chat_reply(
            body.topic.strip(),
            [m.model_dump() for m in body.messages],
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"Chat generation failed: {exc}") from exc

    return ChatResponse(reply=reply, topic=body.topic.strip())
