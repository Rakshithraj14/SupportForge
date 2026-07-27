from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Conversation, Message
from app.graph.workflow import get_workflow


async def get_or_create_conversation(db: AsyncSession, chat_id: str) -> Conversation:
    result = await db.execute(
        select(Conversation).where(Conversation.telegram_chat_id == chat_id)
    )
    conversation = result.scalar_one_or_none()
    if conversation is None:
        conversation = Conversation(telegram_chat_id=chat_id)
        db.add(conversation)
        await db.flush()
    return conversation


async def handle_chat_message(db: AsyncSession, chat_id: str, question: str) -> Message:
    conversation = await get_or_create_conversation(db, chat_id)

    user_message = Message(conversation_id=conversation.id, role="user", content=question)
    db.add(user_message)
    await db.flush()

    workflow = get_workflow()
    result = await workflow.ainvoke({"question": question, "context": [], "answer": ""})

    assistant_message = Message(
        conversation_id=conversation.id, role="assistant", content=result["answer"]
    )
    db.add(assistant_message)
    await db.commit()
    await db.refresh(assistant_message)
    return assistant_message
