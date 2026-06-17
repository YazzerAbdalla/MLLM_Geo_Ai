# Audit Finding Validation Report

## Methodology
Each finding from the original audit was independently reproduced, analyzed for root cause, and classified as CONFIRMED, PARTIALLY CONFIRMED, or FALSE POSITIVE.

---

## DEF-001: Classification Status Corruption

| Field | Value |
|-------|-------|
| **Classification** | **CONFIRMED** |
| **Severity** | Critical |
| **Root Cause** | `app/application/fusion_service.py:447-456` — The `except` block sets `status="failed"` but does NOT re-raise the exception. The caller in `tasks/classify.py:28` then unconditionally sets `status="completed"`, overwriting the failure. |
| **Evidence** | `GET /classify-status/{job_id}` returned `{"status": "completed", "error": "all input arrays must have the same shape"}` — contradictory state |
| **Fix Applied** | Added `raise` after `update_job(status="failed")` in `fusion_service.py:457` |

---

## DEF-002: `num_cells` Always Zero

| Field | Value |
|-------|-------|
| **Classification** | **CONFIRMED** |
| **Severity** | High |
| **Root Cause** | `app/infrastructure/redis_store.py:83-101` — `get_job()` only reads specific fields (`id, type, status, progress, step, error, result_url, grid_id, celery_task_id`). It does NOT read `num_cells`. The field is stored correctly via `update_job()` but never retrieved. |
| **Evidence** | `area-status` always returned `{"num_cells": 0}` even when the grid had 25 cells |
| **Fix Applied** | Added `num_cells` to the `get_job()` return dict in `redis_store.py`. Also added `num_cells: 0` to the initial job dict in `job_store.py`. |

---

## DEF-003: Graph Features Always Zero

| Field | Value |
|-------|-------|
| **Classification** | **FALSE POSITIVE** (with underlying real bug discovered) |
| **Severity** | High |
| **Root Cause** | The original audit tested with `modalities=[]` (empty), which legitimately produces zero graph features because no road network data is loaded. When `modalities=["graph"]` is used, graph features ARE correctly loaded (confirmed: `node_count=42-84`, `total_length=16287-18385m`). However, a DIFFERENT real bug was discovered: `attention_fusion()` in `spatial_service.py:83` crashes on `np.stack()` because inputs have different shapes `(384,)`, `(256,)`, `(3,)`. |
| **Evidence** | Grid with `modalities=["graph"]` shows non-zero `node_count`, `total_length`, `avg_degree`. But classification errors with "all input arrays must have the same shape" |
| **Fix Applied** | (1) Wired `fusion_method` parameter through the call chain from API → `classify_task` → `execute()` → `create_multimodal_feature()`. (2) Rewrote `attention_fusion()` to handle different-shaped inputs via norm-based scoring + concatenation. |

---

## DEF-004: MLLM Training Enqueues Invalid Paths

| Field | Value |
|-------|-------|
| **Classification** | **CONFIRMED** |
| **Severity** | High |
| **Root Cause** | `app/interfaces/api.py:474-510` — `POST /mllm/train` accepted any `dataset_path` without validation and queued the task. If the path didn't exist, the Celery worker would fail after queuing. |
| **Evidence** | Observed logs: `Dataset not found: data/train.json` — the task was queued with a non-existent path |
| **Fix Applied** | Added pre-queue validation in the endpoint: checks file exists, supported format (`.csv`, `.json`, `.geojson`), and valid parameter ranges. |

---

## DEF-005: Orphan Grid File

| Field | Value |
|-------|-------|
| **Classification** | **CONFIRMED** |
| **Severity** | Low |
| **Root Cause** | `job_store.py:84-119` — `store_grid()` writes the GeoJSON file first (`gdf.to_file()`), THEN writes to the database. If the process crashes between these two operations, an orphan file is left on disk. |
| **Evidence** | `grid_78d2bf6b.geojson` (8 KB) exists in `data/grids/` but has no corresponding SQLite record. |
| **Fix Applied** | Added `audit_orphan_files()` utility. The `store_grid` now uses a try/finally to clean up orphan files on failure. |

---

## DEF-006: Export Returns 404

| Field | Value |
|-------|-------|
| **Classification** | **PARTIALLY CONFIRMED** |
| **Severity** | High |
| **Root Cause** | Two causes: (1) Because DEF-001 was not fixed, classification "succeeded" with an error but the result file was never written. (2) Even for genuinely completed jobs, the export endpoint did not handle missing files with a useful message. |
| **Evidence** | `GET /export/{job_id}` returned 404 even when the job status was "completed" |
| **Fix Applied** | (1) Fixed DEF-001 so genuinely failed jobs show "failed". (2) Added fallback: if GeoJSON file is missing but `result_data` is available in the job store, the file is regenerated. (3) Added specific error messages for "failed" vs "pending" vs "file missing". |

---

## Summary

| Finding | Status | Severity | Fix Applied |
|---------|--------|----------|-------------|
| DEF-001 | CONFIRMED | Critical | `fusion_service.py` — added `raise` after failed |
| DEF-002 | CONFIRMED | High | `redis_store.py` — added `num_cells` to `get_job()` |
| DEF-003 | FALSE POSITIVE (real bug found) | High | Wired `fusion_method`; fixed `attention_fusion` shapes |
| DEF-004 | CONFIRMED | High | `api.py` — pre-queue validation for MLLM train |
| DEF-005 | CONFIRMED | Low | Added orphan cleanup utility |
| DEF-006 | PARTIALLY CONFIRMED | High | Export endpoint hardened with fallbacks |
