# AI Model Training & Accuracy Report | Date: 2026-05-06 | MLLM-Geo-AI Project

---

## 2A. Dataset Analysis

### Dataset Statistics

| Metric | Value |
|--------|-------|
| Total Rows | 973 |
| Columns | 8 (longitude, latitude, osm_id, name, place_type, category, text_des, label) |
| Missing Values | 2 null in text_des column |
| Unique Grid Cells | 973 |

### Category Distribution

| Category | Count | Percentage |
|----------|-------|------------|
| Health | 594 | 61.1% |
| Education | 379 | 38.9% |
| **Total** | **973** | **100%** |

### Top 10 Most Frequent POI Types

| Rank | POI Type | Count |
|------|----------|-------|
| 1 | Hospital/Health | 594 |
| 2 | School/Education | 379 |

**Note**: Dataset is limited to Health and Education POIs only. No Commercial or Industrial POIs present in current dataset.

### Label Distribution

| Label | Class | Count | Percentage |
|-------|-------|-------|------------|
| 0 | Unknown/Unlabeled | 973 | 100% |

**CRITICAL**: All labels are 0 (unlabeled). There is no ground truth for training. The model cannot be trained until labeled data is available.

---

## 2B. Model Architecture Inspection

### Embedding Dimensions

| Modality | Model | Output Dimension |
|----------|-------|-------------------|
| POI (Text) | paraphrase-multilingual-MiniLM-L12-v2 | 384 |
| Image | ResNet-18 | 256 |
| Graph | OSMnx (node_count, total_length, avg_degree) | 3 |
| **Total Fused** | Concatenation | **643** |

### MLP Architecture

```
Input (643) → Linear(643→128) → ReLU → Dropout(0.3) → Linear(128→3) → Softmax
```

| Layer | Input | Output |
|-------|-------|--------|
| fc1 | 643 | 128 |
| relu | 128 | 128 |
| dropout | 128 | 128 |
| fc2 | 128 | 3 |
| softmax | 3 | 3 |

### Model Weights

| File | Location | Status |
|------|----------|--------|
| urban_mlp.pt | models/ | ✅ Exists |

---

## 2C. Training Metrics

### Status: TRAINING NOT POSSIBLE

**Reason**: Dataset has no ground truth labels. All 973 POIs have label=0 (unlabeled). Cannot perform classification training without labeled data.

### Recommended Train/Validation/Test Split

Since no labels exist, we recommend the following split for future labeled data:

| Dataset Size | Train | Validation | Test |
|--------------|-------|------------|------|
| < 200 cells | 70% | 15% | 15% |
| 200-500 cells | 75% | 12.5% | 12.5% |
| > 500 cells | 80% | 10% | 10% |

For current 973 samples (if labeled):
- Train: 778 samples (80%)
- Validation: 97 samples (10%)
- Test: 98 samples (10%)

---

## 2D. Ablation Study

### Status: NOT POSSIBLE

Ablation studies require trained models with ground truth labels. Since no labels exist, ablation cannot be performed.

### Would-Be Ablation Design (for future)

| Combination | Description |
|-------------|-------------|
| POI only | 384-dim embedding → MLP |
| Image only | 256-dim embedding → MLP |
| POI + Graph | 384 + 3 = 387-dim → MLP |
| All modalities | 384 + 256 + 3 = 643-dim → MLP |

---

## 2E. Identified Weaknesses & Recommendations

### Data Quality Issues

| Issue | Severity | Recommendation |
|-------|----------|-----------------|
| Only 2 categories (Health, Education) | HIGH | Collect Commercial & Industrial POIs |
| No ground truth labels | CRITICAL | Label at least 200 cells manually |
| Missing text descriptions | LOW | Fill 2 missing text_des values |
| No satellite images | HIGH | Download Sentinel-2 for Cairo bbox |
| No road network data | HIGH | Download OSM road data |

### Model Architecture Improvements

| Improvement | Impact |
|-------------|--------|
| Add GNN (PyTorch Geometric) | High - for spatial relationships |
| Attention-based fusion | Medium - better than concat |
| LoRA fine-tuning for MLLM | High - custom model training |

---

## Summary

| Metric | Status |
|--------|--------|
| Dataset Size | 973 POIs |
| Categories | 2 (Health, Education) |
| Labeled Samples | 0 (0%) |
| Trainable | ❌ NO - No ground truth |
| Model Weights | ✅ Loaded from models/urban_mlp.pt |
| Ablation Study | ❌ NOT POSSIBLE |

**Conclusion**: The AI model architecture is correctly implemented with 643-dimensional input (384 POI + 256 Image + 3 Graph). However, **training is not possible** because all data points have label=0 (unlabeled). The team must collect labeled ground truth data before any training can occur.

---

*Report generated: 2026-05-06*
*Project: MLLM-Geo-AI Urban Classification System*