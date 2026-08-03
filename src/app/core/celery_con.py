from celery import Celery

celery_app = Celery(
    'udemy',
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)

celery_app.conf.imports = (
    "app.tasks.subtitles",
)