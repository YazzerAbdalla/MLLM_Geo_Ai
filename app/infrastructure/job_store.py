"""
 * JobStore for tracking asynchronous task progress.
 * Uses Redis for persistence with in-memory fallback.
 """
import uuid
from typing import Any

from app.infrastructure.redis_store import RedisJobStore

_redis_store = RedisJobStore()
_MEMORY_JOBS: dict[str, dict] = {}


class JobStore:
    """
     * Centralized store for jobs and grids.
     * Uses Redis with in-memory fallback when Redis is unavailable.
    """
    def __init__(self):
        pass

    def _redis_ok(self) -> bool:
        try:
            return _redis_store.is_available()
        except Exception:
            return False

    def create_job(self, job_type: str) -> str:
        job_id = str(uuid.uuid4())

        memory_job = {
            "id": job_id,
            "type": job_type,
            "status": "pending",
            "progress": 0.0,
            "step": "initialized",
            "error": None,
            "result_url": None,
            "grid_id": None,
            "celery_task_id": None,
            "num_cells": 0,
        }
        _MEMORY_JOBS[job_id] = memory_job

        if self._redis_ok():
            try:
                _redis_store.create_job(job_id, job_type)
            except Exception:
                pass

        return job_id

    def update_job(self, job_id: str, **kwargs):
        if job_id not in _MEMORY_JOBS:
            _MEMORY_JOBS[job_id] = {"id": job_id}

        _MEMORY_JOBS[job_id].update(kwargs)

        if self._redis_ok():
            try:
                _redis_store.update_job(job_id, **kwargs)
            except Exception:
                pass

    def get_job(self, job_id: str):
        if self._redis_ok():
            try:
                job = _redis_store.get_job(job_id)
                if job:
                    return job
            except Exception:
                pass

        return _MEMORY_JOBS.get(job_id)

    def delete_job(self, job_id: str):
        _MEMORY_JOBS.pop(job_id, None)

        if self._redis_ok():
            try:
                _redis_store.delete_job(job_id)
            except Exception:
                pass

    def store_grid(self, grid_id: str, grid_data: Any):
        import os
        import json
        import geopandas as gpd
        from app.infrastructure.db import SessionLocal
        from app.models.grid import Grid

        gdf = grid_data["gdf"]
        bbox = grid_data["bbox"]

        os.makedirs("data/grids", exist_ok=True)
        geojson_path = f"data/grids/{grid_id}.geojson"

        gdf.to_file(geojson_path, driver="GeoJSON")

        db = SessionLocal()
        try:
            db_grid = db.query(Grid).filter(Grid.id == grid_id).first()

            if not db_grid:
                db_grid = Grid(
                    id=grid_id,
                    bbox=json.dumps(bbox),
                    grid_size_m=500,
                    num_cells=len(gdf),
                    status="completed"
                )
                db.add(db_grid)
            else:
                db_grid.bbox = json.dumps(bbox)
                db_grid.num_cells = len(gdf)
                db_grid.status = "completed"

            db.commit()
        finally:
            db.close()

    def get_grid(self, grid_id: str):
        import os
        import json
        import geopandas as gpd
        from app.infrastructure.db import SessionLocal
        from app.models.grid import Grid

        db = SessionLocal()
        try:
            db_grid = db.query(Grid).filter(Grid.id == grid_id).first()
            if not db_grid:
                return None

            geojson_path = f"data/grids/{grid_id}.geojson"
            if not os.path.exists(geojson_path):
                return None

            gdf = gpd.read_file(geojson_path)
            bbox = json.loads(db_grid.bbox)

            return {"gdf": gdf, "bbox": bbox}
        finally:
            db.close()


job_store = JobStore()