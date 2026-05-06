"""
 * Redis JobStore for tracking asynchronous task progress.
 """
import redis
import os
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
        if url is None:
            url = os.getenv("REDIS_URL", "redis://localhost:6379")
        try:
            self.r = redis.from_url(url, decode_responses=True)
            self.r.ping()
            REDIS_AVAILABLE = True
            print(f"Redis connected: {url}")
        except Exception as e:
            if not optional:
                raise RuntimeError(f"Cannot connect to Redis at {url}. Is Redis running?")
            REDIS_AVAILABLE = False
            print(f"WARNING: Redis unavailable: {e}")
            print("         Some features limited without Redis.")

    def create_job(self, job_id: str, job_type: str):
        """
         * Create a new job.
        """
        if not REDIS_AVAILABLE:
            return
        self.r.set(f"job:{job_id}:status", "pending")
        self.r.set(f"job:{job_id}:progress", "0.0")
        self.r.set(f"job:{job_id}:step", "initialized")
        self.r.set(f"job:{job_id}:type", job_type)

    def set_status(self, job_id: str, status: str):
        if not REDIS_AVAILABLE:
            return
        self.r.set(f"job:{job_id}:status", status)

    def set_progress(self, job_id: str, progress: float, step: str):
        if not REDIS_AVAILABLE:
            return
        self.r.set(f"job:{job_id}:progress", str(round(progress, 4)))
        self.r.set(f"job:{job_id}:step", step)

    def update_job(self, job_id: str, **kwargs):
        if not REDIS_AVAILABLE:
            return
        for key, value in kwargs.items():
            full_key = f"job:{job_id}:{key}"
            self.r.set(full_key, str(value))

    def get_job(self, job_id: str):
        if not REDIS_AVAILABLE:
            return None
        status = self.r.get(f"job:{job_id}:status")
        if not status:
            return None
        return {
            "id": job_id,
            "type": self.r.get(f"job:{job_id}:type"),
            "status": status,
            "progress": float(self.r.get(f"job:{job_id}:progress") or 0),
            "step": self.r.get(f"job:{job_id}:step") or "",
            "error": self.r.get(f"job:{job_id}:error"),
            "result_url": self.r.get(f"job:{job_id}:result_url"),
            "grid_id": self.r.get(f"job:{job_id}:grid_id"),
        }

    def delete_job(self, job_id: str):
        if not REDIS_AVAILABLE:
            return
        keys = self.r.keys(f"job:{job_id}:*")
        if keys:
            self.r.delete(*keys)