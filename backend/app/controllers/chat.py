from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.ai.assistant import Assistant
from app.core.database import get_db
from app.core.deps import get_optional_user
from app.core.redis_client import get_redis
from app.models import User
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])


def get_assistant(
    db: Session = Depends(get_db),
    redis=Depends(get_redis),
    user: User | None = Depends(get_optional_user),
) -> Assistant:
    return Assistant(db, redis, user=user)


@router.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest, assistant: Assistant = Depends(get_assistant)):
    return assistant.reply(body.message, body.session_id)
