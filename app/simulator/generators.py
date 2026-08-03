from app.llm.client import get_ollama_client
from app.simulator.personas import PERSONAS


async def generate_customer_message(persona: str, incident_description: str) -> str:
    client = get_ollama_client()
    user_prompt = (
        f"Incident: {incident_description}\n\n"
        "Write a single realistic support message (1-3 sentences) that this customer "
        "would send about this incident. Reply with only the message, no preamble."
    )
    return await client.chat(
        [
            {"role": "system", "content": PERSONAS[persona]},
            {"role": "user", "content": user_prompt},
        ]
    )
