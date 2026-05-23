````md
# AI Tasks — MLLM-Geo-AI Onboarding Document

Source: onboarding_team_arabic.pdf  
Project: MLLM-Geo-AI — Urban AI Dashboard  
Version: v1.0 — May 2026

---

# AI Team Structure

## Student 3 — AI / Data
Responsible for:
- Dataset fixing
- Multi-class CSV labeling
- Data preparation

## Student 4 — AI / Training
Responsible for:
- Training pipeline fixes
- Validation monitoring
- Training history persistence
- Model stability

## Student 5 — AI / Evaluation
Responsible for:
- Spatial Accuracy
- Ablation Study
- Evaluation metrics
- Output schema completion

---

# AI Tasks

---

# Student 3 — AI / Data Tasks

## AI-1 — Re-label Dataset CSV

### Priority
P0 — Critical

### File
`data/raw/project.csv`

### Objective
Fix the single-class dataset problem.

### Required Work
- Re-map `category` column into 3 urban classes:
  - Education / Health → 0 (Residential)
  - Mall / Shop / Bank → 1 (Commercial)
  - Factory / Industrial → 2 (Industrial)

### Validation
Verify:
```python
df['label'].value_counts()
````

### Additional Requirement

If commercial or industrial POIs do not exist:

* Generate approximately 100 synthetic rows for each missing class.

### Expected Output

* Corrected multi-class dataset
* At least 3 classes present
* Balanced enough distribution for training

---

## AI-2 — Verify Data Loader Reads Labels

### Priority

P1 — Important

### File

`app/infrastructure/data_loader.py`

### Objective

Ensure the data loader:

* Reads the new `label` column
* Passes labels correctly into the AI pipeline

### Expected Output

* Functional label-aware pipeline
* Correct label propagation during training

---

## AI-3 — Create Dataset Verification Script

### Priority

P1 — Important

### File

`scripts/verify_dataset.py` (new)

### Objective

Create a quick dataset verification script.

### Required Checks

* Number of classes
* Class distribution
* Empty/null values
* Dataset statistics

### Expected Output

* Executable verification script
* Human-readable dataset diagnostics before training

---

# Student 4 — AI / Training Tasks

## AI-4 — Fix Encoder Method Call

### Priority

P0 — Critical

### File

`scripts/train_multimodal.py`

### Objective

Replace:

```python
poi_enc.encode()
```

With:

```python
poi_enc.embed_texts()
```

### Additional Requirement

Search globally:

```bash
grep -rn 'poi_enc.encode|poi_encoder.encode' app/ scripts/
```

### Expected Output

* Working embedding pipeline
* No encoder API crashes

---

## AI-5 — Fix MLP Hidden Dimension Mismatch

### Priority

P0 — Critical

### File

`app/domain/mlp_model.py`

### Objective

Fix hidden dimension mismatch.

### Required Change

Change:

```python
hidden_dim=128
```

To:

```python
hidden_dim=256
```

OR:

* Retrain the model after fixing dataset labels.

### Expected Output

* Model weights load correctly
* No runtime shape mismatch errors

---

## AI-6 — Add Validation Monitoring + Training History

### Priority

P0 — Critical

### File

`scripts/train_multimodal.py`

### Objective

Add validation evaluation during training.

### Required Metrics

* `val_loss`
* `val_accuracy`

### Additional Requirement

Save:

```json
evals/training_history.json
```

### Expected Output

* Validation monitoring loop
* Persisted training history
* Defense-ready training curves

---

## AI-7 — Cache OSM Road Network

### Priority

P0 — Critical

### File

`data/raw/roads.graphml` (new)

### Objective

Pre-download and cache OSM road network locally.

### Required Script

```python
import osmnx as ox

G = ox.graph_from_bbox(
    30.10,
    29.90,
    31.30,
    31.10
)

ox.save_graphml(
    G,
    'data/raw/roads.graphml'
)
```

### Expected Output

* Local cached graph
* Faster and stable demo execution
* No live OSM download during defense

---

## AI-8 — Add Ablation Study Support

### Priority

P1 — Important

### File

`scripts/train_multimodal.py`

### Objective

Add support for modality ablation experiments.

### Required CLI Flag

```bash
--modalities
```

### Example

```bash
python train.py --modalities poi
python train.py --modalities poi,image,graph
```

### Required Behavior

Build feature vectors conditionally based on selected modalities.

### Expected Output

* Configurable modality training
* Support for:

  * POI only
  * POI + Image
  * POI + Image + Graph

---

# Student 5 — AI / Evaluation Tasks

## AI-9 — Add Missing Embedding Norm Fields

### Priority

P1 — Important

### File

`app/application/fusion_service.py`

### Objective

Add missing output schema fields.

### Required Fields

```python
graph_embedding_norm
text_embedding_norm
```

### Example

```python
graph_embedding_norm = float(np.linalg.norm(graph_feat))
text_embedding_norm  = float(np.linalg.norm(poi_emb))
```

### Reference

PRD v3.0 — FR-29

### Expected Output

* Complete output schema
* Improved PRD compliance

---

## AI-10 — Implement Spatial Accuracy

### Priority

P1 — Important

### File

`evals/eval_multimodal.py`

### Objective

Implement 8-neighbor Spatial Accuracy metric.

### Logic

For every cell:

* Find 8 neighboring cells
* Compute majority class
* Compare prediction consistency

### Required Output

Spatial consistency percentage.

### Reference

PRD v3.0 — FR-29

### Expected Output

* Functional spatial evaluation metric
* Geographic consistency measurement

---

## AI-11 — Run Ablation Study Experiments

### Priority

P1 — Important

### Directory

`evals/ablation_results/`

### Objective

Run 3 ablation experiments:

1. POI only
2. POI + Image
3. All modalities

### Required Output

* Separate CSV result for each experiment
* Comparison table for defense presentation

### Expected Deliverables

* Ablation evaluation reports
* Comparative metrics
* Defense-ready experiment analysis

---

# Expected AI Deliverables Summary

## Dataset Deliverables

* Multi-class labeled dataset
* Dataset verification script
* Synthetic data if required

## Training Deliverables

* Stable multimodal training pipeline
* Validation monitoring
* Training history JSON
* Cached road graph
* Working embedding pipeline

## Evaluation Deliverables

* Spatial Accuracy implementation
* Ablation Study support
* Ablation experiment results
* Complete schema fields

## Defense Deliverables

* Training curves
* Evaluation metrics
* Ablation comparison tables
* Stable demo-ready pipeline

```