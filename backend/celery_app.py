from celery import Celery
from config import settings

celery_app = Celery(
    "bm_ai_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["tasks.box_tasks"],
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    result_expires=3600,  # Results kept in Redis for 1 hour
    timezone="UTC",
    enable_utc=True,
)
