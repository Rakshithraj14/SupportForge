import asyncio

from app.services.knowledge_service import process_document
from app.workers.celery_app import celery_app


@celery_app.task(name="ingest_document")
def ingest_document_task(document_id: int, filename: str, file_path: str) -> None:
    asyncio.run(process_document(document_id, filename, file_path))
