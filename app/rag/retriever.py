from app.rag.embedder import embed_query
from app.rag.indexer import COLLECTION_NAME, get_qdrant_client


async def search(query: str, top_k: int = 5) -> list[str]:
    client = get_qdrant_client()
    query_vector = await embed_query(query)
    response = await client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k,
    )
    return [point.payload["text"] for point in response.points]
