# MLLM Training Report | Date: 2026-06-17 | MLLM-Geo-AI Project

## 1. MLLM Training Endpoints

| Endpoint | Status | Notes |
|----------|--------|-------|
| POST /api/v1/mllm/train | ✅ IMPLEMENTED | 202 Accepted with validation |
| GET /api/v1/mllm/train-status/{job_id} | ✅ IMPLEMENTED | Same pattern as classify-status |
| GET /api/v1/mllm/export/{job_id} | ❌ MISSING | Not implemented |
| GET /api/v1/mllm/model-card/{job_id} | ❌ MISSING | Not implemented |

## 2. Training Implementation

The `train_mllm_task` (Celery task) supports:
- Loading CSV datasets with `label` and `text_des` columns
- POI embedding via `Embedder`
- Image encoding via `ImageEncoder`
- MLP training with configurable epochs, batch_size, learning_rate
- Model checkpoint saving to `data/models/trained/`
- Cancel handling (checks for cancelled status during training)

**Validation** at API level:
- dataset_path required and must exist
- Supported extensions: .csv, .json, .geojson
- epochs: 1-100
- batch_size: 1-1024

## 3. Issues

1. **No mllm/export endpoint**: Trained models can't be downloaded via API
2. **No mllm/model-card endpoint**: No model metadata output
3. **MllmTrainer class** (`app/infrastructure/mllm_trainer.py`) uses `peft` (LoRA) but `peft` is NOT installed, causing import error in test_mllm_trainer.py
4. **Training is MLP only**: True MLLM (LLM fine-tuning) is not implemented — `MllmTrainer` exists but isn't connected to the API

## 4. Evidence Matrix

| Item | Code Verified | Runtime Verified | Evidence Attached |
|------|:-------------:|:----------------:|:-----------------:|
| POST /mllm/train | YES | YES (validation) | YES |
| GET /train-status | YES | YES | YES |
| GET /mllm/export | NO | NO | NO |
| GET /model-card | NO | NO | NO |
| Celery task | YES | YES (9 runs) | YES |
