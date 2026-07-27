from app.llm.client import get_ollama_client


async def embed_chunks(chunks: list[str]) -> list[list[float]]:
    client = get_ollama_client()
    return [await client.embed(chunk) for chunk in chunks]


async def embed_query(text: str) -> list[float]:
    client = get_ollama_client()
    return await client.embed(text)
