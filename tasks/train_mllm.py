"""
 * Celery MLLM training task.
"""

from celery_app import celery_app


@celery_app.task(bind=True)
def train_mllm_task(
    self,
    job_id: str,
    model_name: str,
    dataset_path: str,
    epochs: int,
    batch_size: int
):
    from app.infrastructure.job_store import JobStore

    store = JobStore()

    try:

        store.update_job(
            job_id,
            status="running",
            step="preparing_dataset",
            progress=0.1
        )

        # Dataset preparation placeholder

        store.update_job(
            job_id,
            step="training",
            progress=0.5
        )

        # Training placeholder

        store.update_job(
            job_id,
            step="saving_model",
            progress=0.9
        )

        # Save model placeholder

        store.update_job(
            job_id,
            status="completed",
            step="done",
            progress=1.0
        )

    except Exception as e:

        store.update_job(
            job_id,
            status="failed",
            error=str(e)
        )

        raise