# data_ingestion/celeryconfig.py

from celery.schedules import crontab

beat_schedule = {
    "rebuild-faiss-every-3h": {
        "task": "data_ingestion.celery_app.rebuild_faiss_index",  # <-- match module path!
        "schedule": crontab(minute=0, hour="*/3"),  # every 3 hours
    }
}
 