# AI Model Training & Accuracy Report | Date: 2026-05-24 | MLLM-Geo-AI Project

---

## 2A. Dataset Analysis

### Dataset Statistics

| Metric | May 6 | May 24 | Change |
|--------|-------|--------|--------|
| Total Rows | 973 | 1,166 | **+193 (new + relabeled)** |
| Columns | 8 | 8 | Unchanged |
| Missing values | 2 null in text_des | 0 (dropped) | Fixed |

### Category Distribution

| Category | Count | Label |
|----------|-------|-------|
| Health | 592 | 0 (Residential) |
| Education | 379 | 0 (Residential) |
| Bank | 144 | 1 (Commercial) |
| Mall | 40 | 1 (Commercial) |
| Industrial | 11 | 2 (Industrial) |

### Label Distribution

| Label | Class | Count | Percentage |
|-------|-------|-------|------------|
| 0 | Residential | 971 | 83.3% |
| 1 | Commercial | 184 | 15.8% |
| 2 | Industrial | 11 | 0.9% |

**Status: LABELS EXIST (was: all zeros)** — P0-1 resolved.
**Warning**: Class 2 (Industrial) has only 11 real samples. Run `python scripts/relabel_dataset.py` to add 100 synthetic Industrial POIs.

---

## 2B. Model Architecture

### Embedding Dimensions

| Modality | Model | Output Dim |
|----------|-------|-----------|
| POI (Text) | paraphrase-multilingual-MiniLM-L12-v2 | 384 |
| Image | ResNet-18 | 256 |
| Graph | OSMnx features | 3 |
| **Total Fused** | Concatenation | **643** |

### MLP Architecture

```
Input (643) → Linear(643→256) → ReLU → Dropout(0.3) → Linear(256→3) → Softmax
```

| Layer | Input | Output |
|-------|-------|--------|
| fc1 | 643 | 256 |
| relu | 256 | 256 |
| dropout | 256 | 256 |
| fc2 | 256 | 3 |
| softmax | 3 | 3 |

**Status: hidden_dim=256 (was: 128)** — P0-2 resolved.

### Model Weights

| File | Location | Size | Status |
|------|----------|------|--------|
| urban_mlp.pt | models/ | 0.3 MB | Exists |
| random_forest.pkl | models/ | ~0 MB | Exists |
| model.safetensors | models/sentence_transformer/ | 448.8 MB | Exists |

---

## 2C. Training Metrics

### Training History (20 epochs)

| Metric | Value |
|--------|-------|
| Final Train Loss | 0.5519 |
| Final Val Loss | 0.5517 |
| Final Val Accuracy | 100% |
| Epochs to 100% Val Acc | **Epoch 5** |

### Evaluation Results (test set)

| Metric | Value |
|--------|-------|
| Accuracy | 1.0 (100%) |
| F1 Macro | 1.0 |
| F1 per class | [1.0, 1.0, 1.0] |
| Spatial Accuracy | **0.8455** (8-neighbor voting) |
| Confusion Matrix | [[198,0,0], [0,33,0], [0,0,3]] |

**Note**: 100% accuracy on test set (234 samples) suggests the synthetic data or train/test split may be too easy. Spatial accuracy of 0.8455 is a more realistic metric.

---

## 2D. Ablation Study

### Ablation Results (from evals/ablation_results/)

| Experiment | Accuracy | F1-Score | Spatial Accuracy |
|------------|----------|----------|-----------------|
| POI Only | 1.0 | 1.0 | N/A |
| POI + Image | 1.0 | 1.0 | 0.8455 |
| Full Model | 1.0 | 1.0 | 0.8455 |

**Limitation**: All experiments show 1.0 accuracy, making ablation comparison uninformative. This is due to limited data diversity (overfitting to simple synthetic patterns).

---

## 2E. Identified Weaknesses

| Issue | Severity | Recommendation |
|-------|----------|----------------|
| Class 2 only 11 samples (needs synthetic generation) | MEDIUM | Run `python scripts/relabel_dataset.py` |
| 100% test accuracy (overfitting concern) | MEDIUM | Use real-world test data with harder examples |
| Graph features hardcoded as [0,0,0] in eval | LOW | Integrate real OSMnx features |
| Synthetic coordinates randomly placed | LOW | Use realistic spatial distribution |
| No attention fusion (concat only) | LOW | Post-MVP enhancement |

---

## Summary

| Metric | May 6 | May 24 | Verdict |
|--------|-------|--------|---------|
| Dataset Size | 973 | 1,166 | Growth |
| Categories | 2 (Health, Education) | 5 (Health, Education, Bank, Mall, Industrial) | Expanded |
| Labeled Samples | 0 (0%) | 1,166 (100%) | **CRITICAL FIX** |
| Model Trainable | NO | YES | **FIXED** |
| hidden_dim | 128 | 256 | **FIXED** |
| Training History | Missing | 20 epochs saved | **FIXED** |
| Ablation Study | Not possible | 7 CSV results | **FIXED** |
| Spatial Accuracy | Missing | 0.8455 (8-neighbor) | **FIXED** |

---

*Report generated: 2026-05-24*
*Project: MLLM-Geo-AI Urban Classification System*
