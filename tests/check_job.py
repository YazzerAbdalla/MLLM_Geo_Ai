

from app.infrastructure.job_store import JobStore

store = JobStore()

job_id = "4bb9a144-1ca6-4c21-84ab-cc1895cff95e"

print(
    store.get_job(job_id)
)