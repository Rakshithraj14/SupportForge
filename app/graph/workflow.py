from functools import lru_cache

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.graph.state import GraphState
from app.llm.client import get_ollama_client
from app.llm.prompts import SYSTEM_PROMPT, build_user_prompt
from app.rag.retriever import search


async def retrieve_node(state: GraphState) -> dict:
    context = await search(state["question"])
    return {"context": context}


async def generate_node(state: GraphState) -> dict:
    client = get_ollama_client()
    prompt = build_user_prompt(state["question"], state["context"])
    answer = await client.chat(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
    )
    return {"answer": answer}


@lru_cache
def get_workflow() -> CompiledStateGraph:
    graph = StateGraph(GraphState)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("generate", generate_node)
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)
    return graph.compile()
