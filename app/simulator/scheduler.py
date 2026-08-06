import asyncio

from app.simulator.incidents import INCIDENTS, run_incident_simulation
from app.workers.celery_app import celery_app
from app.workers.evaluation import evaluate_message_task


@celery_app.task(name="run_scheduled_simulations")
def run_scheduled_simulations_task() -> None:
    asyncio.run(_run_all_incidents())


async def _run_all_incidents() -> None:
    for incident_name in INCIDENTS:
        results = await run_incident_simulation(incident_name, conversations_per_persona=1)
        for result in results:
            evaluate_message_task.delay(result["message_id"])
