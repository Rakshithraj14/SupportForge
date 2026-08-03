from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery("supportforge", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.imports = ("app.workers.ingestion", "app.workers.evaluation")
