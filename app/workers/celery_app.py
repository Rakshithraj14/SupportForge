from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

settings = get_settings()

celery_app = Celery("supportforge", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.imports = (
    "app.workers.ingestion",
    "app.workers.evaluation",
    "app.simulator.scheduler",
)
celery_app.conf.beat_schedule = {
    "nightly-incident-simulation": {
        "task": "run_scheduled_simulations",
        "schedule": crontab(hour=3, minute=0),
    },
}
