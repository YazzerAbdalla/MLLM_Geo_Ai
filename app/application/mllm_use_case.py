from app.infrastructure.job_store import JobStore
from tasks.train_mllm import train_mllm_task


class MllmUseCase:

    def __init__(self):
        self.job_store = JobStore()

    def start_training(
        self,
        source_job_id: str,
        dataset_path: str,
        epochs: int = 3,
        batch_size: int = 4,
        model_name: str = "sshleifer/tiny-gpt2"
    ):

        job_id = self.job_store.create_job(
            "mllm_training"
        )

        self.job_store.update_job(
            job_id,
            status="queued",
            progress=0.0,
            step="created",
            source_job_id=source_job_id
        )

        train_mllm_task.delay(
            job_id,
            model_name,
            dataset_path,
            epochs,
            batch_size
        )

        return {
            "job_id": job_id,
            "status": "queued"
        }

    def get_status(self, job_id: str):

        return self.job_store.get_job(job_id)