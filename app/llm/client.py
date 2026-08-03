from functools import lru_cache

import httpx

from app.config import get_settings
from app.monitoring.prometheus import CHAT_TOKENS


class OllamaClient:
    def __init__(self, base_url: str, chat_model: str, embed_model: str, timeout: float = 60.0):
        self._http = httpx.AsyncClient(base_url=base_url, timeout=timeout)
        self.chat_model = chat_model
        self.embed_model = embed_model

    async def chat(self, messages: list[dict[str, str]]) -> str:
        response = await self._http.post(
            "/api/chat",
            json={"model": self.chat_model, "messages": messages, "stream": False},
        )
        response.raise_for_status()
        body = response.json()

        if "prompt_eval_count" in body:
            CHAT_TOKENS.labels(type="prompt").observe(body["prompt_eval_count"])
        if "eval_count" in body:
            CHAT_TOKENS.labels(type="completion").observe(body["eval_count"])

        return body["message"]["content"]

    async def embed(self, text: str) -> list[float]:
        response = await self._http.post(
            "/api/embeddings",
            json={"model": self.embed_model, "prompt": text},
        )
        response.raise_for_status()
        return response.json()["embedding"]

    async def aclose(self) -> None:
        await self._http.aclose()


@lru_cache
def get_ollama_client() -> OllamaClient:
    settings = get_settings()
    return OllamaClient(
        base_url=settings.ollama_base_url,
        chat_model=settings.ollama_chat_model,
        embed_model=settings.ollama_embed_model,
    )
