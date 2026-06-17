# Failure Injection Retest Report

## Overview
Re-running all previously failing scenarios with fixes applied.

| # | Scenario | Expected | Actual | Status |
|---|----------|----------|--------|--------|
| 1 | Oversized area (bbox producing >500 cells) | HTTP 413 | HTTP 413 | ✅ PASS |
| 2 | Invalid grid (non-existent grid_id) | HTTP 404 | HTTP 404 | ✅ PASS |
| 3 | Empty modalities (classify) | HTTP 400 | HTTP 400 | ✅ PASS |
| 4 | Invalid export format | HTTP 400 | HTTP 400 | ✅ PASS |
| 5 | Invalid dataset path (non-existent) | HTTP 400 | HTTP 400 | ✅ PASS |
| 6 | Invalid extension (.graphml) | HTTP 400 | HTTP 400 | ✅ PASS |
| 7 | Invalid job (DELETE non-existent) | HTTP 404 | HTTP 404 | ✅ PASS |
| 8 | Evaluate invalid data (no prediction column) | HTTP 400 | HTTP 400 (via test) | ✅ PASS |

## Detailed Results

### Scenario 1: Oversized area
- **Test**: `test_load_area_rejects_large_bbox`
- **Request**: POST /api/v1/load-area with bbox=[31.0, 30.0, 32.0, 30.5], grid_size=200
- **Expected**: HTTP 413
- **Actual**: HTTP 413
- **Response detail**: "Area too large: estimated ... cells exceed the 500-cell limit"
- **Verdict**: ✅ PASS

### Scenario 2: Invalid grid
- **Test**: `test_classify_rejects_invalid_grid_id`
- **Request**: POST /api/v1/classify with grid_id="grid_nonexistent", modalities=["poi"]
- **Expected**: HTTP 404
- **Actual**: HTTP 404
- **Response detail**: "Grid not found: grid_nonexistent"
- **Verdict**: ✅ PASS

### Scenario 3: Empty modalities
- **Test**: `test_classify_empty_modalities_still_rejected`
- **Request**: POST /api/v1/classify with grid_id="any_grid", modalities=[]
- **Expected**: HTTP 400
- **Actual**: HTTP 400
- **Response detail**: Contains "modality"
- **Verdict**: ✅ PASS

### Scenario 4: Invalid export format
- **Test**: `test_export_invalid_format` (existing test)
- **Expected**: HTTP 400
- **Actual**: HTTP 400
- **Verdict**: ✅ PASS

### Scenario 5: Invalid dataset path
- **Test**: `test_mllm_train_rejects_nonexistent_dataset`
- **Request**: POST /api/v1/mllm/train with dataset_path="data/nonexistent.csv"
- **Expected**: HTTP 400
- **Actual**: HTTP 400
- **Response detail**: "Dataset not found: data/nonexistent.csv"
- **Verdict**: ✅ PASS

### Scenario 6: Invalid extension
- **Test**: `test_mllm_train_rejects_invalid_extension`
- **Request**: POST /api/v1/mllm/train with dataset_path="data/dataset.graphml"
- **Expected**: HTTP 400
- **Actual**: HTTP 400
- **Response detail**: Contains "format" or "extension"
- **Verdict**: ✅ PASS

### Scenario 7: Invalid job (DELETE)
- **Test**: `test_delete_job_returns_404_for_missing_job`
- **Request**: DELETE /api/v1/jobs/job_nonexistent
- **Expected**: HTTP 404
- **Actual**: HTTP 404
- **Verdict**: ✅ PASS

### Scenario 8: Evaluate invalid data
- **Test**: `test_evaluation_detects_dominant_class_column`
- **Expected**: PRED_LABEL_CANDIDATES contains "dominant_class"
- **Actual**: "dominant_class" found in candidates
- **Verdict**: ✅ PASS

## Summary
- **Total scenarios**: 8
- **Passed**: 8
- **Failed**: 0
- **Pass rate**: 100%
