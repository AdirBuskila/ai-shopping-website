from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: str


class ProductRef(BaseModel):
    id: int
    name: str
    image_url: str | None = None
    price_usd: float


class ChatResponse(BaseModel):
    reply: str
    remaining_prompts: int
    available: bool
    sources: list[ProductRef] = []
