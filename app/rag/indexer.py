from functools import lru_cache
from uuid import uuid4

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.config import get_settings

COLLECTION_NAME = "documents"
VECTOR_SIZE = 768  # nomic-embed-text output dimension


@lru_cache
def get_qdrant_client() -> AsyncQdrantClient:
    settings = get_settings()
    return AsyncQdrantClient(url=settings.qdrant_url)


async def ensure_collection() -> None:
    client = get_qdrant_client()
    if not await client.collection_exists(COLLECTION_NAME):
        await client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )


async def index_chunks(document_id: int, chunks: list[str], embeddings: list[list[float]]) -> None:
    await ensure_collection()
    client = get_qdrant_client()
    points = [
        PointStruct(
            id=str(uuid4()),
            vector=embedding,
            payload={"document_id": document_id, "text": chunk},
        )
        for chunk, embedding in zip(chunks, embeddings)
    ]
    await client.upsert(collection_name=COLLECTION_NAME, points=points)
