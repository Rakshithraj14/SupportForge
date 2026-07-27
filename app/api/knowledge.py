from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.knowledge import KnowledgeUploadResponse
from app.services.knowledge_service import ingest_document

router = APIRouter()


@router.post("/knowledge/upload", response_model=KnowledgeUploadResponse)
async def upload_knowledge(
    file: UploadFile = File(...), db: AsyncSession = Depends(get_db)
) -> KnowledgeUploadResponse:
    content = await file.read()
    document = await ingest_document(
        db, filename=file.filename, content_type=file.content_type, content=content
    )
    return KnowledgeUploadResponse(
        document_id=document.id,
        filename=document.filename,
        status=document.status,
        chunk_count=document.chunk_count,
    )
