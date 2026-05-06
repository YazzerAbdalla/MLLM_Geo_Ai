# File Status Guide

This document classifies all files in the project by their status.

**Purpose**: Help junior developers understand what each file does  
**Last Updated**: May 2026

---

## Status Categories

| Status | Meaning |
|--------|---------|
| ACTIVE | Working, used by the application |
| PARTIAL | Works with limitations |
| PLANNED | Not implemented yet |
| ARCHIVE | Not used, kept for reference |
| RESEARCH | Historical/ research materials |

---

## Active Files (Working)

These files are actively used and work correctly:

### Core Application

| File | Description |
|------|------------|
| `app/config.py` | Configuration (model dimensions) |
| `app/main.py` | FastAPI entry point |
| `app/domain/mlp_model.py` | UrbanMLP classifier (PyTorch) |
| `app/domain/spatial_service.py` | Grid generation |

### Infrastructure (AI/Machine Learning)

| File | Description |
|------|------------|
| `app/infrastructure/ai_model.py` | Sentence-Transformer embedder |
| `app/infrastructure/image_encoder.py` | ResNet18 image encoder |
| `app/infrastructure/road_network.py` | OSMnx road network loader |

### Infrastructure (Data)

| File | Description |
|------|------------|
| `app/infrastructure/satellite_loader.py` | Satellite image loading |
| `app/infrastructure/db.py` | SQLite database |

### Application Layer

| File | Description |
|------|------------|
| `app/application/fusion_service.py` | Multi-modal classification |
| `app/application/export_service.py` | Export to CSV/GeoJSON |

### API Endpoints

| File | Description |
|------|------------|
| `app/interfaces/api.py` | All HTTP endpoints |

### Scripts

| File | Description |
|------|------------|
| `scripts/download_model.py` | Download sentence transformer |
| `scripts/process_data.py` | Process CSV data |

### Tests

| File | Description |
|------|------------|
| `tests/test_api_integration.py` | API integration tests |
| `tests/test_fusion.py` | Fusion tests |
| `tests/test_image_encoder.py` | Image encoder tests |
| `tests/test_road_network.py` | Road network tests |
| `tests/test_satellite_loader.py` | Satellite loader tests |
| `tests/test_spatial_service.py` | Spatial service tests |

### Configuration

| File | Description |
|------|------------|
| `config.json` | Test bounding box config |
| `requirements.txt` | Python dependencies |
| `AGENTS.md` | Agent instructions |

### Models

| File | Description |
|------|------------|
| `models/sentence_transformer/` | Pre-downloaded transformer |
| `models/urban_mlp.pt` | Trained MLP classifier |
| `models/random_forest.pkl` | Baseline model |

### Data

| File | Description |
|------|------------|
| `data/sat_images/` | Sample satellite images |
| `assets/project.csv` | Sample POI data |

---

## Partial Files (Limited Functionality)

These files work but have limitations:

### Celery Tasks (Require Redis + Celery)

| File | Status |
|------|--------|
| `tasks/load_area.py` | Requires Celery + Redis |
| `tasks/classify.py` | Requires Celery + Redis |
| `celery_app.py` | Requires Redis broker |

**Note**: These files exist but require Redis + Celery to be running. Without them, async endpoints return HTTP 501.

### Redis Integration

| File | Limitation |
|------|----------|
| `app/infrastructure/redis_store.py` | Gracefully handles unavailability |
| `app/infrastructure/job_store.py` | Uses Redis when available |

**Note**: Redis is optional - app works without it (with warnings).

### Docker Files

| File | Limitation |
|------|----------|
| `docker-compose.yml` | Optional, not tested for juniors |
| `Dockerfile` | Optional, not tested for juniors |
| `nginx.conf` | Optional reverse proxy |

**Note**: These are for advanced deployment only.

---

## Planned Files (Not Implemented)

These features are planned but need more work:

### Query Endpoint

| File | Status |
|------|--------|
| `POST /api/v1/query` | Returns 501 "Not implemented" |

**Note**: Natural language query feature planned for v2.

### Additional Scripts

| File | Status |
|------|--------|
| `scripts/train.py` | Works but needs training data |
| `scripts/train_baseline.py` | Works but needs training data |
| `scripts/train_multimodal.py` | Works but needs training data |

**Note**: Training scripts exist but require labeled training data.

---

## Archive Candidates

These files are not used and may be removed in the future:

| File | Reason |
|------|--------|
| `manual_golden_run.py` | Empty file (0 bytes) |
| `celery_app.py` | Orphan file (no tasks module attached) |

**Note**: These are kept for reference but marked for potential removal.

---

## Documentation Files

### Active Documentation

| File | Description |
|------|------------|
| `README.md` | Project overview |
| `docs/project_status.md` | System status (works/partial/planned) |
| `docs/quick_start_demo.md` | First run guide |
| `docs/windows_setup_guide.md` | Windows troubleshooting |

### Historical/Research

| File | Description |
|------|------------|
| `docs/Scientific_Analysis.md` | Academic methodology |
| `docs/PROGRESS_REPORT.md` | Project history |
| `docs/CODEBASE_ANALYSIS_REPORT.md` | Past analysis |
| `docs/MLLM_GeoAI_Build_Plan.md` | Original plan |
| `docs/*.pdf` (Arabic) | Research documents |

### Superseded (Can Be Archived)

| File | Reason |
|------|--------|
| `AGENT_TASKS.md` | Old agent tasks (see AGENTS.md) |
| `docs/prd-*.md` | Old PRD documents |
| `docs/api-contract-*.md` | Old API contracts |

---

## Data Files

### Sample/Testing Data

| File | Status |
|------|--------|
| `data/sat_images/cell_*.png` | Sample tiles (active) |
| `assets/project.csv` | Sample POI data (active) |
| `evals/baseline_results.json` | Past results (research) |
| `evals/multimodal_results.json` | Past results (research) |

### Generated Data

| File | Status |
|------|--------|
| `data/results/` | Output directory (generated at runtime) |
| `data/raw/` | Raw data directory |
| `mllm_geo_ai.db` | SQLite database file |

---

## Files NOT to Modify

These files should NOT be modified by junior developers:

| File | Why |
|------|-----|
| `app/domain/mlp_model.py` | Working ML model |
| `app/infrastructure/ai_model.py` | Working embedder |
| `app/infrastructure/image_encoder.py` | Working encoder |
| `app/infrastructure/road_network.py` | Working loader |
| `tests/test_fusion.py` | Passing tests |
| `tests/test_image_encoder.py` | Passing tests |

---

## How to Use This Guide

### For Learning the Code
1. Start with `app/config.py` (simple, just settings)
2. Then `app/main.py` (entry point)
3. Then `app/domain/mlp_model.py` (ML model)
4. Then `app/infrastructure/` (encoders/loaders)

### For Running the App
1. Read `docs/quick_start_demo.md` first
2. Check `docs/project_status.md` for what's working
3. Look at `README.md` for overview

### For Understanding Features
1. This file shows what's working
2. `docs/project_status.md` explains limitations

---

## Summary

| Status | Count |
|--------|-------|
| ACTIVE | Many files |
| PARTIAL | Few files |
| PLANNED | 1 feature |
| ARCHIVE | 2 files |
| RESEARCH | Several files |

---

## Questions?

- If a file is not working: Check docs/project_status.md
- If you need help: See docs/quick_start_demo.md
- If you're confused: This file helps orient you

**Start simple**: Don't try to understand everything at once!