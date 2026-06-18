# Defense Demo Simulation Report | Date: 2026-06-17 | MLLM-Geo-AI Project

## 1. Demo Workflow Simulation

### Step 1: Select Area
- Bounding box: [31.20, 30.00, 31.21, 30.01]
- Grid size: 1000m

### Step 2: Load Area
- POST /api/v1/load-area → 202 Accepted ✅
- Job completed in ~3 seconds ✅

### Step 3: View Grid
- GET /api/v1/grid/{grid_id}/preview → GeoJSON returned ✅
- GET /api/v1/grid/{grid_id}/details → Cell info returned ✅

### Step 4: Run Classification
- POST /api/v1/classify → 202 Accepted ✅
- But job did not complete within 30s ⚠️

### Step 5: Export Results
- Could not test (no completed classification) ❌

### Step 6: Run Evaluation
- Could not test (no completed classification) ❌

## 2. Results

| Metric | Value |
|--------|-------|
| Total execution time | Partial (E2E incomplete) |
| Failures | 1 (classify timeout) |
| Manual interventions needed | 0 (so far) |
| User-facing issues | Graph-topology timeout >2min |

## 3. Pre-Demo Must-Fix Items

1. **Fix MLP weight mismatch** (P0-2 re-opened): hidden_dim=128 vs 256
2. **Fix classify task** — ensure Celery worker processes classify tasks promptly
3. **Fix graph-topology endpoint** — currently times out
4. **Fix class balance** — Class 2 has only 11 samples

## 4. Demo Flow Readiness

| Step | Status | Notes |
|------|--------|-------|
| 1. Select Area | ✅ READY | Bbox input works |
| 2. Load Area | ✅ READY | Async job completes |
| 3. View Grid | ✅ READY | Preview + details |
| 4. Classify | ⚠️ PARTIAL | Accepts request but completion unverified |
| 5. Export | ⚠️ PARTIAL | Code exists, not runtime-tested |
| 6. Evaluate | ⚠️ PARTIAL | Code exists, not runtime-tested |
| 7. Metrics | ✅ READY | Training history + eval results available |

## 5. Evidence Matrix

| Item | Code Verified | Runtime Verified | Evidence Attached |
|------|:-------------:|:----------------:|:-----------------:|
| Load Area | YES | YES | YES |
| View Grid | YES | YES | YES |
| Classify | YES | PARTIAL | YES |
| Export | YES | NO | NO |
| Evaluate | YES | NO | NO |
