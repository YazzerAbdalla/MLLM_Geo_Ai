"""Celery tasks package."""
from .load_area import load_area_task
from .classify import classify_task
from .train_mllm import train_mllm_task