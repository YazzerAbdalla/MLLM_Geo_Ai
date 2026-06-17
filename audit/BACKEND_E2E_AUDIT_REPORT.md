# Backend End-to-End Audit Report

**Date:** 2026-06-17  
**App:** MLLM-Geo-AI-App  
**Auditor:** AI Audit Agent  

---

## Executive Summary

| Area | Status |
|------|--------|
| Environment | ✅ Operational |
| API Endpoints | ✅ 18 endpoints available |
| Area Loading | ✅ Working |
| Classification | ⚠️ Partial |
| Export | ⚠️ Partial |
| Training | ⚠️ Partial |
| Evaluation | ❌ Broken |
| Job Management | ⚠️ Partial |
| Failure Handling | ⚠️ Partial |
| Database | ⚠️ Orphan records |

## Finding Count

- **Critical:** 4
- **High:** 6
- **Medium:** 4
- **Low:** 3

---

## Critical Findings

### C1: Modality filtering is ignored in classification
The `modalities` parameter received by `classify_task` is never passed to `MultiModalClassificationUseCase.execute()`. All modalities are always processed.

### C2: Missing modality dimensions crash fusion
`create_multimodal_feature` always concatenates all 3 modalities (384+256+3=643). Single-modality requests crash with "all input arrays must have the same shape".

### C3: Job status incorrectly set to "completed" on error
When classification fails during fusion, the status is set to "completed" with the error stored separately. The status should be "failed".

### C4: Road density calculation produces unrealistic values
Road density values reach billions (e.g., 802,693,272,762 km/km²) due to incorrect cell area calculation. Realistic max should be ~20-50 km/km².

---

## High Findings

### H1: Evaluation endpoint broken
`PRED_LABEL_CANDIDATES` list does not include `dominant_class`, which is the actual column name in prediction results. Evaluation always fails.

### H2: API validation is bypassed
Missing dataset validation in `/mllm/train` creates a Celery job instead of returning 400 immediately. Task later fails with "Dataset not found".

### H3: No GET endpoint for generic job status
The audit spec expects `GET /jobs/{job_id}`, but only specialized status endpoints exist (`/area-status`, `/classify-status`, `/train-status`).

### H4: Celery worker is stuck processing road network
Single worker with solo pool processes 584MB road graphml sequentially, causing long queue delays.

### H5: Result data stored in Redis causes high memory usage
441 Redis job keys with large result payloads (including GeoJSON for 25+ cells). This will not scale.

### H6: No shapefile export validation
Shapefile export returns a zip file but content validation was not possible due to missing download.

---

## Medium Findings

### M1: `num_cells` shows 0 in area-status response
The API returns `num_cells: 0` for completed jobs because Redis stores it as string "25" and the getter reads `num_cells` from memory store, not Redis.

### M2: SQLite `jobs` table is always empty
All job data goes to Redis/memory. SQLite `jobs` table has 0 rows while `grids` has 24 rows. Potential orphaned grids.

### M3: No training dataset validation for column presence
API validates file extension but not that required columns (`label`, `text_des`) exist. Validation happens in Celery task, wasting resources.

### M4: No performance metrics for classify endpoint
Classify endpoint latency could not be measured due to Celery queue delays from single worker.

---

## Low Findings

### L1: Thumbnail endpoint uses .jpg but files are .png
The thumbnail endpoint returns JPEG but reads .png files. Conversion works but adds latency.

### L2: Swagger docs missing for some endpoints
The WebSocket endpoint is available but not in OpenAPI schema.

### L3: Logging is minimal
No structured logging in API handlers or task workers.

---

## Verdict

**NOT READY**

The system has critical issues that prevent it from being used in any production or defense scenario:
1. Classification with single modalities crashes
2. Modality filtering is completely ignored
3. Evaluation workflow is broken
4. Road density values are mathematically incorrect
5. Overconfidence (confidence=1.0) in most predictions
6. Text embeddings are always zero (no POI data extracted)
