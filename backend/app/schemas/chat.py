from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: str


class ChatResponse(BaseModel):
    reply: str
    remaining_prompts: int
    available: bool
    sources: list[str] = []
