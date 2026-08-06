from functools import lru_cache

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.config import get_settings
from app.database.session import AsyncSessionLocal
from app.graph.state import GraphState
from app.llm.client import get_ollama_client
from app.llm.prompts import build_user_prompt, get_active_prompt
from app.monitoring.tracing import get_langfuse_client
from app.rag.retriever import search


async def retrieve_node(state: GraphState) -> dict:
    context = await search(state["question"])
    return {"context": context}


async def generate_node(state: GraphState) -> dict:
    async with AsyncSessionLocal() as db:
        prompt_version = await get_active_prompt(db)

    client = get_ollama_client()
    prompt = build_user_prompt(state["question"], state["context"])
    messages = [
        {"role": "system", "content": prompt_version.content},
        {"role": "user", "content": prompt},
    ]

    langfuse = get_langfuse_client()
    with langfuse.start_as_current_observation(
        name="generate",
        as_type="generation",
        input=messages,
        model=get_settings().ollama_chat_model,
        version=str(prompt_version.version),
    ) as generation:
        answer = await client.chat(messages)
        generation.update(output=answer)

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
