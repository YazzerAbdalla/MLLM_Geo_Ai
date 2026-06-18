# Legacy Failures Report | Date: 2026-06-17 | MLLM-Geo-AI Project

## 1. Previously Known Failures

### 1.1 torch_geometric dependency issue

**Status**: ⚠️ PARTIAL

**Details**: 
- `torch-geometric` is listed in requirements.txt
- `app/infrastructure/gnn_model.py` imports `torch_geometric.nn.SAGEConv`
- The import works (no error at runtime)
- However, the GNN model is NOT used in the actual pipeline (UrbanMLP is used)
- `test_gnn.py` exists but was not tested in this session

### 1.2 Mock API mismatch (road_network test)

**Status**: ❌ STILL FAILING

**Details**:
- Test `test_road_network_loader` fails because the mock expects `graph_from_bbox(30.1, 29.9, 31.3, 31.1, ...)` but the actual code calls `graph_from_bbox(bbox=(30.1, 29.9, 31.3, 31.1), ...)` using keyword argument `bbox=`
- The code was updated for OSMnx v2 but the test wasn't updated

### 1.3 Missing evaluation function (spatial accuracy)

**Status**: ❌ STILL FAILING

**Details**:
- Test `test_spatial_accuracy_exists` imports `compute_spatial_accuracy` from `evals.eval_multimodal`
- The actual function is named `compute_spatial_consistency`
- Function exists but has wrong name for the test

## 2. Additional Failures Found

### 2.1 MLP weight mismatch (P0-2 regression)

**Status**: ❌ STILL BROKEN

**Details**: `models/urban_mlp.pt` has `hidden_dim=128` but the code initializes `UrbanMLP` with `hidden_dim=256`. Loading the saved weights fails.

### 2.2 Class balance issue (P0-1 not fully resolved)

**Status**: ⚠️ PARTIAL

**Details**: Class 0=971, Class 1=184, Class 2=11 — Industrial class severely under-represented.

### 2.3 Async flow test failure

**Status**: ❌ STILL FAILING

**Details**: `test_load_area_and_classify_flow` fails because the async job stays "queued" when using the TestClient (no Celery worker available in test context).

## 3. Summary

| Failure | Previous Status | Current Status | Delta |
|---------|:--------------:|:--------------:|:-----:|
| torch_geometric issue | ❌ | ⚠️ PARTIAL | Improved |
| Mock API mismatch (road_network) | ❌ | ❌ STILL FAILING | Unchanged |
| Missing eval function | ❌ | ❌ STILL FAILING | Unchanged |
| MLP weight mismatch | ✅ FIXED (claimed) | ❌ STILL BROKEN | Regression |
| Class balance | ⚠️ PARTIAL | ⚠️ PARTIAL | Unchanged |
| Async flow test | ❌ | ❌ STILL FAILING | Unchanged |

## 4. Evidence Matrix

| Item | Code Verified | Runtime Verified | Evidence Attached |
|------|:-------------:|:----------------:|:-----------------:|
| torch_geometric | YES | YES (imports) | YES |
| Mock API mismatch | YES | YES (test fails) | YES |
| Missing eval function | YES | YES (test fails) | YES |
| MLP weight mismatch | YES | YES (load fails) | YES |
| Class balance | YES | YES | YES |
| Async flow test | YES | YES (test fails) | YES |
