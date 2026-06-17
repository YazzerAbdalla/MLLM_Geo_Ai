"""
 * Redis JobStore for tracking asynchronous task progress.
 """
import os
import redis
from dotenv import load_dotenv

load_dotenv()

REDIS_AVAILABLE = False


class RedisJobStore:
    """
     * Redis-based store for jobs and grids.
     * Gracefully handles Redis unavailability.
    """
    def __init__(self, url: str = None, optional: bool = True):
        global REDIS_AVAILABLE

        self.r = None
        self.url = url or os.getenv("REDIS_URL", "redis://localhost:6379")

        try:
            self.r = redis.from_url(self.url, decode_responses=True)
            self.r.ping()
            REDIS_AVAILABLE = True
            print(f"Redis connected: {self.url}")
        except Exception as e:
            REDIS_AVAILABLE = False
            self.r = None

            if not optional:
                raise RuntimeError(
                    f"Cannot connect to Redis at {self.url}. Is Redis running?"
                ) from e

            print(f"WARNING: Redis unavailable: {e}")
            print("         Some features limited without Redis.")

    def is_available(self) -> bool:
        """
         * Check whether Redis is currently available.
        """
        if self.r is None:
            return False
        try:
            return bool(self.r.ping())
        except Exception:
            return False

    def create_job(self, job_id: str, job_type: str):
        """
         * Create a new job.
        """
        if not self.is_available():
            return

        self.r.set(f"job:{job_id}:status", "pending")
        self.r.set(f"job:{job_id}:progress", "0.0")
        self.r.set(f"job:{job_id}:step", "initialized")
        self.r.set(f"job:{job_id}:type", job_type)

    def set_status(self, job_id: str, status: str):
        if not self.is_available():
            return
        self.r.set(f"job:{job_id}:status", status)

    def set_progress(self, job_id: str, progress: float, step: str):
        if not self.is_available():
            return
        self.r.set(f"job:{job_id}:progress", str(round(progress, 4)))
        self.r.set(f"job:{job_id}:step", step)

    def update_job(self, job_id: str, **kwargs):
        if not self.is_available():
            return

        for key, value in kwargs.items():
            full_key = f"job:{job_id}:{key}"
            self.r.set(full_key, str(value))

    def get_job(self, job_id: str):
        if not self.is_available():
            return None

        status = self.r.get(f"job:{job_id}:status")
        if not status:
            return None

        num_cells_raw = self.r.get(f"job:{job_id}:num_cells")
        try:
            num_cells = int(num_cells_raw) if num_cells_raw else 0
        except (ValueError, TypeError):
            num_cells = 0

        return {
            "id": job_id,
            "type": self.r.get(f"job:{job_id}:type"),
            "status": status,
            "progress": float(self.r.get(f"job:{job_id}:progress") or 0),
            "step": self.r.get(f"job:{job_id}:step") or "",
            "error": self.r.get(f"job:{job_id}:error"),
            "result_url": self.r.get(f"job:{job_id}:result_url"),
            "grid_id": self.r.get(f"job:{job_id}:grid_id"),
            "celery_task_id": self.r.get(f"job:{job_id}:celery_task_id"),
            "num_cells": num_cells,
        }

    def delete_job(self, job_id: str):
        if not self.is_available():
            return

        keys = self.r.keys(f"job:{job_id}:*")
        if keys:
            self.r.delete(*keys)

            