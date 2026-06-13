from app.application.mllm_use_case import MllmUseCase

use_case = MllmUseCase()

result = use_case.start_training(
    source_job_id="embedding_job_001",
    dataset_path="data/train.json"
)

print(result)