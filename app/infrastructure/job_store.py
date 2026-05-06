"""
 * JobStore for tracking asynchronous task progress.
 * Uses Redis for persistence.
 """
import uuid
from app.infrastructure.redis_store import RedisJobStore

_redis_store = RedisJobStore()


class JobStore:
    """
     * Centralized store for jobs and grids.
     * Uses Redis exclusively - no in-memory fallback.
    """
    def __init__(self):
        pass

    def _get_store(self):
        return _redis_store

    def create_job(self, job_type: str) -> str:
        """
         * Create a new job and return its ID.
        """
        job_id = str(uuid.uuid4())
        _redis_store.create_job(job_id, job_type)
        return job_id

    def update_job(self, job_id: str, **kwargs):
        """
         * Update an existing job.
        """
        _redis_store.update_job(job_id, **kwargs)

    def get_job(self, job_id: str):
        """
         * Retrieve job info.
        """
        return _redis_store.get_job(job_id)

    def store_grid(self, grid_id: str, grid_data: any):
        """
         * Store grid metadata or GeoDataFrame.
        """
        raise NotImplementedError("Grid storage must be implemented with SQLite")

    def get_grid(self, grid_id: str):
        """
         * Retrieve grid data.
        """
        raise NotImplementedError("Grid storage must be implemented with SQLite")


job_store = JobStore()
