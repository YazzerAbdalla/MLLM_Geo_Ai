# Legacy Failures Report

**Date:** 2026-06-17
**Project:** MLLM-Geo-AI

## Known Issues from Previous Audits

### 1. torch_geometric Dependency Issue

| Status | Detail |
|--------|--------|
| ❌ **STILL FAILING** | `torch_geometric` is installed in `.venv` (version 2.8.0) but NOT in the system Python (`C:\Program Files\Python313`). Running `python -c "import torch_geometric"` with the system Python raises `ModuleNotFoundError`. The project's default `python` command points to system Python, not `.venv`. |

**Verdict:** Works inside `.venv`, fails with default `python` on PATH.

---

### 2. Mock API Mismatch

| Status | Detail |
|--------|--------|
| ✅ **FIXED** | All API endpoints use real implementations. No mock stubs found in route definitions. Review of `app/interfaces/api.py` confirms real implementations for all endpoints. |

**Files confirmed:** `app/interfaces/api.py`, `app/application/use_cases.py`, `app/application/fusion_service.py`

---

### 3. Missing Evaluation Function

| Status | Detail |
|--------|--------|
| ⚠️ **PARTIAL** | Evaluate endpoint exists at `POST /api/v1/evaluate` in `app/interfaces/api.py:452`. Evaluation service exists at `app/application/evaluation_service.py`. However: |
|        | - **No `app.db` SQLite database** with an `evaluations` table could be verified |
|        | - The `app/infrastructure/evaluation_service.py` path does NOT exist (service is in `app/application/`) |
|        | - Runtime was NOT tested with a ground truth file |

---

## Additional Findings

### 4. peft Module Missing

| Status | Detail |
|--------|--------|
| ❌ **STILL FAILING** | `peft` is required by `app/infrastructure/mllm_trainer.py:7` (`from peft import LoraConfig, get_pept_model, TaskType`). The `peft` module is NOT installed in either the system Python or the project `.venv`. |

**Impact:** `mllm_trainer.py` cannot be imported. Any training flow using `train_mllm_task` will fail at import time.

---

### 5. data/train.json Missing

| Status | Detail |
|--------|--------|
| ❌ **STILL FAILING** | `data/train.json` does not exist on disk. The file is referenced indirectly through the training pipeline (`app/application/mllm_use_case.py` passes a `dataset_path` parameter). |

**Impact:** MLLM training tasks cannot proceed without training data.

---

### 6. Graph-Topology Endpoint Returns 500

| Status | Detail |
|--------|--------|
| ⚠️ **NEW ISSUE** | `GET /api/v1/grid/{id}/graph-topology` returns HTTP 500 after ~13.5 seconds. Root cause is the 584MB `data/raw/roads.graphml` file being loaded entirely into memory without streaming or pagination. |

**Impact:** The graph-topology visualization feature is non-functional for the Cairo grid.

---

## Summary Status Table

| #  | Issue                          | Status        | Severity |
|----|--------------------------------|---------------|----------|
| 1  | torch_geometric dependency     | ❌ STILL FAILING (depends on Python env) | High |
| 2  | Mock API mismatch              | ✅ FIXED       | N/A      |
| 3  | Missing evaluation function    | ⚠️ PARTIAL     | Medium   |
| 4  | peft module missing            | ❌ STILL FAILING | High   |
| 5  | data/train.json missing        | ❌ STILL FAILING | High   |
| 6  | Graph-topology 500 error       | ⚠️ NEW ISSUE   | Medium   |

## Evidence Matrix

| Evidence File                                      | Content                                          |
|----------------------------------------------------|--------------------------------------------------|
| `app/infrastructure/mllm_trainer.py:7`             | `from peft import LoraConfig, ...` — will fail   |
| `app/interfaces/api.py:452`                        | `POST /api/v1/evaluate` endpoint definition      |
| `app/application/evaluation_service.py`            | Evaluation service exists (in `application/`, not `infrastructure/`) |
| `data/raw/roads.graphml`                           | 584MB — causes graph-topology 500 error          |
| `data/train.json`                                  | **File does not exist**                          |
| `.venv/Lib/site-packages/torch_geometric/`         | torch_geometric 2.8.0 installed in venv only     |
| System Python: `python -c "import peft"`           | ModuleNotFoundError                              |
