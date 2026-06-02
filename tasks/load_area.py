"""
 * Celery load_area task.
"""
import os
from celery_app import celery_app
from dotenv import load_dotenv

load_dotenv()


@celery_app.task(bind=True)
def load_area_task(self, job_id: str, bbox: list, grid_size: int, modalities: list = None):
    import ee
    from app.infrastructure.job_store import JobStore
    from celery.exceptions import Ignore

    # Initialize GEE in this worker process
    project_id = os.getenv('EARTH_ENGINE_PROJECT')
    if project_id:
        try:
            ee.Initialize(project=project_id)
        except Exception as e:
            print(f'GEE init warning: {e}')

    store = JobStore()
    if modalities is None:
        modalities = ["poi", "image", "graph"]

    try:
        job = store.get_job(job_id) or {}

        if job.get("status") == "cancelled":
           raise Ignore()
        
        store.update_job(job_id, status="running", step="generating_grid", progress=0.1)

        from app.domain.spatial_service import generate_grid
        min_x, min_y, max_x, max_y = bbox
        grid_gdf = generate_grid((min_x, min_y, max_x, max_y), cell_size_m=grid_size)

        job = store.get_job(job_id) or {}

        if job.get("status") == "cancelled":
           raise Ignore()

        grid_id = f"grid_{job_id[:8]}"

        store.update_job(job_id, step="downloading_satellite", progress=0.3)
        if "image" in modalities:
            from app.infrastructure.satellite_loader import SatelliteImageLoader
            loader = SatelliteImageLoader()
            loader.download_for_grid(grid_gdf, grid_id)

        job = store.get_job(job_id) or {}

        if job.get("status") == "cancelled":
           raise Ignore()


        store.update_job(job_id, step="downloading_road_network", progress=0.6)
        if "graph" in modalities:
            pass

        store.store_grid(grid_id, {"gdf": grid_gdf, "bbox": bbox})

        store.update_job(job_id, status="completed", step="done", progress=1.0, grid_id=grid_id, num_cells=len(grid_gdf))

    except Exception as e:
        store.update_job(job_id, status="failed", error=str(e))
        raise