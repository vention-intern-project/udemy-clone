from celery import Celery

from app.core.config import settings

redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0"

celery_app = Celery(
    "udemy",
    broker=redis_url,
    backend=redis_url,
)

celery_app.conf.imports = ("app.tasks.subtitles", "app.tasks.uploads")
