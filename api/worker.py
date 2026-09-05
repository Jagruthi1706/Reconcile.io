from celery import Celery

from api.config import get_settings

settings = get_settings()
celery_app = Celery(
    "reconcile",
    broker=settings.redis_url,
    backend=settings.redis_url,
)
celery_app.conf.update(task_ignore_result=False, imports=("api.tasks",))
