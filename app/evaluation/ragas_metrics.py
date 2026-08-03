from functools import lru_cache

from openai import AsyncOpenAI
from ragas.llms import llm_factory
from ragas.llms.base import InstructorBaseRagasLLM
from ragas.metrics.collections import ContextPrecisionWithoutReference, ContextRecall

from app.config import get_settings


@lru_cache
def get_judge_llm() -> InstructorBaseRagasLLM:
    settings = get_settings()
    client = AsyncOpenAI(base_url=f"{settings.ollama_base_url}/v1", api_key="ollama")
    return llm_factory(settings.ollama_chat_model, client=client)


async def score_context_precision_and_recall(
    question: str, answer: str, context: list[str]
) -> tuple[float, float]:
    llm = get_judge_llm()

    precision_result = await ContextPrecisionWithoutReference(llm=llm).ascore(
        user_input=question, response=answer, retrieved_contexts=context
    )
    recall_result = await ContextRecall(llm=llm).ascore(
        user_input=question, retrieved_contexts=context, reference=answer
    )
    return precision_result.value, recall_result.value
