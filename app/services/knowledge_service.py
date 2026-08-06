from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Document
from app.database.session import AsyncSessionLocal
from app.rag.chunker import chunk_text
from app.rag.embedder import embed_chunks
from app.rag.indexer import index_chunks
from app.rag.loader import load_document

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


async def create_pending_document(
    db: AsyncSession, filename: str, content_type: str, content: bytes
) -> tuple[Document, str]:
    document = Document(filename=filename, content_type=content_type, status="pending")
    db.add(document)
    await db.commit()
    await db.refresh(document)

    file_path = UPLOAD_DIR / f"{document.id}_{filename}"
    file_path.write_bytes(content)
    return document, str(file_path)


async def process_document(document_id: int, filename: str, file_path: str) -> None:
    path = Path(file_path)
    try:
        async with AsyncSessionLocal() as db:
            document = (
                await db.execute(select(Document).where(Document.id == document_id))
            ).scalar_one()
            try:
                content = path.read_bytes()
                text = load_document(filename, content)
                chunks = chunk_text(text)
                embeddings = await embed_chunks(chunks)
                await index_chunks(document_id, chunks, embeddings)
                document.status = "indexed"
                document.chunk_count = len(chunks)
            except Exception:
                document.status = "failed"
                raise
            finally:
                await db.commit()
    finally:
        path.unlink(missing_ok=True)
