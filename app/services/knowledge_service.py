from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Document
from app.rag.chunker import chunk_text
from app.rag.embedder import embed_chunks
from app.rag.indexer import index_chunks
from app.rag.loader import load_document


async def ingest_document(
    db: AsyncSession, filename: str, content_type: str, content: bytes
) -> Document:
    document = Document(filename=filename, content_type=content_type, status="pending")
    db.add(document)
    await db.flush()

    text = load_document(filename, content)
    chunks = chunk_text(text)
    embeddings = await embed_chunks(chunks)
    await index_chunks(document.id, chunks, embeddings)

    document.status = "indexed"
    document.chunk_count = len(chunks)
    await db.commit()
    await db.refresh(document)
    return document
