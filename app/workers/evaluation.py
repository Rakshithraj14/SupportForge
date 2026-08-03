import asyncio

from app.database.session import AsyncSessionLocal
from app.evaluation.evaluator import evaluate_message
from app.workers.celery_app import celery_app


@celery_app.task(name="evaluate_message")
def evaluate_message_task(message_id: int) -> None:
    asyncio.run(_evaluate(message_id))


async def _evaluate(message_id: int) -> None:
    async with AsyncSessionLocal() as db:
        await evaluate_message(db, message_id)
