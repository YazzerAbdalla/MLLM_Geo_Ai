"""
 * JobStore for tracking asynchronous task progress.
 * Uses Redis for persistence.
 """
import uuid
from typing import Any

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

    def store_grid(self, grid_id: str, grid_data: Any):
        """
         * Store grid metadata or GeoDataFrame in SQLite and local file system.
        """
        import os
        import json
        import geopandas as gpd
        from app.infrastructure.db import SessionLocal
        from app.models.grid import Grid

        gdf = grid_data["gdf"]
        bbox = grid_data["bbox"]

        os.makedirs("data/grids", exist_ok=True)
        geojson_path = f"data/grids/{grid_id}.geojson"

        # Save GeoDataFrame locally
        gdf.to_file(geojson_path, driver="GeoJSON")

        # Save metadata in SQLite
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
        """
         * Retrieve grid data from SQLite and local GeoJSON file.
        """
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