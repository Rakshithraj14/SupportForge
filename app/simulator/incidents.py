from uuid import uuid4

from app.database.session import AsyncSessionLocal
from app.services.chat_service import handle_chat_message
from app.simulator.generators import generate_customer_message
from app.simulator.personas import PERSONAS

INCIDENTS = {
    "payment_gateway_down": (
        "The payment gateway has been down for the last 2 hours, and customers are unable "
        "to complete checkout."
    ),
    "account_locked": (
        "Customers are being incorrectly locked out of their accounts after a recent "
        "security update."
    ),
    "shipping_delay": (
        "Orders placed in the last week are experiencing significant shipping delays due "
        "to a carrier outage."
    ),
}


async def run_incident_simulation(incident_name: str, conversations_per_persona: int = 1) -> list[dict]:
    if incident_name not in INCIDENTS:
        raise ValueError(f"Unknown incident: {incident_name}")
    description = INCIDENTS[incident_name]

    results = []
    for persona in PERSONAS:
        for _ in range(conversations_per_persona):
            chat_id = f"sim-{incident_name}-{persona}-{uuid4().hex[:8]}"
            customer_message = await generate_customer_message(persona, description)

            async with AsyncSessionLocal() as db:
                assistant_message = await handle_chat_message(
                    db, chat_id=chat_id, question=customer_message
                )

            results.append(
                {
                    "persona": persona,
                    "chat_id": chat_id,
                    "message_id": assistant_message.id,
                    "question": customer_message,
                    "answer": assistant_message.content,
                }
            )
    return results
