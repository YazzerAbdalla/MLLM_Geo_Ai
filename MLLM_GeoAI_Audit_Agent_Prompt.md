# MLLM-Geo-AI Project — Full Implementation Audit Prompt
> Ready-to-send to an AI coding agent (Claude Code / Cursor / similar).
> All context is embedded — the agent does NOT need to read any external files.

---

## MISSION

You are a senior AI/ML engineer performing a complete implementation audit of the **MLLM-Geo-AI Urban Classification System** — a graduation project that classifies Cairo's urban areas (Residential / Commercial / Industrial) using multi-modal AI (POI embeddings + satellite imagery + road graph features).

Work through **5 phases in strict order**. Do not skip ahead.

---

## EMBEDDED CONTEXT — READ THIS BEFORE TOUCHING ANY CODE

### A. Project Background

The system analyzes 500 m × 500 m grid cells over Cairo, Egypt. For each cell it extracts:
- **POI embeddings** (384-dim) via `paraphrase-multilingual-MiniLM-L12-v2`
- **Image embeddings** (256-dim) via ResNet-18
- **Graph features** (3-dim: node_count, total_length, avg_degree) via OSMnx
- **Fused vector** (643-dim) → fed into `UrbanMLP` → 3-class softmax (Residential / Commercial / Industrial)

The FastAPI backend exposes async endpoints. A React/MapLibre frontend already exists (23/23 tasks complete per the onboarding doc). The backend is at ~45% API coverage (9 of 20 endpoints).

---

### B. AI Task Objectives (Source: Onboarding Document — Arabic Team Distribution, May 2026)

These are the exact deliverables expected from the AI student team. Use these as the **ground truth** for your audit.

#### Student 3 — Data / Dataset

| Task ID | File | What Must Be Done | Priority |
|---------|------|-------------------|----------|
| AI-1 | `data/raw/project.csv` | Re-label the CSV by mapping `category` column → numeric label: Education/Health→0, Mall/Shop/Bank→1, Industrial/Factory→2. Verify 3 classes exist in `df['label'].value_counts()`. If Commercial/Industrial POIs are missing, generate ~100 synthetic rows per class. | P0 Critical |
| AI-2 | `app/infrastructure/data_loader.py` | Verify the data loader reads the new `label` column and passes it correctly through the pipeline. | P1 Important |
| AI-3 | `scripts/verify_dataset.py` (NEW) | Write a verification script that prints: row count, class distribution, null counts. Must run before any training. | P1 Important |

#### Student 4 — Training Pipeline

| Task ID | File | What Must Be Done | Priority |
|---------|------|-------------------|----------|
| AI-4 | `scripts/train_multimodal.py` line 27 | Change `poi_enc.encode()` → `poi_enc.embed_texts()`. Search all calls: `grep -rn 'poi_enc.encode\|poi_encoder.encode' app/ scripts/` | P0 Critical |
| AI-5 | `app/domain/mlp_model.py` line 12 | Change `hidden_dim=256` → `hidden_dim=128` to match saved weights. Delete `models/urban_mlp.pt` and retrain after AI-1. | P0 Critical |
| AI-6 | `scripts/train_multimodal.py` | Add validation loop after each epoch (val_loss + val_accuracy). Save training history to `evals/training_history.json` for the defense presentation. | P0 Critical |
| AI-7 | `data/raw/roads.graphml` (NEW) | Pre-download the Cairo road network and save locally to prevent WiFi collapse during demo: `python -c "import osmnx as ox; G=ox.graph_from_bbox(30.10,29.90,31.30,31.10); ox.save_graphml(G,'data/raw/roads.graphml')"` | P0 Critical |
| AI-8 | `scripts/train_multimodal.py` | Add `--modalities` argparse flag to support ablation studies. Example: `python train.py --modalities poi` or `--modalities poi,image,graph`. Build conditional feature vector. | P1 Important |

#### Student 5 — Evaluation

| Task ID | File | What Must Be Done | Priority |
|---------|------|-------------------|----------|
| AI-9 | `app/application/fusion_service.py` (~line 133) | Add two missing fields to each cell classification result: `graph_embedding_norm: float(np.linalg.norm(graph_feat))` and `text_embedding_norm: float(np.linalg.norm(poi_emb))`. Required by PRD v3.0 FR-29. | P1 Important |
| AI-10 | `evals/eval_multimodal.py` | Implement 8-neighbor Spatial Accuracy algorithm: for each cell, compute the most frequent class among its 8 grid neighbors; compare to the cell's prediction. Output: percentage. Required by PRD v3.0 FR-29. | P1 Important |
| AI-11 | `evals/ablation_results/` (NEW dir) | Run 3 ablation experiments after AI-8 is done: (1) POI only, (2) POI+Image, (3) All modalities. Save each result as a separate CSV. Produce a comparison table for the defense. | P1 Important |

---

### C. Current System Status (Source: Master Summary Report 2026-05-06)

**Overall Health Score: 7/10**

| Component | Status |
|-----------|--------|
| App Boot | ✅ Works |
| Grid Generation (500m, EPSG:32636) | ✅ Works |
| POI Embedding (MiniLM, 384-dim) | ✅ Works |
| Image Encoder (ResNet-18, 256-dim) | ✅ Works |
| Multi-modal Fusion (643-dim concat) | ✅ Works |
| MLP Classifier (UrbanMLP) | ✅ Exists |
| Redis | ❌ Not running |
| Celery Workers | ❌ Not running |
| Grid Storage (SQLite) | ⚠️ Configured, not implemented |
| WebSocket | ❌ Missing |
| MLLM Builder Endpoints | ❌ All 4 missing |

**API Coverage: 9 / 20 endpoints implemented (45%)**

Critical missing (for the defense): `DELETE /jobs/{job_id}`, `GET /grid/{id}/graph-topology`, `POST /evaluate`, `GET /evaluate/{id}/export`.

**CRITICAL AI BLOCKER: All 973 data rows have `label = 0` (single class). The model cannot learn anything. Training is blocked until AI-1 is completed.**

---

### D. Known AI-Specific Bugs (Source: AI Training & Accuracy Report 2026-05-06)

1. **Single-class dataset**: All 973 POIs labeled 0. Only 2 POI categories (Health, Education). No Commercial or Industrial POIs.
2. **API mismatch bug**: `scripts/train_multimodal.py` line 27 calls `poi_enc.encode()` but the embedder exposes `embed_texts()`. This causes a crash at training start.
3. **Hidden dim mismatch**: `mlp_model.py` has `hidden_dim=256` but saved weights `models/urban_mlp.pt` were trained with `hidden_dim=128`. Loading the saved weights causes a shape error.
4. **No validation monitoring**: Training script has no val loop, no training history saved. Cannot show learning curves at defense.
5. **No satellite images downloaded yet**: `data/sat_images/` is empty or missing.
6. **No road graph file**: `data/raw/roads.graphml` does not exist locally.
7. **Missing output fields**: `graph_embedding_norm` and `text_embedding_norm` are required by PRD v3.0 FR-29 but not returned by `fusion_service.py`.
8. **No Spatial Accuracy implementation**: `evals/eval_multimodal.py` does not implement the 8-neighbor algorithm.
9. **No ablation study infrastructure**: No `--modalities` flag, no `evals/ablation_results/` directory.
10. **No verification script**: `scripts/verify_dataset.py` does not exist.

---

### E. Step 2 Document Phases (Source: Student Project Document — Arabic)

The project follows a 12-phase academic pipeline. The following phases are directly relevant to this AI audit:

- **Phase 2**: Multi-modal data collection — POI (OSMnx), road network (OSMnx → GraphML), satellite imagery (Sentinel-2 / GEE)
- **Phase 3**: Data cleaning — unified WGS84 coordinates, remove nulls, standardize categories
- **Phase 4**: Graph construction G=(V, E) — road nodes → intersection points, edges → road segments
- **Phase 6**: Feature fusion — X = [POI_emb(384) + Image_emb(256) + Graph_feat(3) + Text_emb(384)] with Concatenation / Weighted / Attention methods
- **Phase 7**: Base models — GNN (PyTorch Geometric) for spatial intelligence + CNN (ResNet) + Text Encoder (MiniLM/BERT)
- **Phase 9**: Training — Classification loss + Contrastive loss, val monitoring, saving training history
- **Phase 10**: Evaluation — Accuracy, F1-score per class, Spatial Accuracy (8-neighbor contiguity)
- **Phase 11**: Digital Twin — NL query in Arabic/English returning matching cell IDs + spatial explanation

**Current Phase Completion**: 4 of 12 phases complete. 8 phases are partially done or not started.

---

### F. Scoring Context (Source: Onboarding Document — May 2026)

The defense requires 35/50 points minimum. Current score is 22/50.

| Dimension | Current | Target | Main Problem |
|-----------|---------|--------|--------------|
| Model training quality | 3/10 | 8/10 | All labels = 0, single class |
| Output schema completeness | 7/10 | 9/10 | 2 fields missing from PRD v3.0 |
| API coverage | 6/10 | 7/10 | 7 endpoints missing |
| Step 2 phase completion | 5/10 | 8/10 | 8 of 12 phases incomplete |
| Demo stability | 1/10 | 8/10 | Dim conflict + encoder crash |

P0 tasks alone push score to ~33 (below threshold). P0 + P1 tasks push to ~40 (above threshold).

---

## PHASE 1 — CAPTURE OBJECTIVES & EXPECTED DELIVERABLES

Before touching any code, produce a structured summary of all expected AI deliverables. For each task (AI-1 through AI-11), document:

- **Objective**: What is this task supposed to achieve?
- **Expected output file/artifact**: What file, script, or metric must exist when done?
- **Success criterion**: How do we know it's complete?
- **Dependency**: What other task must be done first?

Format this as a table. This table becomes the audit checklist for Phase 2.

---

## PHASE 2 — INSPECT CURRENT CODEBASE

Scan the repository and for each deliverable from Phase 1, determine:

- **EXISTS**: The file/feature exists
- **COMPLETE**: Fully satisfies the objective
- **PARTIAL**: Exists but incomplete (describe what's missing)
- **MISSING**: File or feature does not exist
- **BROKEN**: Exists but has a bug that prevents it from working
- **MOCKED/STUBBED**: Has placeholder logic (hardcoded values, `pass`, `raise NotImplementedError`, returns 501)

Pay special attention to:

1. **`data/raw/project.csv`** — Does `label` column have 3 distinct classes? Or all zeros?
2. **`scripts/train_multimodal.py`** — Does it call `poi_enc.encode()` (broken) or `embed_texts()` (correct)? Does it have a val loop? Does it save `evals/training_history.json`?
3. **`app/domain/mlp_model.py`** — What is `hidden_dim`? Is it 128 or 256?
4. **`models/urban_mlp.pt`** — Does it exist? What input_dim does it expect?
5. **`data/raw/roads.graphml`** — Does it exist locally?
6. **`scripts/verify_dataset.py`** — Does it exist?
7. **`app/application/fusion_service.py`** — Does the classification result include `graph_embedding_norm` and `text_embedding_norm`?
8. **`evals/eval_multimodal.py`** — Does it implement 8-neighbor Spatial Accuracy?
9. **`evals/ablation_results/`** — Does this directory exist with CSV results?
10. **`scripts/train_multimodal.py`** — Does it have `--modalities` argparse flag?

For the API layer, verify which of these endpoints exist with real logic (not stubs):
- `DELETE /api/v1/jobs/{job_id}`
- `GET /api/v1/grid/{grid_id}/graph-topology`
- `POST /api/v1/evaluate`
- `GET /api/v1/evaluate/{job_id}/export`

---

## PHASE 3 — VALIDATE & TEST THE AI TRAINING PIPELINE

### Step 3A — Dataset Validation

Run (or write and run) a dataset check:

```python
import pandas as pd
df = pd.read_csv('data/raw/project.csv')
print("Rows:", len(df))
print("Columns:", df.columns.tolist())
print("Label distribution:\n", df['label'].value_counts())
print("Nulls:\n", df.isnull().sum())
print("Categories:\n", df['category'].value_counts() if 'category' in df.columns else "No category column")
```

Confirm: Does the dataset have 3 classes? If not, this is a P0 blocker — document it clearly.

### Step 3B — Encoder API Verification

Test the POI embedder:

```python
from app.infrastructure.ai_model import Embedder
enc = Embedder()
# Test which method name is correct
print(dir(enc))  # Look for encode vs embed_texts
test = enc.embed_texts(["test hospital"])  # or enc.encode(...)
print("Embedding shape:", test.shape)  # Expect (1, 384)
```

If `encode()` is called in training scripts but the method is actually `embed_texts()`, document as BROKEN (Bug #2).

### Step 3C — MLP Architecture Verification

```python
import torch
from app.domain.mlp_model import UrbanMLP
model = UrbanMLP(input_dim=643)
print(model)  # Check hidden_dim
# Try loading saved weights
try:
    state = torch.load('models/urban_mlp.pt', map_location='cpu')
    model.load_state_dict(state)
    print("Weights loaded OK")
except Exception as e:
    print("Weight load FAILED:", e)  # Document as Bug #3 if fails
```

### Step 3D — End-to-End Training Attempt

Attempt to run the training script. Capture the exact error if it crashes:

```bash
python scripts/train_multimodal.py 2>&1 | head -50
```

Document: Does it crash? At which line? What is the error?

### Step 3E — Inference Smoke Test

Test the classification pipeline end-to-end with a small synthetic input:

```python
import numpy as np
import torch
from app.domain.mlp_model import UrbanMLP

model = UrbanMLP(input_dim=643)
model.eval()
x = torch.randn(1, 643)
with torch.no_grad():
    out = model(x)
print("Output shape:", out.shape)  # Expect (1, 3)
print("Probabilities:", out)       # Should sum to ~1.0
```

### Step 3F — Fusion Service Output Validation

Check whether the classification result includes the two required fields:

```python
# After running a classification job, inspect the output GeoJSON
# Look for these fields in each feature's properties:
# - graph_embedding_norm (float)
# - text_embedding_norm (float)
# Document: PRESENT or MISSING
```

---

## PHASE 4 — CREATE MISSING TESTS

If the following test files do not exist, **create them** and **run them**:

### Test 1: `tests/test_dataset_quality.py`

```python
"""Tests that dataset has 3 classes and no critical nulls."""
import pytest
import pandas as pd

def test_label_distribution():
    df = pd.read_csv('data/raw/project.csv')
    assert 'label' in df.columns, "label column missing"
    classes = df['label'].nunique()
    assert classes == 3, f"Expected 3 classes, got {classes}. All labels may be 0."

def test_no_null_labels():
    df = pd.read_csv('data/raw/project.csv')
    null_labels = df['label'].isnull().sum()
    assert null_labels == 0, f"{null_labels} null labels found"

def test_class_balance():
    df = pd.read_csv('data/raw/project.csv')
    counts = df['label'].value_counts()
    min_class = counts.min()
    assert min_class >= 50, f"Smallest class has only {min_class} samples. Need at least 50 per class."
```

### Test 2: `tests/test_mlp_architecture.py`

```python
"""Tests MLP model shape compatibility."""
import pytest
import torch
from app.domain.mlp_model import UrbanMLP

def test_output_shape():
    model = UrbanMLP(input_dim=643)
    x = torch.randn(4, 643)
    out = model(x)
    assert out.shape == (4, 3), f"Expected (4,3), got {out.shape}"

def test_probabilities_sum_to_one():
    model = UrbanMLP(input_dim=643)
    x = torch.randn(4, 643)
    out = model(x)
    sums = out.sum(dim=1)
    assert torch.allclose(sums, torch.ones(4), atol=1e-5), "Softmax outputs don't sum to 1"

def test_weights_load():
    import os
    if not os.path.exists('models/urban_mlp.pt'):
        pytest.skip("No saved weights to test")
    model = UrbanMLP(input_dim=643)
    try:
        state = torch.load('models/urban_mlp.pt', map_location='cpu')
        model.load_state_dict(state)
    except Exception as e:
        pytest.fail(f"Weight loading failed: {e}")
```

### Test 3: `tests/test_embedding_pipeline.py`

```python
"""Tests the POI embedding pipeline."""
import pytest
import numpy as np
from app.infrastructure.ai_model import Embedder

def test_embedder_method_exists():
    enc = Embedder()
    assert hasattr(enc, 'embed_texts'), "embed_texts() method missing from Embedder"

def test_embedding_shape():
    enc = Embedder()
    result = enc.embed_texts(["hospital cairo", "school downtown"])
    assert result.shape == (2, 384), f"Expected (2, 384), got {result.shape}"

def test_embedding_not_zero():
    enc = Embedder()
    result = enc.embed_texts(["test"])
    assert result.sum() != 0, "Embedding is all zeros"
```

### Test 4: `tests/test_fusion_output_schema.py`

```python
"""Tests that classification output includes required PRD v3.0 fields."""
import pytest

REQUIRED_CELL_FIELDS = [
    'cell_id', 'dominant_class', 'confidences',
    'poi_top_categories', 'road_density_km_per_km2',
    'node_count', 'graph_embedding_norm', 'text_embedding_norm'
]

def test_required_fields_documented():
    """Placeholder — replace with actual API call result check."""
    # This test documents the required schema from PRD v3.0 FR-29
    missing = []
    # TODO: Run a classification and check the actual GeoJSON output
    # For now, just assert the requirements are known
    assert len(REQUIRED_CELL_FIELDS) == 8, "Schema field list incomplete"
```

### Test 5: `tests/test_spatial_accuracy.py`

```python
"""Tests the 8-neighbor Spatial Accuracy implementation."""
import pytest
import numpy as np

def test_spatial_accuracy_exists():
    try:
        from evals.eval_multimodal import compute_spatial_accuracy
    except ImportError:
        pytest.fail("compute_spatial_accuracy not found in evals/eval_multimodal.py")

def test_spatial_accuracy_perfect_grid():
    from evals.eval_multimodal import compute_spatial_accuracy
    # 3x3 grid, all Residential
    predictions = np.zeros((3, 3), dtype=int)  # All class 0
    score = compute_spatial_accuracy(predictions)
    assert score == 1.0, f"Perfect grid should score 1.0, got {score}"

def test_spatial_accuracy_range():
    from evals.eval_multimodal import compute_spatial_accuracy
    import numpy as np
    predictions = np.random.randint(0, 3, size=(5, 5))
    score = compute_spatial_accuracy(predictions)
    assert 0.0 <= score <= 1.0, f"Score {score} out of [0,1] range"
```

**Run all tests:**

```bash
pytest tests/ -v --tb=short 2>&1
```

Document: number passed, failed, errors, skipped.

---

## PHASE 5 — GENERATE COMPREHENSIVE AUDIT REPORT

Produce a structured report with the following sections. Write in English. Be specific — cite file names and line numbers.

---

### SECTION 1: Planned Objectives

List all 11 AI tasks (AI-1 to AI-11) with their objectives and expected deliverables, exactly as described in the onboarding document.

---

### SECTION 2: Expected Deliverables Checklist

| Task ID | Expected Artifact | Status | Evidence |
|---------|------------------|--------|----------|
| AI-1 | `data/raw/project.csv` with 3-class labels | ? | |
| AI-2 | `data_loader.py` reads `label` correctly | ? | |
| AI-3 | `scripts/verify_dataset.py` exists and runs | ? | |
| AI-4 | Training script uses `embed_texts()` not `encode()` | ? | |
| AI-5 | `mlp_model.py` has `hidden_dim=128`, weights compatible | ? | |
| AI-6 | Val loop in training + `evals/training_history.json` | ? | |
| AI-7 | `data/raw/roads.graphml` exists locally | ? | |
| AI-8 | `--modalities` argparse flag in training script | ? | |
| AI-9 | `graph_embedding_norm` + `text_embedding_norm` in output | ? | |
| AI-10 | `evals/eval_multimodal.py` has 8-neighbor Spatial Accuracy | ? | |
| AI-11 | `evals/ablation_results/` with 3 experiment CSVs | ? | |

---

### SECTION 3: Implementation Status — Detailed Findings

For each task, write a paragraph with:
- What exists
- What is missing or broken
- The exact file path and line number of the issue
- Whether this is: COMPLETE / PARTIAL / MISSING / BROKEN / MOCKED

---

### SECTION 4: AI Training Audit

Cover these exactly:

**4.1 Dataset Quality**
- Row count, class distribution, null counts (from Phase 3A)
- Is multi-class training possible? YES / NO (blocked)
- Root cause if blocked

**4.2 Training Pipeline**
- Does `train_multimodal.py` run without error? YES / NO
- First crash point and error message (from Phase 3D)
- Are both bugs (encode→embed_texts, hidden_dim mismatch) present?

**4.3 Model Architecture**
- Actual hidden_dim in `mlp_model.py`
- Actual dimensions in `models/urban_mlp.pt`
- Are they compatible? YES / NO

**4.4 Validation Monitoring**
- Is there a val loop? YES / NO
- Does `evals/training_history.json` exist? YES / NO
- Implication for defense

**4.5 Embedding Pipeline**
- Does `Embedder.embed_texts()` work? YES / NO (shape, error)
- Does `ImageEncoder.encode()` work? YES / NO
- Are embeddings non-zero and correctly shaped?

**4.6 Evaluation Metrics**
- Is Spatial Accuracy (8-neighbor) implemented? YES / NO
- Are `graph_embedding_norm` / `text_embedding_norm` in output? YES / NO
- Are 3 ablation CSVs in `evals/ablation_results/`? YES / NO

**4.7 Demo Stability Risk**
- Is `data/raw/roads.graphml` pre-downloaded? YES / NO
- What happens if WiFi is unavailable during demo?

---

### SECTION 5: Test Results

| Test File | Test Name | Result | Error Message |
|-----------|-----------|--------|---------------|
| tests/test_dataset_quality.py | test_label_distribution | PASS/FAIL | |
| tests/test_dataset_quality.py | test_no_null_labels | PASS/FAIL | |
| tests/test_dataset_quality.py | test_class_balance | PASS/FAIL | |
| tests/test_mlp_architecture.py | test_output_shape | PASS/FAIL | |
| tests/test_mlp_architecture.py | test_probabilities_sum_to_one | PASS/FAIL | |
| tests/test_mlp_architecture.py | test_weights_load | PASS/FAIL | |
| tests/test_embedding_pipeline.py | test_embedder_method_exists | PASS/FAIL | |
| tests/test_embedding_pipeline.py | test_embedding_shape | PASS/FAIL | |
| tests/test_embedding_pipeline.py | test_embedding_not_zero | PASS/FAIL | |
| tests/test_fusion_output_schema.py | test_required_fields_documented | PASS/FAIL | |
| tests/test_spatial_accuracy.py | test_spatial_accuracy_exists | PASS/FAIL | |
| tests/test_spatial_accuracy.py | test_spatial_accuracy_perfect_grid | PASS/FAIL | |
| tests/test_spatial_accuracy.py | test_spatial_accuracy_range | PASS/FAIL | |

Also report any pre-existing tests from `tests/test_api_integration.py` and `tests/test_celery_tasks.py`.

---

### SECTION 6: Gap Analysis — Step 2 Phases vs Current Implementation

| Phase | Phase Name | Expected | Actual Status | Gap Description |
|-------|-----------|----------|---------------|-----------------|
| Phase 2 | Multi-modal data collection | POI + roads + satellite loaded | ? | |
| Phase 3 | Data cleaning | WGS84, no nulls, 3 classes | ? | |
| Phase 4 | Graph G=(V,E) | roads.graphml loaded, nodes/edges extracted | ? | |
| Phase 6 | Feature fusion | 643-dim vector, 3 fusion methods | ? | |
| Phase 7 | Base models (GNN/CNN/Text) | GNN not yet; CNN ✅; Text ✅ | ? | |
| Phase 9 | Training | Val monitoring, history JSON, 3-class | ? | |
| Phase 10 | Evaluation | Accuracy, F1, Spatial Accuracy | ? | |
| Phase 11 | Digital Twin NL query | Arabic/English query → cell IDs | ? | |

For each gap: state the missing artifact, the risk it creates for the defense, and the estimated fix time.

---

### SECTION 7: Final Readiness Assessment

Provide:

**7.1 Overall Completion Percentage**
- AI tasks: X / 11 complete (Y%)
- API endpoints: 9 / 20 (45%)
- Step 2 phases: X / 12 (Y%)

**7.2 Current Estimated Defense Score**
- Based on the scoring rubric from the onboarding document (target: 35/50)
- Current estimated score: X/50
- Score after P0 fixes only: ~33/50
- Score after P0+P1 fixes: ~40/50

**7.3 Critical Blockers (Must Fix Before Defense)**
List in priority order. For each: what breaks without it, estimated fix time.

**7.4 Demo Readiness**
- Can a live demo run end-to-end? YES / NO / PARTIAL
- What is the minimum fix set for a working demo?

**7.5 Recommended Next Actions (Ranked)**

| Rank | Action | File | Time Est. | Impact |
|------|--------|------|-----------|--------|
| 1 | Fix dataset labels (3 classes) | data/raw/project.csv | 2 hrs | Unblocks all training |
| 2 | Fix encode→embed_texts | scripts/train_multimodal.py | 15 min | Unblocks training run |
| 3 | Fix hidden_dim mismatch | app/domain/mlp_model.py | 15 min | Fixes weight loading |
| 4 | Add val loop + history JSON | scripts/train_multimodal.py | 30 min | Defense visualization |
| 5 | Pre-download roads.graphml | data/raw/roads.graphml | 10 min | Demo stability |
| 6 | Add graph/text norm fields | app/application/fusion_service.py | 30 min | PRD compliance |
| 7 | Implement Spatial Accuracy | evals/eval_multimodal.py | 2 hrs | Evaluation metric |
| 8 | Add --modalities flag | scripts/train_multimodal.py | 1 hr | Ablation study |
| 9 | Run 3 ablation experiments | evals/ablation_results/ | 2 hrs | Defense table |
| 10 | Write verify_dataset.py | scripts/verify_dataset.py | 30 min | Pre-training safety |

---

## EXECUTION INSTRUCTIONS FOR THE AGENT

1. Work through Phases 1–5 in strict order.
2. In Phase 2, inspect actual file contents — do not trust comments or documentation.
3. In Phase 3, actually run the code and capture real output — not hypothetical.
4. In Phase 4, create all 5 test files if they don't exist, then run `pytest tests/ -v`.
5. In Phase 5, every finding must cite a file name and line number where possible.
6. Never mark a feature as COMPLETE based on its existence alone — verify it actually works.
7. Distinguish clearly: COMPLETE vs PARTIAL vs MISSING vs BROKEN vs MOCKED.
8. The audience for the final report is the project supervisor / faculty advisor.
9. Output the full Phase 5 report in Markdown.

---

*Prompt generated: May 2026 | Context sources: Onboarding Document (Arabic, May 2026), Master Summary Report (2026-05-06), AI Training & Accuracy Report (2026-05-06), API Contract Verification Report (2026-05-06), Tasks Status Report (2026-05-06), Step 2 Student Document, PRD v3.0*
