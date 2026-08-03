from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.rag.loader import is_supported_file
from app.schemas.knowledge import KnowledgeUploadResponse
from app.services.knowledge_service import create_pending_document
from app.workers.ingestion import ingest_document_task

router = APIRouter()


@router.post("/knowledge/upload", response_model=KnowledgeUploadResponse)
async def upload_knowledge(
    file: UploadFile = File(...), db: AsyncSession = Depends(get_db)
) -> KnowledgeUploadResponse:
    if not is_supported_file(file.filename):
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.filename}")

    content = await file.read()
    document, file_path = await create_pending_document(
        db, filename=file.filename, content_type=file.content_type, content=content
    )
    ingest_document_task.delay(document.id, document.filename, file_path)

    return KnowledgeUploadResponse(
        document_id=document.id,
        filename=document.filename,
        status=document.status,
        chunk_count=document.chunk_count,
    )
