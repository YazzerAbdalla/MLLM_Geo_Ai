import os
from app.infrastructure.job_store import JobStore
from tasks.train_mllm import train_mllm_task


class MllmUseCase:

    def __init__(self):
        self.job_store = JobStore()

    def _validate_training_inputs(self, dataset_path: str, epochs: int, batch_size: int):
        if not dataset_path:
            raise ValueError("dataset_path is required")
        if not os.path.exists(dataset_path):
            raise ValueError(f"Dataset not found: {dataset_path}")
        valid_extensions = (".csv", ".json", ".geojson")
        if not dataset_path.lower().endswith(valid_extensions):
            raise ValueError(f"Unsupported dataset format. Supported: {valid_extensions}")
        if epochs < 1 or epochs > 100:
            raise ValueError("epochs must be between 1 and 100")
        if batch_size < 1 or batch_size > 1024:
            raise ValueError("batch_size must be between 1 and 1024")

    def start_training(
        self,
        source_job_id: str,
        dataset_path: str,
        epochs: int = 3,
        batch_size: int = 4,
        model_name: str = "sshleifer/tiny-gpt2"
    ):
        self._validate_training_inputs(dataset_path, epochs, batch_size)

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