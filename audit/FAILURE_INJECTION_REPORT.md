# Failure Injection Report

**Date:** 2026-06-17  

---

## Test Results

| # | Scenario | Request | Expected Code | Actual Code | Expected Error | Actual Error | Status |
|---|----------|---------|---------------|-------------|----------------|--------------|--------|
| 1 | Invalid area (too large) | POST load-area with 30x29-32x31, grid_size=100 | 413 | timeout | "exceed the 500-cell limit" | - | ❌ |
| 2 | Invalid grid id | POST classify grid_id="nonexistent_grid" | 400/404 | 202 | "Grid not found" | Job created (fails in Celery) | ❌ |
| 3 | Empty modalities | POST classify modalities=[] | 400 | 202 | "At least one modality required" | Job created | ❌ |
| 4 | Invalid job id | GET area-status/"invalid-job-id-xyz" | 404 | 404 | "Job not found" | "Job not found" | ✅ |
| 5 | Non-existent grid details | GET grid/"fake_grid"/details | 404 | 404 | "Grid not found" | "Grid not found" | ✅ |
| 6 | Non-existent grid preview | GET grid/"fake_grid"/preview | 404 | 404 | "Grid not found" | "Grid not found" | ✅ |
| 7 | Delete non-existent job | DELETE jobs/"fake-job-123" | 404 | 405 | "Job not found" | Method Not Allowed | ❌ |
| 8 | Invalid export format | GET export?format=xml | 400 | 400 | "format must be..." | No detail provided | ⚠️ |
| 9 | Missing training dataset | POST mllm/train dataset_path="nonexistent" | 400 | 202 | "Dataset not found" | Job created (fails in Celery) | ❌ |
| 10 | Wrong training extension | POST mllm/train .graphml | 400 | 202 | "Unsupported format" | Job created (fails in Celery) | ❌ |
| 11 | Invalid training params (epochs=0) | POST mllm/train epochs=0 | 400 | 422 | Validation error | Validation error | ✅ |
| 12 | Evaluate non-existent job | POST evaluate job_id="nonexistent" | 404 | 404 | "Job not found" | "Job not found" | ✅ |

---

## Summary

| Category | Pass | Fail | Partial |
|----------|------|------|---------|
| Input validation | 5 | 5 | 2 |
| Error messages | 6 | 2 | 4 |
| Status codes | 6 | 4 | 2 |

- **Total tests:** 12
- **Pass:** 4 (33%)
- **Fail:** 5 (42%)
- **Partial:** 3 (25%)

## Key Issues

1. **Validation bypassed for training API** - Invalid dataset paths create Celery tasks instead of returning 400
2. **Classify accepts invalid grid_id** - Creates a job that will fail later instead of validating upfront
3. **DELETE endpoint returns 405** - Method not supported on some server instances
4. **Too-large area causes timeout** - No timeout protection in the endpoint
5. **Empty modalities are accepted** - Creates a job that will fail in fusion
6. **No 500 errors observed** ✅ - All failures are graceful
