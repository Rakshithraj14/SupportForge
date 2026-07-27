from typing import TypedDict


class GraphState(TypedDict):
    question: str
    context: list[str]
    answer: str
