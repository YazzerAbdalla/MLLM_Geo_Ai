# MLLM-Geo-AI Agent Instructions

## App background 
  This app is a grade project for MultiModal Learning for Geographical Applications
  at ELCT-TUIT for stedunts in CSC last year. the app is a web app that can be used to 
  classify geographical data into different categories. by using multi-modal learning techniques, so use b1 and b2 english words and simple sentences , also explain 
  the code in simple way.
  

## Running the App
```bash
python -m app.main
```
Server starts at `http://localhost:8000`. Do NOT use `uvicorn app.main`.

## Running Tests
```bash
pytest tests/
```
- Tests use FastAPI TestClient (no server startup needed)
- Use `"modalities": []` in API calls to skip real satellite/road downloads for fast testing

## Key Commands
- **Download model**: `python scripts/download_model.py`
- **Process data**: `python scripts/process_data.py`

## Architecture
- **DDD structure**: `app/application/`, `app/domain/`, `app/infrastructure/`, `app/interfaces/`
- **Entry point**: `app/main.py`
- **API routes**: `app/interfaces/api.py`
- **Config**: `app/config.py` (POI_DIM=384, IMG_DIM=256, GRAPH_DIM=3, FUSION_DIM=643)

## Test Data
- **Bounding box**: `[31.20, 30.00, 31.22, 30.02]` from `config.json`
- **Grid size**: 500m

## Model
- **Name**: `paraphrase-multilingual-MiniLM-L12-v2`
- **Location**: `models/sentence_transformer/`

## Environment
- **GEE project**: `EARTH_ENGINE_PROJECT=grade-project-493621` in `.env`
- Requires GEE auth for satellite features; app warns but continues without it

## API Endpoints
- `POST /api/v1/load-area` - Create grid from bbox
- `GET /api/v1/area-status/{job_id}` - Poll job status
- `POST /api/v1/classify` - Run classification
- `GET /api/v1/classify-status/{job_id}` - Poll classification status
- `GET /api/v1/classification-result/{job_id}` - Get results
- `GET /health` - Health check

## Agent Workflow Rules

**RULE 1 — READ BEFORE WRITE**
Before editing any file, always read its current content in full.
Never assume what a file contains based on its name alone.

**RULE 2 — ONE TASK AT A TIME**
Complete each numbered task fully before starting the next.
A task is complete only when:
  (a) all files are written/edited
  (b) the targeted pytest or manual check passes
  (c) you print a TASK COMPLETE marker with the check ID

**RULE 3 — NEVER BREAK PASSING TESTS**
Before editing any file, run `pytest tests/ -q` and record the current pass count.
After your edit, re-run and confirm the count did not drop.
If a test breaks that was previously passing, fix it before continuing.

**RULE 4 — PRESERVE EXISTING WORKING CODE**
The ML pipeline (encoders, MLP, inference) already passes checks 1.1–1.3.
Do not refactor, rename, or move any of the following unless a task explicitly requires it:
  - app/infrastructure/ai_model.py
  - app/infrastructure/image_encoder.py
  - app/infrastructure/road_network.py
  - app/domain/mlp_model.py
  - tests/test_fusion.py
  - tests/test_image_encoder.py

**RULE 5 — VERIFY EACH CHECK EXPLICITLY**
After completing each task, run the exact verification command listed in the task's VERIFY section.
Do not mark a task complete without it.

**RULE 6 — DEPENDENCY ORDER IS MANDATORY**
Sprint 1 → Sprint 2 → Sprint 3 → Sprint 4.
Within each sprint, tasks must be done in numbered order.
Do not skip ahead even if a later task looks independent.

**RULE 7 — REPORT FORMAT**
After each task print this exact block:
  ┌─────────────────────────────────────────┐
  │ TASK X.Y COMPLETE                       │
  │ Check: 3.X → PASS                       │
  │ Files changed: file1.py, file2.py       │
  │ Tests: N passed, 0 failed               │
  └─────────────────────────────────────────┘
If a task fails, print:
  ✗ TASK X.Y FAILED
  Reason: <exact error>
  Next action: <what you will try>
Then attempt the fix. Never move to the next task while in a failed state.