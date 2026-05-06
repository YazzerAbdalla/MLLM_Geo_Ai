# Codebase Analysis Report: Multi-Modal Geo-AI

## Executive Summary

Current branch implements multi-modal urban classification pipeline matching the document's architecture requirements. However, **critical ML issues** prevent proper training and evaluation.

**Verdict**: Pipeline architecture ✅ CORRECT, but training quality ❌ FAILING

---

## 1. Pipeline Architecture vs Document Requirements

| Document Phase | Implementation | Status |
|-----------------|---------------|--------|
| **Phase 2: Data Collection** | | |
| Load Road Network (OSMnx) | `RoadNetworkLoader` | ✅ |
| Load POI (OSM) | `Embedder` | ✅ |
| Load Satellite (GEE) | `SatelliteImageLoader` | ✅ |
| **Phase 6: Fusion** | | |
| POI → Embedding | Sentence-Transformer (384 dim) | ✅ |
| Image → CNN | ResNet18 (256 dim) | ✅ |
| Graph → Features | OSMnx degree/length (3 dim) | ✅ |
| Fusion (Concatenation) | `np.concatenate()` | ✅ |
| **Phase 7-8: Model** | | |
| MLP Classifier | UrbanMLP (643→128→3) | ✅ |
| Output | GeoJSON + confidences | ✅ |

---

## 2. Critical Issues Found

### 🔴 Issue 1: SEVERE Class Imbalance (ALL labels = 0)

```
data/raw/project.csv Analysis:
- Total rows: 973
- Label 0 (Residential): 973 (100%)
- Label 1 (Commercial): 0 (0%)
- Label 2 (Industrial): 0 (0%)
```

**Impact**: Model predicts only "Residential" → 100% accuracy is meaningless.

**Evidence**:
```python
# evals/baseline_results.json
{"accuracy": 1.0, "f1_macro": 1.0, "confusion_matrix": [[195]]}
```

The confusion matrix has only 1 row/column → only 1 class present.

---

### 🔴 Issue 2: No Train/Val Split Monitoring

**Current Code** (`scripts/train_multimodal.py`):
```python
train_df, _ = train_test_split(df, test_size=0.2, random_state=42)  # _ is unused!
# Model trained only on train_df, never validates
# No epoch-by-epoch loss tracking
```

**Document Requirement (Phase 9)**:
- "Classification Loss"
- "Fine-tuning"

**Missing**:
- Validation set during training
- Train/val loss curves
- Early stopping

**Cannot detect overfitting** because model never evaluates on validation data.

---

### 🔴 Issue 3: Graph Features NOT Loaded

```python
# scripts/train_multimodal.py:35-36
graph_emb = [0, 0, 0]  # Hardcoded zeros!
# Combined becomes: poi_emb + img_emb + [0, 0, 0]
```

**Impact**: Graph modality contributes 0% to classification.
Only POI + Image are actually used.

---

### 🔴 Issue 4: No Ablation Study Support

**Document Recommends**:
- POI only
- Image only
- POI + Image
- All

**Current Code**: Hardcoded to always use all 3 (but graph is zeros anyway).

---

## 3. Model Architecture Details

### UrbanMLP (app/domain/mlp_model.py)
```python
UrbanMLP(input_dim=643, hidden_dim=128, output_dim=3):
    Linear(643 → 128) → ReLU → Dropout(0.3) → Linear(128 → 3) → Softmax
```

**Anti-overfitting Measures**:
- ✅ Dropout(0.3) present
- ❌ No validation monitoring
- ❌ No L2 regularization
- ❌ No early stopping

**Output Layer**: Softmax on 3 classes (Residential, Commercial, Industrial)

---

## 4. Configuration

### Dimensions (app/config.py)
```python
POI_DIM = 384      # sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2)
IMG_DIM = 256      # ResNet18
GRAPH_DIM = 3       # (node_count, total_length, avg_degree)
FUSION_DIM = 643   # 384 + 256 + 3
```

### Data Storage
```
data/
├── raw/project.csv     # 973 POI records
├── sat_images/        # Satellite patches
├── results/          # Classification outputs
└── thumbnails/       # Preview images
```

---

## 5. Missing Document Requirements

| Document Requirement | Status |
|---------------------|--------|
| **Phase 4: Graph Building** | |
| G = (V, E) nodes/edges | ❌ Not persisted |
| Neighbor nodes relation | ❌ Not extracted |
| **Phase 7: GNN** | |
| PyTorch Geometric | ❌ Not implemented |
| Edge features | ❌ Not used |
| **Phase 7: Vision Encoder** | |
| ResNet/EfficientNet | ✅ ResNet18 |
| **Phase 7: Text Encoder** | |
| MiniLM/BERT | ✅ sentence-transformers |
| **Phase 8: Base Model** | |
| LLaMA (small) | ❌ Not implemented |
| LoRA Fine-tuning | ❌ Not implemented |
| **Fusion Methods** | |
| Concatenation | ✅ Implemented |
| Weighted Fusion | ❌ Not implemented |
| Attention Fusion | ❌ Not implemented |
| Gated Fusion | ❌ Not implemented |
| **Phase 10: Metrics** | |
| Accuracy | ✅ |
| F1-score | ✅ |
| Spatial Accuracy | ❌ Not implemented |
| **Phase 11: Digital Twin** | |
| Interactive Map | ❌ Not implemented |
| Query Capability | ❌ Not implemented |

---

## 6. Encoders Implementation

### POI Encoder (app/infrastructure/ai_model.py)
```python
Embedder(model_name='paraphrase-multilingual-MiniLM-L12-v2')
- Output: 384 dim
- Caching: Redis optional
- Method: mean pooling
```

### Image Encoder (app/infrastructure/image_encoder.py)
```python
ImageEncoder():
- Model: ResNet18 (pretrained)
- Input: 224x224
- Output: 256 dim
- Batch encoding: supported
```

### Road Network (app/infrastructure/road_network.py)
```python
RoadNetworkLoader():
- Input: bbox or place_name
- Output: node_count, total_length, avg_degree (3 dim)
- Method: spatial clip to geometry
```

---

## 7. Training Flow

### Current Pipeline
```
1. Load project.csv
2. Train/val split (unused val)
3. For each row:
   - POI embedding (sentence-transformer)
   - Image embedding (ResNet18)
   - Graph = [0, 0, 0]  ← BUG
4. Concatenate → 643 dim
5. MLP forward
6. CrossEntropyLoss
7. Backprop
8. Save model
```

### Expected Pipeline (per document)
```
1. Load project.csv
2. Train/val/test split (80/10/10)
3. For each row:
   - POI embedding
   - Image embedding  
   - Graph features (from OSMnx)
4. Concatenate → 643 dim
5. MLP forward
6. CrossEntropyLoss
7. Backprop
8. Calculate train/val metrics per epoch
9. Early stopping check
10. Final evaluation on test set
```

---

## 8. Files Changed Summary

```
Branch: HEAD vs master
Files: 75 changed
Insertions: 1,006,798 lines
Deletions: 176 lines
```

### Key New Files
| File | Purpose |
|------|---------|
| `app/application/fusion_service.py` | Multi-modal pipeline |
| `app/infrastructure/image_encoder.py` | ResNet18 encoder |
| `app/infrastructure/road_network.py` | OSMnx loader |
| `app/domain/mlp_model.py` | Classifier |
| `scripts/train_multimodal.py` | Training script |
| `evals/eval_multimodal.py` | Evaluation |

---

## 9. Overfitting Analysis

### Current State: CANNOT DETERMINE

**Reasons**:
1. No validation set used during training
2. All data is label=0 (single class)
3. Train accuracy = 100% expected
4. No test/val to compare

### If Fixed - How to Monitor:
```python
# Proper training loop
for epoch in range(epochs):
    model.train()
    train_loss = compute_loss(train_loader)
    
    model.eval()
    val_loss = compute_loss(val_loader)
    
    if val_loss > best_val_loss + patience:
        break  # Early stopping
    
    # Overfitting detection:
    # train_loss ↓ and val_loss ↑ = OVERFITTING
```

### Model Capacity Analysis
- Input: 643 dim
- Hidden: 128 dim
- Parameters: ~82K
- Training samples: ~800
- **Ratio**: No risk of overfitting with current data size

---

## 10. Recommendations

### Immediate Fixes (Critical)
1. **Fix labels**: Create realistic label distribution (0, 1, 2)
2. **Add train/val split**: Monitor both losses
3. **Load graph features**: Replace `[0, 0, 0]` with actual features
4. **Add early stopping**: Prevent overfitting

### Medium Priority
1. Add ablation study support
2. Implement weighted fusion
3. Add spatial accuracy metric

### Future Enhancements (per document)
1. Implement GNN for spatial relationships
2. Add attention fusion mechanism
3. Integrate small LLM (LLaMA/Distil)
4. Add LoRA fine-tuning
5. Digital twin visualization

---

## 11. Output Format (Verified ✅)

```json
{
  "cell_id": 1,
  "dominant_class": "Residential",
  "confidences": {
    "Residential": 0.85,
    "Commercial": 0.10,
    "Industrial": 0.05
  },
  "road_density_km_per_km2": 2.5,
  "node_count": 10,
  "poi_top_categories": ["school", "hospital"],
  "satellite_thumbnail_url": "/api/v1/thumbnails/grid_xxx/1.jpg"
}
```

Matches document Phase 10 output requirement.

---

## 12. Conclusion

| Aspect | Status |
|--------|--------|
| Architecture | ✅ Matches document |
| Data loading | ⚠️ Partial (graph missing) |
| Training | ❌ No validation |
| Evaluation | ⚠️ Single class only |
| Output format | ✅ Correct |

**Overall**: Pipeline framework is correct, but ML training loop needs fixes before meaningful results can be obtained.

**Next Steps**:
1. Fix label distribution in dataset
2. Add proper train/val/test split
3. Load actual graph features
4. Re-run training and evaluation

---

*Report generated: 2026-04-28*
*Analysis performed by: Senior AI Engineer Review*