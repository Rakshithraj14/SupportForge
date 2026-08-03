from functools import lru_cache

from deepeval.metrics import FaithfulnessMetric, HallucinationMetric
from deepeval.models import OllamaModel
from deepeval.test_case import LLMTestCase

from app.config import get_settings


@lru_cache
def get_judge_model() -> OllamaModel:
    settings = get_settings()
    return OllamaModel(model=settings.ollama_chat_model, base_url=settings.ollama_base_url)


async def score_faithfulness_and_hallucination(
    question: str, answer: str, context: list[str]
) -> tuple[float, float]:
    judge = get_judge_model()
    test_case = LLMTestCase(
        input=question,
        actual_output=answer,
        retrieval_context=context,
        context=context,
    )

    faithfulness_score = await FaithfulnessMetric(model=judge, include_reason=False).a_measure(
        test_case
    )
    hallucination_score = await HallucinationMetric(model=judge, include_reason=False).a_measure(
        test_case
    )
    return faithfulness_score, hallucination_score
