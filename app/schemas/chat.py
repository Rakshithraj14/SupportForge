from pydantic import BaseModel


class ChatRequest(BaseModel):
    chat_id: str
    message: str


class ChatResponse(BaseModel):
    conversation_id: int
    message_id: int
    answer: str
