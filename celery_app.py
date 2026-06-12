"""
 * Celery application configuration.
"""
import os
from celery import Celery
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "mllm_geo_ai",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["tasks.load_area", "tasks.classify", "tasks.train_mllm"]
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    task_routes={
        "tasks.classify.*": {"queue": "gpu"},
        "tasks.load_area.*": {"queue": "cpu"},
        "tasks.train_mllm.*": {"queue": "cpu"},
    }
)

if os.getenv("TESTING"):
    celery_app.conf.task_always_eager = True