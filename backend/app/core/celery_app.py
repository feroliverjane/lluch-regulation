from celery import Celery
from celery.schedules import crontab
from .config import settings

celery_app = Celery(
    "lluch_regulation",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Madrid",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3000,  # 50 minutes
)

# Periodic tasks schedule
celery_app.conf.beat_schedule = {
    "review-composites-daily": {
        "task": "app.tasks.review_composites",
        "schedule": crontab(hour=2, minute=0),  # Run at 2 AM daily
    },
    "cleanup-old-drafts": {
        "task": "app.tasks.cleanup_old_drafts",
        "schedule": crontab(hour=3, minute=0, day_of_week=0),  # Weekly on Sunday at 3 AM
    },
}








