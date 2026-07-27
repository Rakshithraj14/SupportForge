SYSTEM_PROMPT = (
    "You are SupportForge, a helpful customer support assistant. "
    "Answer the user's question using only the provided context. "
    "If the context does not contain the answer, say you don't know "
    "instead of guessing."
)


def build_user_prompt(question: str, context_chunks: list[str]) -> str:
    context_block = "\n\n".join(context_chunks) if context_chunks else "No relevant context found."
    return f"Context:\n{context_block}\n\nQuestion: {question}"
