# Model Consistency Report | Date: 2026-06-17 | MLLM-Geo-AI Project

## 1. Feature Dimensions

| Feature | Expected Dim | Actual Dim | Status |
|---------|-------------|------------|--------|
| POI (text embedding) | 384 | 384 | ✅ MATCH |
| Image (ResNet-18) | 256 | 256 | ✅ MATCH |
| Graph (OSMnx features) | 3 | 3 | ✅ MATCH |
| Fused | 643 | 643 | ✅ MATCH |

## 2. Model Architecture

**UrbanMLP** (`app/domain/mlp_model.py`):
- input_dim: 643 (FUSION_DIM)
- hidden_dim: 256 (code)
- output_dim: 3

## 3. 🚨 CRITICAL: Model Weight Mismatch

| Property | Training (checkpoint) | Inference (code) | Status |
|----------|---------------------|------------------|--------|
| hidden_dim | **128** | **256** | ❌ MISMATCH |
| input_dim | 643 | 643 | ✅ MATCH |
| output_dim | 3 | 3 | ✅ MATCH |

**Evidence:**
```python
checkpoint = torch.load('models/urban_mlp.pt')
checkpoint['net.0.weight'].shape  # torch.Size([128, 643])
# Code initializes with hidden_dim=256
model = UrbanMLP()  # net.0.weight shape would be [256, 643]
```

**Impact**: Loading the saved model will fail with:
```
RuntimeError: size mismatch for net.0.weight: 
  copying a param with shape torch.Size([128, 643]) from checkpoint, 
  the shape in current model is torch.Size([256, 643])
```

## 4. Recommendation

Either:
1. Change `hidden_dim=128` in `mlp_model.py` to match the saved checkpoint
2. Or retrain the model with `hidden_dim=256`

## 5. Other Model Files

| File | Size | Purpose |
|------|------|---------|
| models/urban_mlp.pt | 333 KB | Main MLP checkpoint (hidden_dim=128) |
| models/random_forest.pkl | 47 KB | Legacy baseline model |
| models/sentence_transformer/ | - | MiniLM model (not checked) |

## 6. Evidence Matrix

| Item | Code Verified | Runtime Verified | Evidence Attached |
|------|:-------------:|:----------------:|:-----------------:|
| Feature Dimensions | YES | YES | YES |
| Model Architecture | YES | YES | YES |
| Weight Compatibility | YES | YES (FAILS) | YES |
