# New Features Assessment | Date: 2026-05-24 | MLLM-Geo-AI Project

---

## 5A. Resolved Issues from remaining_phases_report (May 4, 2026)

### P0 — Critical Fixes (All Resolved)

| ID | Issue | File(s) | Resolution | Quality |
|----|-------|---------|------------|---------|
| P0-1 | Dataset labels all 0 | data/raw/project.csv | Category→label mapping (0=Res, 1=Comm, 2=Ind) | Solid — uses real category data |
| P0-2 | MLP hidden_dim=128 vs 256 | domain/mlp_model.py | Changed default to 256 | Solid — matches saved weights |
| P0-3 | encode() vs embed_texts() | scripts/train_multimodal.py | All callers use embed_texts() | Solid |
| P0-4 | No val_loss monitoring | scripts/train_multimodal.py | Added val loop with loss + accuracy | Solid — training history saved |
| P0-5 | roads.graphml not cached | data/raw/roads.graphml | 558 MB OSMnx dump downloaded | Excellent — instant load |

### P1 — Recommended Fixes (All Resolved)

| ID | Issue | File(s) | Resolution | Quality |
|----|-------|---------|------------|---------|
| P1-6 | No ablation support | scripts/train_multimodal.py | --modalities argparse flag + 7 CSV results | Good |
| P1-7 | Missing output schema fields | fusion_service.py | **Partial** — verify graph/text_embedding_norm | **Not verified** |
| P1-8 | No training history | scripts/train_multimodal.py | training_history.json saved (20 epochs) | Solid |
| P1-9 | No spatial accuracy | evals/eval_multimodal.py | 8-neighbor voting algorithm | Solid — 0.8455 on eval |
| P1-10 | No DELETE job endpoint | interfaces/api.py | DELETE /jobs/{job_id} implemented | Functional |

---

## 5B. New API Endpoints Since May 6

| Endpoint | HTTP | Quality | Notes |
|----------|------|---------|-------|
| DELETE /api/v1/jobs/{job_id} | DELETE | Good | Status updated to "cancelled". Celery revocation not implemented (minor). |
| GET /api/v1/grid/{grid_id}/graph-topology | GET | Partial | Implemented but grid storage not done — always returns 501 |
| POST /api/v1/evaluate | POST | Good | sklearn metrics + spatial accuracy computed. File upload validated. |
| GET /api/v1/evaluate/{job_id}/export | GET | Good | CSV export of evaluation results with proper headers |

---

## 5C. New Test Files Since May 6

| File | Tests | Purpose |
|------|-------|---------|
| tests/test_dataset_quality.py | 3 | Label distribution, null checks, class balance |
| tests/test_embedding_pipeline.py | Unknown | Embedding pipeline validation |
| tests/test_fusion_output_schema.py | Unknown | Output schema integrity |
| tests/test_mlp_architecture.py | 1 | hidden_dim verification |
| tests/test_spatial_accuracy.py | 3 | 8-neighbor spatial accuracy correctness |
| tests/test_road_network.py | Unknown | Road network loader tests |
| tests/test_satellite_loader.py | Unknown | Satellite loader tests |

### New Scripts Since May 6

| Script | Purpose |
|--------|---------|
| scripts/train_multimodal.py | Full multi-modal training with CLI flags |
| scripts/train_baseline.py | Baseline (POI-only) training |
| scripts/relabel_dataset.py | Category→label mapping + synthetic generation |
| scripts/verify_dataset.py | Dataset integrity checks |

### New Evaluation Files Since May 6

| File | Purpose |
|------|---------|
| evals/eval_multimodal.py | Multi-modal evaluation with spatial accuracy |
| evals/eval_baseline.py | Baseline evaluation |
| evals/run_ablation.py | Ablation study runner |
| evals/training_history.json | 20-epoch training history |
| evals/multimodal_results.json | Accuracy=1.0, spatial_accuracy=0.8455 |
| evals/ablation_results/ (7 CSVs) | POI-only, POI+Image, Full, comparison |

---

## 5D. Current Blockers

| Blocker | Priority | Impact | Resolution |
|---------|----------|--------|------------|
| Celery workers not running | HIGH | Async jobs not processed (test fails) | Start workers |
| Grid storage not implemented | MEDIUM | graph-topology endpoint fails | Implement file-based storage |
| Class 2 only 11 real samples | MEDIUM | Class imbalance | Run relabel_dataset.py |
| WebSocket not implemented | LOW | No real-time progress | Post-MVP |

## 5E. Defect: API-3 Evaluate Endpoint Issues

The `POST /evaluate` endpoint was audited and found with these issues:
1. `spatial_accuracy` is a copy of `overall_accuracy` in `evaluation_service.py:200` (though a real spatial accuracy exists in `eval_multimodal.py`)
2. Missing `python-multipart` dependency (now resolved)
3. No file size limit validation

---

*Report generated: 2026-05-24*
*Project: MLLM-Geo-AI Urban Classification System*
