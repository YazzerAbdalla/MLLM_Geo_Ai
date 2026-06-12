"""
 * Celery classify task.
"""
from celery_app import celery_app


@celery_app.task(bind=True)
def classify_task(self, job_id: str, grid_id: str, modalities: list = None, fusion_method: str = "concat"):
    from app.infrastructure.job_store import JobStore
    from celery.exceptions import Ignore

    store = JobStore()
    if modalities is None:
        modalities = ["poi", "image", "graph"]

    try:
        job = store.get_job(job_id) or {}

        if job.get("status") == "cancelled":
           raise Ignore()
        
        store.update_job(job_id, status="running", step="loading_grid", progress=0.1)

        from app.application.fusion_service import MultiModalClassificationUseCase
        use_case = MultiModalClassificationUseCase()
        use_case.execute(job_id, grid_id)

        store.update_job(job_id, status="completed", step="done", progress=1.0)

    except Ignore:
        store.update_job(job_id, status="cancelled", step="cancelled")
        return   

    except Exception as e:
        store.update_job(job_id, status="failed", error=str(e))
        raise

