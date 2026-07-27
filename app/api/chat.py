from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import handle_chat_message

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)) -> ChatResponse:
    message = await handle_chat_message(db, chat_id=request.chat_id, question=request.message)
    return ChatResponse(
        conversation_id=message.conversation_id,
        message_id=message.id,
        answer=message.content,
    )
