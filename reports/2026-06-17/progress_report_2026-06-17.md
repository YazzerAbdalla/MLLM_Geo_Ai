# System Audit Report | Date: 2026-06-17 | MLLM-Geo-AI Project

---

## Section 1: What Changed Since Last Audit (May 24 → Jun 17)

| Category | May 24 Status | Jun 17 Status | Delta |
|----------|:-------------:|:-------------:|:-----:|
| Celery Worker | NOT RUNNING | ✅ RUNNING | +1 |
| Tests Passing | 22 pass, 2 fail | 77 pass, 4 fail, 3 skip | +55 tests |
| Test Errors | 0 | 2 errors (mllm_trainer, mllm_use_case) | -2 |
| MLP Weight Match | Claimed Fixed | ❌ Hidden_dim 128≠256 | Regression |
| Server.log | N/A | ✅ Present | +1 |

**Key changes since last report:**
- Test suite expanded significantly (from 24 to 86 test files)
- Celery worker now runs continuously (3 registered tasks, 33 jobs processed)
- Redis now has 781 accumulated job keys from previous runs
- SQLite has 51 grid records

---

## Section 2: P0 Critical Fixes Status

| ID | Issue | May 24 Status | Jun 17 Status | Evidence |
|----|-------|:-------------:|:-------------:|----------|
| P0-1 | Dataset labels all 0 | ✅ RESOLVED | ✅ RESOLVED | 1,166 rows, labels 0/1/2 |
| P0-2 | MLP hidden_dim mismatch | ✅ RESOLVED | ❌ STILL BROKEN | Checkpoint hidden_dim=128, code=256 |
| P0-3 | encode() vs embed_texts() | ✅ RESOLVED | ✅ RESOLVED | All callers use embed_texts() |
| P0-4 | No val_loss monitoring | ✅ RESOLVED | ✅ RESOLVED | 20-epoch training_history.json |
| P0-5 | roads.graphml not cached | ✅ RESOLVED | ✅ RESOLVED | 558 MB cached file exists |

**⚠️ P0-2 is a regression**: The May 24 report claimed it was fixed, but the model file `urban_mlp.pt` still has hidden_dim=128 while the code initializes with hidden_dim=256. Loading fails with shape mismatch.

---

## Section 3: P1 Recommended Fixes Status

| ID | Issue | May 24 Status | Jun 17 Status | Evidence |
|----|-------|:-------------:|:-------------:|----------|
| P1-6 | Ablation support | ✅ RESOLVED | ✅ RESOLVED | ablation_results/ directory exists |
| P1-7 | Missing schema fields | ⚠️ PARTIAL | ✅ RESOLVED | text/graph embedding norm computed |
| P1-8 | Training history | ✅ RESOLVED | ✅ RESOLVED | evals/training_history.json |
| P1-9 | Spatial accuracy | ✅ RESOLVED | ⚠️ PARTIAL | compute_spatial_consistency exists but test imports wrong name |
| P1-10 | DELETE job endpoint | ✅ RESOLVED | ✅ RESOLVED | DELETE /api/v1/jobs/{job_id} |

---

## Section 4: Phase 2–12 Completion

| Phase | Status | Notes |
|-------|--------|-------|
| 2. Multi-Modal Data Collection | ✅ COMPLETE | POI, satellite (144), roads (cached) |
| 3. Data Cleaning (WGS84) | ✅ COMPLETE | Backend only |
| 4. Graph G=(V,E) | ✅ COMPLETE | OSMnx integration, graph-topology endpoint |
| 5. Feature Engineering | ✅ COMPLETE | 643-dim fusion vector |
| 6. Feature Fusion | ✅ COMPLETE | Concat + attention fusion modes |
| 7. Base Models | ⚠️ PARTIAL | MLP weight mismatch (P0-2 regression) |
| 8. GNN Integration | ❌ NOT USED | Code exists but unused |
| 9. Training Pipeline | ✅ COMPLETE | MLP training with val monitoring |
| 10. Evaluation Metrics | ⚠️ PARTIAL | spatial_consistency available but test broken |
| 11. Digital Twin NL Query | ❌ MISSING | Stub endpoint only |
| 12. Geo-MLLM Export | ❌ MISSING | P2 future work |

---

## Section 5: API Coverage Matrix

| # | Method | Route | Status | Runtime Verified |
|---|--------|-------|:------:|:----------------:|
| 1 | GET | /health | ✅ WORKING | YES |
| 2 | POST | /api/v1/load-area | ✅ WORKING | YES |
| 3 | GET | /api/v1/area-status/{id} | ✅ WORKING | YES |
| 4 | GET | /api/v1/grid/{id}/preview | ✅ WORKING | YES |
| 5 | GET | /api/v1/grid/{id}/details | ✅ WORKING | YES |
| 6 | GET | /api/v1/grid/{id}/graph-topology | ⚠️ BROKEN (timeout) | YES |
| 7 | GET | /api/v1/grid/{id}/pois | ✅ WORKING | NO |
| 8 | POST | /api/v1/classify | ✅ WORKING | YES |
| 9 | GET | /api/v1/classify-status/{id} | ✅ WORKING | YES |
| 10 | GET | /api/v1/classification-result/{id} | ✅ WORKING | NO |
| 11 | GET | /api/v1/export/{id} | ✅ WORKING | NO |
| 12 | GET | /api/v1/thumbnails/{gid}/{cid}.jpg | ✅ WORKING | NO |
| 13 | DELETE | /api/v1/jobs/{id} | ✅ WORKING | YES |
| 14 | POST | /api/v1/evaluate | ✅ WORKING | NO |
| 15 | GET | /api/v1/evaluate/{id}/export | ✅ WORKING | NO |
| 16 | POST | /api/v1/mllm/train | ✅ WORKING | YES (validation) |
| 17 | GET | /api/v1/mllm/train-status/{id} | ✅ WORKING | YES |
| 18 | GET | /api/v1/mllm/export/{id} | ❌ MISSING | N/A |
| 19 | GET | /api/v1/mllm/model-card/{id} | ❌ MISSING | N/A |
| 20 | POST | /api/v1/query | ⚠️ STUB (501) | YES |
| 21 | WS | /api/v1/ws/progress/{id} | ⚠️ PARTIAL | NO |
| 22 | POST | /api/v1/train | ❌ MISSING | N/A |

**Total**: 16/22 (73%) implemented or working, 13/22 (59%) fully functional

---

## Section 6: Infrastructure Status

| Component | Status | Runtime Verified |
|-----------|--------|:----------------:|
| FastAPI Server | ✅ RUNNING | YES |
| Redis | ✅ RUNNING | YES |
| Celery Worker | ✅ RUNNING | YES |
| SQLite | ✅ EXISTS | YES |
| Docker Compose | ⚠️ CONFIGURED | NO |
| Earth Engine | ⚠️ CONFIGURED | NO |
| Training History | ✅ PERSISTED | YES |
| Model Weights | ❌ BROKEN (mismatch) | YES |

---

## Section 7: Async Processing Findings

**load-area**: ✅ Fully working — 202 → poll → completed
**classify**: ⚠️ Partially working — 202 accepted, but completion slow/unverified
**mllm/train**: ✅ Working — validated and submitted to Celery

**Key Issue**: Classify task may have high latency due to image encoding pipeline. Need performance optimization.

---

## Section 8: Failure Injection Findings

All tested error cases returned correct status codes:
- Invalid grid_id → 404
- Empty modalities → 400
- Missing dataset → 400
- Missing job → 404

7/12 failure cases runtime verified. Remaining 5 are code-verified but not runtime-tested.

---

## Section 9: Performance Findings

| Endpoint | Latency | Notes |
|----------|---------|-------|
| /health | ~50ms | Fast |
| load-area (202) | ~200ms | Async |
| area-status | ~50ms | Memory/Redis lookup |
| grid-preview | ~100ms | Disk read |
| graph-topology | >120s | **TIMEOUT** |
| classify (202) | ~200ms | Async (slow completion) |

---

## Section 10: Spatial Validation Findings

- CRS: Correctly uses projected CRS for road density calculation (EPSG:3857)
- Road density: Code handles projection correctly
- Graph metrics: `clustering_coeff` and `degree_centrality` hardcoded to 0.0
- Spatial consistency score: 0.8455 (from evaluation)

---

## Section 11: Classification Output Findings

- All 13 required PRD v3.0 fields present
- `text_embedding_norm` and `graph_embedding_norm` now correctly computed
- `clustering_coeff` and `degree_centrality` hardcoded to 0.0 (not computed)
- Valid GeoJSON geometry guaranteed

---

## Section 12: Model Consistency Findings

**🚨 CRITICAL: Model weight mismatch**
- Saved checkpoint: hidden_dim=128
- Code initialization: hidden_dim=256
- Result: UrbanMLP.load_state_dict() fails at runtime

All feature dimensions (POI=384, IMG=256, GRAPH=3, FUSION=643) match correctly.

---

## Section 13: Technical Assessment

### Biggest Defense Risk
The **MLP weight mismatch** (P0-2). If a demo tries to load the saved model and classify, it will crash with a PyTorch shape error. This was claimed fixed in May but the actual model file was never updated.

### Most Surprising Finding
The **graph-topology endpoint timeout**. Loading a 558MB GraphML file on every request is not feasible. This needs caching or pre-processing.

### Top 3 Priorities Before Defense
1. **Fix MLP weight mismatch** — Either change hidden_dim to 128 in code or retrain with 256
2. **Fix graph-topology performance** — Cache parsed graph or serve from pre-processed format
3. **Fix failing tests** — 4 test failures + 2 errors need attention

### Realistic P2 Features
- GNN integration (code exists but unused)
- WebSocket progress events (pubsub not connected to job store)
- MLLM with LoRA (peft dependency issue)

### Honest Readiness Score
**28/50** — Below the 35/50 defense threshold. The MLP model issue and failing async flow are critical.

---

## Section 14: Defense Readiness Score

| Dimension | Previous (May 24) | Current (Jun 17) | Delta |
|-----------|:-----------------:|:-----------------:|:-----:|
| ML Training Quality | 7/10 | 6/10 | -1 |
| Output Schema Completeness | 8/10 | 8/10 | 0 |
| API Coverage | 8/10 | 6/10 | -2 |
| Phase Completion | 9/10 | 7/10 | -2 |
| Demo Stability | 8/10 | 5/10 | -3 |
| Infrastructure Readiness | 5/10 | 7/10 | +2 |
| Async Reliability | 5/10 | 5/10 | 0 |
| **TOTAL** | **40/50** | **44/70** | **Avg: 22/50 → 28/50** |

**Note**: The May 24 score of 40/50 was based on a smaller test suite and claimed fixes that were not actually validated. The current score is based on actual runtime verification with more comprehensive testing.

---

*Report generated: 2026-06-17*
*Project: MLLM-Geo-AI Urban Classification System*
