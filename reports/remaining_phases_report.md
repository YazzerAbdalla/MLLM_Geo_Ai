  
**MLLM-Geo-AI**  
**Remaining Phases & Tasks Report**

Gap Analysis vs Step 2 Plan  ·  May 4, 2026

| Defense Readiness Score | Required Threshold |
| :---: | :---: |
| **22 / 50  — NOT READY** | **≥ 35 / 50** |

| Dimension | Score | Key Problem |
| ----- | ----- | ----- |
| ML Training Quality | **3/10** | Single-class dataset, trivial 100% accuracy |
| Output Schema Completeness | 7/10 | 2 fields missing from PRD v3.0 |
| API Coverage | **6/10** | 7 endpoints missing |
| Step 2 Phase Completion | 5/10 | 8/12 phases partial or missing |
| Demo Stability | **1/10** | MLP weight mismatch \+ POI encoder crash |

# **1\. Current Status — What Was Fixed vs What Remains**

| Issue | Previous | Now | Action Required |
| ----- | :---: | :---: | ----- |
| Class imbalance (all label=0) | **BROKEN** | **BROKEN** | Re-label CSV: map category to 0/1/2 |
| Val split unused in training | **BROKEN** | **BROKEN** | Add val\_loss loop to train\_multimodal.py |
| Graph features hardcoded zeros | **BROKEN** | **FIXED** | Done — real OSMnx features |
| No ablation support (--modalities) | **BROKEN** | **BROKEN** | Add argparse flag to training script |
| Spatial Accuracy metric missing | **MISSING** | **MISSING** | Implement 8-neighbor algorithm in eval |
| MLLM / LLM not integrated | **MISSING** | **MISSING** | Planned P2 — mention in defense |
| Digital Twin NL query (501) | **MISSING** | **MISSING** | Planned P2 — mention in defense |

# **2\. P0 — Critical Fixes (Must Complete Before Defense)**

These 5 issues are hard blockers. The demo will crash or produce meaningless results without them. Estimated total: \~4 hours.

## **P0-1  Fix Dataset Labels — Single Class Problem**

File: data/raw/project.csv

All 973 rows have label=0 (Residential). The model learns nothing and reports trivial 100% accuracy. You must create real multi-class ground truth.

**Fix: remap the category column**

\# Python script — run once to fix the CSV

import pandas as pd

df \= pd.read\_csv('data/raw/project.csv')

label\_map \= {

    'Education': 0,   \# Residential

    'Health':    0,   \# Residential

    \# Add more categories from your data:

    \# 'mall':       1,  'shop': 1,  'bank': 1,  \# Commercial

    \# 'factory':    2,  'industrial': 2,         \# Industrial

}

df\['label'\] \= df\['category'\].str.lower().map(label\_map).fillna(0).astype(int)

df.to\_csv('data/raw/project.csv', index=False)

After fixing: verify df\['label'\].value\_counts() shows at least 2 classes. You need Commercial (label=1) and Industrial (label=2) POIs in your data. If none exist, create \~100 synthetic rows for each class from realistic POI names.

Time estimate: 2 hours

## **P0-2  Fix MLP Weight Dimension Mismatch**

File: app/domain/mlp\_model.py, line 12

Saved model weights use hidden\_dim=256 but the code initializes with hidden\_dim=128. This causes a shape error at load time.

**Fix: change one line**

\# BEFORE (line 12\)

def \_\_init\_\_(self, input\_dim, hidden\_dim=128, output\_dim=3):

\# AFTER

def \_\_init\_\_(self, input\_dim, hidden\_dim=256, output\_dim=3):

OR: delete models/urban\_mlp.pt and retrain with hidden\_dim=128 after fixing P0-1.

Time estimate: 30 minutes

## **P0-3  Fix POI Encoder API Error (encode vs embed\_texts)**

Files: scripts/train\_multimodal.py line 27, and any other callers

The code calls poi\_enc.encode() but the class exposes embed\_texts(). This crashes the entire inference pipeline.

**Fix: global search and replace**

\# Find every occurrence:

grep \-rn 'poi\_enc.encode\\|poi\_encoder.encode' app/ scripts/

\# Replace with:

poi\_enc.embed\_texts(texts)   \# correct method name

Time estimate: 15 minutes

## **P0-4  Add Validation Monitoring During Training**

File: scripts/train\_multimodal.py

train\_test\_split creates a val set (line 54\) but it is never used. The training loop has no val\_loss, so overfitting is undetectable.

**Fix: add val evaluation loop**

\# After the training loop, add:

model.eval()

with torch.no\_grad():

    val\_preds \= model(val\_X)

    val\_loss \= criterion(val\_preds, val\_y)

    val\_acc  \= (val\_preds.argmax(1) \== val\_y).float().mean()

\# Also save training history for defense presentation:

history \= {'train\_loss': train\_losses, 'val\_loss': val\_losses}

import json

json.dump(history, open('evals/training\_history.json','w'))

Time estimate: 30 minutes

## **P0-5  Pre-Download OSM Road Network (Prevent Demo Crash)**

File: app/infrastructure/road\_network.py

No roads.graphml is cached. Without it, the pipeline downloads from OSM at demo time — a 10-30 second delay that can fail on conference WiFi.

**Fix: pre-download before the defense**

python \- \<\<'EOF'

import osmnx as ox

G \= ox.graph\_from\_bbox(30.10, 29.90, 31.30, 31.10, network\_type='drive')

ox.save\_graphml(G, 'data/raw/roads.graphml')

print('Done — road network cached')

EOF

Run this once at home on a good internet connection, commit the file, and the demo will load instantly.

Time estimate: 10 minutes (mostly download time)

# **3\. P1 — Recommended Fixes (Should Complete Before Defense)**

These improve your evaluation score from 22 to approximately 30-35/50 and demonstrate academic rigor.

## **P1-6  Add Ablation Study Support (--modalities flag)**

Files: scripts/train\_multimodal.py, app/application/fusion\_service.py

The Step 2 student document explicitly requires ablation studies (POI only / Image only / All). Without a modality flag, this cannot be demonstrated.

**Fix: add argparse CLI flag**

import argparse

parser \= argparse.ArgumentParser()

parser.add\_argument('--modalities', default='poi,image,graph',

                    help='Comma-separated: poi,image,graph,text')

args \= parser.parse\_args()

modalities \= args.modalities.split(',')

\# Then conditionally build feature vector:

features \= \[\]

if 'poi'   in modalities: features.append(poi\_emb)

if 'image' in modalities: features.append(img\_emb)

if 'graph' in modalities: features.append(graph\_feat)

X \= np.concatenate(features, axis=1)

Run three experiments: poi-only, poi+image, all. Save results to separate CSVs. Show the comparison table in your defense slides.

Time estimate: 1 hour

## **P1-7  Add Missing Output Schema Fields**

File: app/application/fusion\_service.py, around line 133-145

PRD v3.0 requires graph\_embedding\_norm and text\_embedding\_norm in each cell result. Currently missing (\~78% schema compliance).

**Fix: add two lines to the result dict**

result \= {

    'cell\_id': cell\_id,

    'dominant\_class': dominant\_class,

    'confidences': confidences,

    'poi\_top\_categories': poi\_top\_cats,

    'road\_density\_km\_per\_km2': road\_density,

    'node\_count': node\_count,

    'satellite\_thumbnail\_url': thumb\_url,

    'graph\_embedding\_norm': float(np.linalg.norm(graph\_feat)),  \# ADD

    'text\_embedding\_norm':  float(np.linalg.norm(poi\_emb)),     \# ADD

}

Time estimate: 30 minutes

## **P1-8  Save Training History to JSON**

File: scripts/train\_multimodal.py

No loss curve data is persisted. You cannot show a training convergence chart in your defense without this.

**Fix: accumulate and save loss per epoch**

train\_losses \= \[\]

for epoch in range(epochs):

    \# ... training loop ...

    train\_losses.append(float(loss.item()))

import json, os

os.makedirs('evals', exist\_ok=True)

json.dump({'train\_loss': train\_losses, 'val\_loss': val\_losses},

          open('evals/training\_history.json', 'w'))

Time estimate: 15 minutes

## **P1-9  Implement Spatial Accuracy Metric**

File: evals/eval\_multimodal.py

Required by PRD v3.0 FR-29. Spatial Accuracy measures the % of cells where the predicted class matches the majority class among its 8 geographic neighbors — a key urban planning metric.

**Fix: implement 8-neighbor voting**

import numpy as np

def spatial\_accuracy(pred\_grid: np.ndarray) \-\> float:

    """

    pred\_grid: 2D array of predicted class labels (shape: H x W)

    Returns: % cells consistent with their 8 neighbors

    """

    H, W \= pred\_grid.shape

    correct \= 0

    for r in range(H):

        for c in range(W):

            neighbors \= \[\]

            for dr in \[-1,0,1\]:

                for dc in \[-1,0,1\]:

                    if dr==0 and dc==0: continue

                    nr, nc \= r+dr, c+dc

                    if 0\<=nr\<H and 0\<=nc\<W:

                        neighbors.append(pred\_grid\[nr, nc\])

            if neighbors:

                majority \= max(set(neighbors), key=neighbors.count)

                if pred\_grid\[r,c\] \== majority: correct \+= 1

    return correct / (H \* W)

Time estimate: 2 hours

## **P1-10  Add DELETE Job Endpoint**

File: app/interfaces/api.py

Required by PRD v3.0 FR-20. Needed by the frontend Cancel button during classification.

**Fix: add one endpoint**

@router.delete('/api/v1/jobs/{job\_id}')

async def cancel\_job(job\_id: str):

    if job\_id in running\_jobs:

        running\_jobs\[job\_id\]\['status'\] \= 'cancelled'

        return {'status': 'cancelled', 'job\_id': job\_id}

    raise HTTPException(status\_code=404, detail='Job not found')

Time estimate: 30 minutes

# **4\. P2 — Future Work (Mention in Defense as Planned Enhancements)**

These are architecturally complex and beyond what is expected for an MVP defense. Frame them as 'Version 2 roadmap' in your presentation.

| Feature | Description | Reference |
| ----- | ----- | ----- |
| GNN (PyTorch Geometric) | Replace MLP with GraphSAGE or GATConv for spatial reasoning over road graph | PRD FR-13, Phase 7 |
| Full MLLM Integration | LLaMA-3.2-1B or DistilGPT-2 with LoRA fine-tuning for geo-language tasks | PRD FR-34, Phase 8 |
| Digital Twin NL Query | Arabic/English query → GeoJSON cell highlights with spatial explanation | PRD FR-46, Phase 11 |
| Attention Fusion | Replace concat with cross-modal attention to learn modality weights dynamically | PRD FR-12, Phase 6 |
| Geo-MLLM Export | Export trained model as .pt / .gguf / .onnx with auto-generated model card | PRD FR-44, Phase 12 |
| Knowledge Distillation | Compress large LLM into small geo-aware model for edge deployment | Student Doc Phase 12 |

# **5\. Step 2 Phase Completion Map**

Cross-reference of your 12-phase student plan against the audit findings.

| \# | Phase | Status | Remaining Tasks |
| ----- | ----- | ----- | ----- |
| 2 | Multi-Modal Data Collection | **PARTIAL** | Pre-cache roads.graphml (P0-5). No other blockers. |
| 3 | Data Cleaning (WGS84) | **OK** | Backend only — no UI needed. Done. |
| 4 | Graph G=(V,E) | **PARTIAL** | OSMnx integration exists. Cache GraphML (P0-5). GET /graph-topology endpoint missing. |
| 6 | Feature Fusion (643 dim) | **OK** | Concat fusion works. Add ablation flag (P1-6). Add attention fusion as P2. |
| 7 | Base Models (ResNet \+ MiniLM \+ MLP) | **PARTIAL** | ResNet18 \+ MiniLM working. MLP weight mismatch (P0-2). GNN is P2. |
| 9 | Training Artifacts | **PARTIAL** | Fix encode→embed\_texts (P0-3). Add val monitoring (P0-4). Save history JSON (P1-8). |
| 10 | Evaluation Metrics | **PARTIAL** | Fix dataset labels first (P0-1). Then: add Spatial Accuracy (P1-9). Add 2 schema fields (P1-7). |
| 11 | Digital Twin NL Query | **MISSING** | Returns 501\. Full implementation is P2 — mention in defense as planned. |
| 12 | Geo-MLLM Export \+ Demo | **MISSING** | P2 — no .pt/.gguf/.onnx export. No model card. Mention as roadmap. |

# **6\. Prioritized Fix Timeline**

| Priority | ID | File | Task | Hours | Dependency |
| :---: | ----- | ----- | ----- | ----- | ----- |
| **P0** | 1 | data/raw/project.csv | Re-label CSV with multi-class ground truth | 2.0 | None |
| **P0** | 2 | domain/mlp\_model.py:12 | Fix hidden\_dim=256 or retrain | 0.5 | After P0-1 |
| **P0** | 3 | scripts/train\_multimodal.py | encode() → embed\_texts() | 0.25 | None |
| **P0** | 4 | scripts/train\_multimodal.py | Add val\_loss monitoring loop | 0.5 | None |
| **P0** | 5 | data/raw/roads.graphml | Pre-download and cache OSM road network | 0.1 | None |
| **P1** | 6 | train\_multimodal.py | Add \--modalities argparse flag | 1.0 | None |
| **P1** | 7 | fusion\_service.py | Add graph/text embedding norm to output schema | 0.5 | None |
| **P1** | 8 | train\_multimodal.py | Save training history to JSON | 0.25 | P0-4 |
| **P1** | 9 | evals/eval\_multimodal.py | Implement 8-neighbor Spatial Accuracy metric | 2.0 | P0-1 |
| **P1** | 10 | interfaces/api.py | Add DELETE /api/v1/jobs/{job\_id} | 0.5 | None |
| **P2** | 11+ | Multiple | GNN / MLLM / Digital Twin / LoRA / Export | 20+ | Post-defense |

| P0 Total (Must-Fix) | P1 Total (Should-Fix) | Combined Total |
| :---: | :---: | :---: |
| **\~3.35 hours** | **\~4.25 hours** | **\~7.6 hours** |

# **7\. API Coverage Gaps**

9 of 16 PRD v3.0 endpoints are implemented (56%). The table below shows what is missing.

| Endpoint | PRD Ref | Status | Action |
| ----- | ----- | :---: | ----- |
| GET /grid/{id}/graph-topology | FR-08 | **MISSING** | Needed for GNN layer on map. Medium priority. |
| DELETE /api/v1/jobs/{job\_id} | FR-20 | **MISSING** | Simple — add cancel endpoint (P1-10) |
| POST /api/v1/evaluate | FR-28 | **MISSING** | Needed for Spatial Accuracy metric (P1-9) |
| GET /api/v1/evaluate/{id}/export | FR-62 | **MISSING** | Add after /evaluate is working |
| POST /api/v1/mllm/train | FR-40 | **MISSING** | P2 — full MLLM builder, post-defense |
| GET /api/v1/mllm/status/{id} | FR-41 | **MISSING** | P2 — dependent on mllm/train |
| GET /api/v1/mllm/export/{id} | FR-44 | **MISSING** | P2 — dependent on mllm/train |
| POST /api/v1/query (NL query) | FR-48 | **MISSING** | Returns 501\. P2 — Digital Twin, post-defense. |

# **8\. Projected Score After Fixes**

| Dimension | Current | After P0 | After P0+P1 |
| ----- | ----- | ----- | ----- |
| ML Training Quality | **3/10** | **7/10** | **8/10** |
| Output Schema | 7/10 | 7/10 | **9/10** |
| API Coverage | 6/10 | 6/10 | **7/10** |
| Phase Completion | 5/10 | **6/10** | **8/10** |
| Demo Stability | **1/10** | **7/10** | **8/10** |
| **TOTAL** | **22/50** | **33/50** | **40/50** |

P0 alone brings you from 22 to \~33 — just below the 35-point threshold but defensible with strong presentation of limitations.

P0 \+ P1 brings you to \~40 — above the threshold and a solid academic defense.

MLLM-Geo-AI  ·  Remaining Phases Report  ·  May 4, 2026  ·  Generated by AI Engineering Team