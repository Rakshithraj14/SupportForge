from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Evaluation, Message
from app.evaluation.deepeval_metrics import score_faithfulness_and_hallucination
from app.evaluation.ragas_metrics import score_context_precision_and_recall


async def evaluate_message(db: AsyncSession, message_id: int) -> Evaluation:
    message = (
        await db.execute(select(Message).where(Message.id == message_id))
    ).scalar_one()

    question_message = (
        await db.execute(
            select(Message)
            .where(Message.conversation_id == message.conversation_id, Message.id < message.id)
            .order_by(Message.id.desc())
            .limit(1)
        )
    ).scalar_one()

    context = message.context or []

    faithfulness, hallucination = await score_faithfulness_and_hallucination(
        question=question_message.content, answer=message.content, context=context
    )
    context_precision, context_recall = await score_context_precision_and_recall(
        question=question_message.content, answer=message.content, context=context
    )

    evaluation = Evaluation(
        message_id=message.id,
        faithfulness=faithfulness,
        hallucination=hallucination,
        context_precision=context_precision,
        context_recall=context_recall,
    )
    db.add(evaluation)
    await db.commit()
    await db.refresh(evaluation)
    return evaluation
