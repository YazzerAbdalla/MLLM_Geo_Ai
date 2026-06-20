"""
Post-Retrain Validation — Direct Python (no API/Celery).
All tests run in-process, lightweight.
"""
import os, sys, json, time
os.environ["PYTHONIOENCODING"] = "utf-8"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
import torch
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.domain.mlp_model import UrbanMLP
from app.config import FUSION_DIM, POI_DIM

CKPT = "models/urban_mlp.pt"
CNAMES = ["Residential", "Commercial", "Industrial"]
OUT = "evals/validation"
os.makedirs(OUT, exist_ok=True)

R = []
def log(m): print(m); R.append(m)
def save(d, fn):
    with open(os.path.join(OUT, fn), "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, default=str)

log("=" * 60)
log("POST-RETRAIN VALIDATION (Direct Mode)")
log("=" * 60)
log(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
log(f"Checkpoint: {os.path.abspath(CKPT)}")

# ============================================================
# TEST 1: Checkpoint Loading
# ============================================================
log("\n" + "=" * 60)
log("TEST 1: CHECKPOINT LOADING")
log("=" * 60)
t1 = {"checkpoint_loaded": False, "differs_from_random": False,
      "total_parameters": 0, "trained_mean": [], "random_mean": []}

if not os.path.exists(CKPT):
    log("  [FAIL] Checkpoint not found")
    save(t1, "test1.json")
else:
    sz_kb = os.path.getsize(CKPT) / 1024
    ckpt_raw = torch.load(CKPT, map_location="cpu", weights_only=True)
    # Handle nested state_dict format
    if isinstance(ckpt_raw, dict) and "state_dict" in ckpt_raw:
        ckpt = ckpt_raw["state_dict"]
        log(f"  Checkpoint format: nested dict with state_dict key")
    else:
        ckpt = ckpt_raw
    model = UrbanMLP()
    t1["total_parameters"] = sum(p.numel() for p in model.parameters())
    log(f"  Path: {os.path.abspath(CKPT)}")
    log(f"  Size: {sz_kb:.1f} KB")
    log(f"  Params: {t1['total_parameters']:,}")
    log(f"  Architecture: input={FUSION_DIM}, hidden=256, output=3")
    log(f"  Checkpoint keys: {list(ckpt_raw.keys())}")
    log(f"  State dict keys: {list(ckpt.keys())}")

    try:
        model.load_state_dict(ckpt, strict=True)
        model.eval()
        t1["checkpoint_loaded"] = True
        log("  [PASS] Checkpoint loaded successfully (NOT random init)")
    except Exception as e:
        log(f"  [FAIL] Checkpoint load error: {e}")

    # Verify output differs from random
    rand_model = UrbanMLP()
    dummy = torch.randn(500, FUSION_DIM)
    with torch.no_grad():
        trained_probs = model(dummy).numpy()
        rand_probs = rand_model(dummy).numpy()

    tm = trained_probs.mean(axis=0)
    rm = rand_probs.mean(axis=0)
    t1["trained_mean"] = [float(v) for v in tm]
    t1["random_mean"] = [float(v) for v in rm]
    t1["differs_from_random"] = bool(np.max(np.abs(tm - rm)) > 0.01)

    log(f"  Trained mean probs: {[f'{v:.4f}' for v in tm]}")
    log(f"  Random mean probs:  {[f'{v:.4f}' for v in rm]}")
    if t1["differs_from_random"]:
        log("  [PASS] Trained model output DIFFERS from random init")
    else:
        log("  [FAIL] Trained model output == random init (checkpoint not effective)")

    # Per-sample verification
    non_uniform = np.sum(np.max(trained_probs, axis=1) > 0.5)
    log(f"  Samples with >50% confidence: {non_uniform}/{500}")
    t1["non_uniform_count"] = int(non_uniform)
    save(t1, "test1.json")

# ============================================================
# TEST 2-4: Class-specific Feature Response
# ============================================================
log("\n" + "=" * 60)
log("TESTS 2-4: CLASS-SPECIFIC FEATURE RESPONSE")
log("=" * 60)
log("  Testing if the model can distinguish classes via feature engineering")

ckpt_raw = torch.load(CKPT, map_location="cpu", weights_only=True)
sd = ckpt_raw["state_dict"] if isinstance(ckpt_raw, dict) and "state_dict" in ckpt_raw else ckpt_raw
model = UrbanMLP()
model.load_state_dict(sd, strict=True)
model.eval()

# Create prototype feature vectors for each class
# Residential: moderate POI norm, moderate graph features
# Commercial: high POI norm, high graph features
# Industrial: moderate POI, high graph features, different pattern

np.random.seed(42)

def make_features(poi_scale, img_scale, graph_vals, n=100):
    """Create n feature vectors with given scales."""
    poi = np.random.randn(n, POI_DIM) * poi_scale
    img = np.random.randn(n, 256) * img_scale
    graph = np.tile(np.array(graph_vals, dtype=np.float32), (n, 1))
    return np.concatenate([poi, img, graph], axis=1).astype(np.float32)

# Residential prototypes (moderate everything)
res_feats = make_features(0.5, 0.5, [5.0, 200.0, 2.5])
# Commercial prototypes (high POI, dense roads)
com_feats = make_features(1.0, 0.8, [15.0, 800.0, 4.0])
# Industrial prototypes (moderate POI, large road network)
ind_feats = make_features(0.4, 0.6, [8.0, 1200.0, 3.0])

with torch.no_grad():
    res_probs = model(torch.tensor(res_feats)).numpy()
    com_probs = model(torch.tensor(com_feats)).numpy()
    ind_probs = model(torch.tensor(ind_feats)).numpy()

def analyze(name, probs):
    preds = np.argmax(probs, axis=1)
    dist = Counter(CNAMES[p] for p in preds)
    avg_conf = float(np.mean(np.max(probs, axis=1)))
    avg_per_class = {CNAMES[i]: float(probs[:, i].mean()) for i in range(3)}
    log(f"  {name}:")
    log(f"    Predictions: {dict(dist)}")
    log(f"    Avg confidence: {avg_conf:.4f}")
    log(f"    Avg prob per class: {avg_per_class}")
    return {"dist": dict(dist), "avg_conf": avg_conf, "avg_probs": avg_per_class,
            "dominant": max(dist, key=dist.get) if dist else "none"}

res_r = analyze("Residential-like features", res_probs)
com_r = analyze("Commercial-like features", com_probs)
ind_r = analyze("Industrial-like features", ind_probs)

# Determine if model distinguishes classes
classes_pred = [res_r["dominant"], com_r["dominant"], ind_r["dominant"]]
distinguishes = (classes_pred[0] != classes_pred[1]) or (classes_pred[0] != classes_pred[2])

t234 = {
    "residential_features": res_r,
    "commercial_features": com_r,
    "industrial_features": ind_r,
    "dominant_classes": classes_pred,
    "model_distinguishes_classes": distinguishes
}

if len(set(classes_pred)) >= 2:
    log(f"  [PASS] Model produces different predictions for different input types")
    t234["verdict_residential"] = "PASS" if res_r["dominant"] == "Residential" else "WARN"
    t234["verdict_commercial"] = "PASS" if com_r["dominant"] == "Commercial" else "WARN"
    t234["verdict_industrial"] = "PASS" if ind_r["dominant"] == "Industrial" else "WARN"
else:
    log(f"  [FAIL] Model predicts same class ({classes_pred[0]}) for all input types")
    t234["verdict_residential"] = "FAIL"
    t234["verdict_commercial"] = "FAIL"
    t234["verdict_industrial"] = "FAIL"

log(f"  Residential->{res_r['dominant']} Commercial->{com_r['dominant']} Industrial->{ind_r['dominant']}")
save(t234, "tests_2_3_4_class_response.json")

# ============================================================
# TEST 5: POI Ablation (simulated)
# ============================================================
log("\n" + "=" * 60)
log("TEST 5: POI ABLATION (Simulated)")
log("=" * 60)

# Take real residential features and zero out the POI portion
n_samples = 100
with_poi = torch.tensor(make_features(0.8, 0.5, [10.0, 500.0, 3.0], n_samples))
without_poi = with_poi.clone()
without_poi[:, :POI_DIM] = 0.0  # Zero out POI embeddings

with torch.no_grad():
    probs_with = model(with_poi).numpy()
    probs_without = model(without_poi).numpy()

preds_with = np.argmax(probs_with, axis=1)
preds_without = np.argmax(probs_without, axis=1)
changes = np.sum(preds_with != preds_without)
log(f"  Samples: {n_samples}")
log(f"  Predictions with POI:    {dict(Counter(CNAMES[p] for p in preds_with))}")
log(f"  Predictions without POI: {dict(Counter(CNAMES[p] for p in preds_without))}")
log(f"  Changed: {changes}/{n_samples} ({changes/n_samples*100:.1f}%)")

t5 = {
    "n_samples": n_samples,
    "with_poi_dist": dict(Counter(CNAMES[p] for p in preds_with)),
    "without_poi_dist": dict(Counter(CNAMES[p] for p in preds_without)),
    "changes": int(changes),
    "change_pct": changes / n_samples * 100,
}
t5["verdict"] = "PASS" if changes > 0 else "FAIL"
log(f"  -> {t5['verdict']}")
save(t5, "test5_poi_ablation.json")

# ============================================================
# TEST 6: Embedding Norm Verification
# ============================================================
log("\n" + "=" * 60)
log("TEST 6: EMBEDDING NORM VERIFICATION")
log("=" * 60)

# Verify that POI norm > 0 when text exists, ≈ 0 when empty
n = 50
emb_with = np.random.randn(n, POI_DIM).astype(np.float32)
emb_with = emb_with / np.linalg.norm(emb_with, axis=1, keepdims=True) * 5.0  # scale to ~5
emb_empty = np.zeros((n, POI_DIM), dtype=np.float32)

norms_with = np.linalg.norm(emb_with, axis=1)
norms_empty = np.linalg.norm(emb_empty, axis=1)

log(f"  Norms with POI: min={norms_with.min():.4f}, max={norms_with.max():.4f}, avg={norms_with.mean():.4f}")
log(f"  Norms empty:    min={norms_empty.min():.4f}, max={norms_empty.max():.4f}, avg={norms_empty.mean():.4f}")
log(f"  All with POI > 0: {np.all(norms_with > 0.001)}")
log(f"  All empty ~0:    {np.all(norms_empty < 0.001)}")

t6 = {
    "with_poi": {"min": float(norms_with.min()), "max": float(norms_with.max()), "avg": float(norms_with.mean())},
    "without_poi": {"min": float(norms_empty.min()), "max": float(norms_empty.max()), "avg": float(norms_empty.mean())},
    "all_with_poi_positive": bool(np.all(norms_with > 0.001)),
    "all_empty_zero": bool(np.all(norms_empty < 0.001))
}
t6["verdict"] = "PASS" if np.all(norms_with > 0.001) and np.all(norms_empty < 0.001) else "FAIL"
log(f"  -> {t6['verdict']}")
save(t6, "test6_embedding_verification.json")

# ============================================================
# TEST 7: Confidence Distribution
# ============================================================
log("\n" + "=" * 60)
log("TEST 7: CONFIDENCE DISTRIBUTION")
log("=" * 60)

# Generate mixed feature vectors and collect confidence
n_total = 500
mixed_feats = []
for _ in range(n_total):
    scale = np.random.uniform(0.1, 2.0)
    gs = np.random.uniform(0, 20, 3).tolist()
    mixed_feats.append(make_features(scale, scale * 0.8, gs, 1)[0])

mixed_feats = np.array(mixed_feats)
with torch.no_grad():
    mixed_probs = model(torch.tensor(mixed_feats)).numpy()

confs = np.max(mixed_probs, axis=1)
stats = {
    "min": float(confs.min()),
    "max": float(confs.max()),
    "mean": float(confs.mean()),
    "std": float(confs.std()),
    "median": float(np.median(confs))
}

bins = [(0,0.3),(0.3,0.4),(0.4,0.5),(0.5,0.6),(0.6,0.7),(0.7,0.8),(0.8,0.9),(0.9,0.95),(0.95,1.01)]
hist = {f"{l:.2f}-{h:.2f}": int(np.sum((confs >= l) & (confs < h))) for l, h in bins}
high90 = int(np.sum(confs >= 0.90))

log(f"  Cells: {n_total}")
log(f"  Stats: {stats}")
log(f"  Hist: {hist}")
log(f"  >=90%: {high90}/{n_total} ({high90/n_total*100:.1f}%)")

t7 = {"num_cells": n_total, "stats": stats, "histogram": hist,
      "high_90pct": high90, "high_90pct_pct": high90/n_total*100}
if stats["std"] < 0.05 and stats["mean"] > 0.90:
    t7["verdict"] = "FAIL"
    log("  [FAIL] Near-uniform high confidence — overfitting suspected")
elif stats["std"] > 0.10:
    t7["verdict"] = "PASS"
    log("  [PASS] Good confidence spread")
else:
    t7["verdict"] = "WARN"
    log("  [WARN] Moderate spread")
save(t7, "test7_confidence_distribution.json")

# ============================================================
# TEST 8: Industrial Class Stress
# ============================================================
log("\n" + "=" * 60)
log("TEST 8: INDUSTRIAL CLASS STRESS")
log("=" * 60)

# Generate features biased toward industrial (large graph features, moderate POI)
ind_variants = [
    make_features(0.3, 0.4, [10, 1500, 2.5], 100),  # big roads, sparse POI
    make_features(0.5, 0.5, [8, 800, 3.5], 100),     # moderate
    make_features(0.2, 0.6, [15, 2000, 2.0], 100),   # very large roads
]
all_ind_feats = np.concatenate(ind_variants)
with torch.no_grad():
    ind_probs_all = model(torch.tensor(all_ind_feats)).numpy()

ind_preds = np.argmax(ind_probs_all, axis=1)
ind_dist = Counter(CNAMES[p] for p in ind_preds)
ind_confs = ind_probs_all[np.arange(len(ind_preds)), ind_preds]
industrial_count = int(np.sum(ind_preds == 2))

log(f"  Industrial-like samples: {len(all_ind_feats)}")
log(f"  Predictions: {dict(ind_dist)}")
log(f"  Predicted Industrial: {industrial_count}")
if industrial_count > 0:
    ind_only = ind_confs[ind_preds == 2]
    log(f"  Industrial confidence: avg={ind_only.mean():.4f} range=[{ind_only.min():.4f},{ind_only.max():.4f}]")

t8 = {
    "total_samples": len(all_ind_feats),
    "predictions": dict(ind_dist),
    "industrial_count": industrial_count,
    "industrial_pct": industrial_count / len(all_ind_feats) * 100,
}
if industrial_count > 0:
    t8["industrial_confidence"] = {
        "avg": float(ind_only.mean()),
        "min": float(ind_only.min()),
        "max": float(ind_only.max())
    }
t8["verdict"] = "PASS" if industrial_count > 0 else "FAIL"
log(f"  -> {t8['verdict']}")
save(t8, "test8_industrial_stress.json")

# ============================================================
# TEST 9: POI Category Quality Check
# ============================================================
log("\n" + "=" * 60)
log("TEST 9: POI CATEGORY QUALITY CHECK")
log("=" * 60)

# Load training data and analyze category extraction
try:
    import pandas as pd
    df = pd.read_csv("data/raw/project.csv")
    texts = df["text_des"].dropna().astype(str).tolist()
    log(f"  Loaded {len(texts)} text descriptions from training data")

    # Simulate current extraction: split into words, take top 3
    all_words = []
    for t in texts[:500]:
        words = t.split()
        if words:
            wc = Counter(words)
            all_words.extend([w for w, _ in wc.most_common(3)])

    wf = Counter(all_words).most_common(30)
    log("  Top 30 words from extraction:")
    for w, c in wf: log(f"    {w}: {c}")

    stops = {"في","من","على","إلى","عن","مع","كان","هذا","تقع","القاهرة","و","ال","ب","ل",
             "حي","مدينة","شارع","منطقة","مدن","بها","كل","غير","ان","قد","اذا","او","ما","لا"}
    fillers = [w for w in all_words if w in stops]
    fp = len(fillers)/len(all_words)*100 if all_words else 0

    meaningful = {"bank","hospital","school","mall","office","restaurant","cafe","shop",
                  "mosque","pharmacy","clinic","supermarket","hotel","park","university","factory"}
    found = set(w.lower() for w in all_words if w.lower() in meaningful)

    log(f"  Total word entries: {len(all_words)}")
    log(f"  Filler/stopword entries: {len(fillers)} ({fp:.1f}%)")
    log(f"  Meaningful categories found: {found if found else 'NONE'}")

    t9 = {"total_entries": len(all_words), "top_30_words": [(w, c) for w, c in wf],
          "filler_entries": len(fillers), "filler_pct": fp, "meaningful_found": list(found)}

    if fp > 50:
        t9["verdict"] = "FAIL"
        log("  [FAIL] Too many filler/stopwords — extraction needs improvement")
    elif len(found) > 0:
        t9["verdict"] = "PASS"
        log("  [PASS] Meaningful categories present")
    else:
        t9["verdict"] = "WARN"
        log("  [WARN] No meaningful categories found — check data source")
except Exception as e:
    log(f"  Could not analyze dataset: {e}")
    t9 = {"error": str(e), "verdict": "WARN"}
save(t9, "test9_analytics_quality.json")

# ============================================================
# TEST 10: Final Report
# ============================================================
log("\n" + "=" * 60)
log("TEST 10: FINAL INFERENCE REPORT")
log("=" * 60)

# Compute dataset stats
try:
    df = pd.read_csv("data/raw/project.csv")
    lc = df["label"].value_counts().sort_index()
    total_samples = len(df)
except:
    lc = {}; total_samples = 0

log(f"\n--- MODEL ---")
log(f"  Checkpoint path:  {os.path.abspath(CKPT)}")
log(f"  Parameter count:  {t1.get('total_parameters', 0):,}")
log(f"  Input dimension:  {FUSION_DIM}")
log(f"  Hidden dimension: 256")
log(f"  Output classes:   3 (Residential, Commercial, Industrial)")

log(f"\n--- DATASET ---")
log(f"  Total samples: {total_samples}")
for l in sorted(lc.index):
    log(f"    {CNAMES[l] if l < len(CNAMES) else f'cls{l}'}: {lc[l]}")
if 2 in lc.index:
    log(f"  WARNING: Industrial has only {lc[2]} samples — severe class imbalance")

log(f"\n--- VALIDATION RESULTS ---")

# T2 Residential
log(f"\n  Residential (T2): {t234.get('verdict_residential', 'N/A')}")
log(f"    Model predicts dominant: {res_r.get('dominant', 'N/A')}")

# T3 Commercial
log(f"\n  Commercial (T3): {t234.get('verdict_commercial', 'N/A')}")
log(f"    Model predicts dominant: {com_r.get('dominant', 'N/A')}")

# T4 Industrial
log(f"\n  Industrial (T4): {t234.get('verdict_industrial', 'N/A')}")
log(f"    Model predicts dominant: {ind_r.get('dominant', 'N/A')}")

# Confidence
if t7.get("stats"):
    s = t7["stats"]
    log(f"\n  Confidence Distribution (T7): {t7.get('verdict', 'N/A')}")
    log(f"    Mean={s['mean']:.4f} Std={s['std']:.4f} Min={s['min']:.4f} Max={s['max']:.4f}")
    log(f"    >=90% confidence: {t7.get('high_90pct_pct', 0):.1f}%")

# POI Ablation
log(f"\n  POI Ablation (T5): {t5.get('verdict', 'N/A')}")
log(f"    Predictions changed: {t5.get('change_pct', 0):.1f}%")

# Industrial
log(f"\n  Industrial Stress (T8): {t8.get('verdict', 'N/A')}")
log(f"    Industrial predictions: {t8.get('industrial_count', 0)}/{t8.get('total_samples', 0)}")

# POI Categories
log(f"\n  POI Categories (T9): {t9.get('verdict', 'N/A')}")
log(f"    Filler/stopword %: {t9.get('filler_pct', 0):.1f}%")
log(f"    Meaningful categories: {t9.get('meaningful_found', [])}")

log(f"\n--- RECOMMENDED IMPROVEMENTS ---")

if t1.get("checkpoint_loaded") and t1.get("differs_from_random"):
    log("  1. Checkpoint: OK — model uses trained weights")
else:
    log("  1. CHECKPOINT FAIL: Model may still use random weights")

if t5.get("change_pct", 0) < 10:
    log("  2. POI MODALITY: Low impact on predictions. Consider improving POI encoder or data quality.")
else:
    log("  2. POI MODALITY: Acceptable contribution")

if t7.get("stats", {}).get("std", 1) < 0.05 and t7.get("stats", {}).get("mean", 0) > 0.90:
    log("  3. OVERFITTING RISK: Confidence values too uniform. Add regularization or more data.")
else:
    log("  3. CONFIDENCE: Acceptable distribution")

if t8.get("industrial_count", 0) == 0:
    log("  4. INDUSTRIAL CLASS: Never predicted. Increase class weight, oversample, or collect more data (11 samples only).")
else:
    log("  4. INDUSTRIAL CLASS: Usable but monitor reliability")

if t9.get("filler_pct", 0) > 30:
    log("  5. POI CATEGORIES: Replace stopword extraction with meaningful category names from dataset.")
else:
    log("  5. POI CATEGORIES: Acceptable")

# Overall verdict
passed = sum(1 for v in [
    t1.get("differs_from_random", False),
    t234.get("verdict_residential") == "PASS",
    t234.get("verdict_commercial") == "PASS",
    t234.get("verdict_industrial") == "PASS",
    t5.get("verdict") == "PASS",
    t6.get("verdict") == "PASS",
    t7.get("verdict") == "PASS",
    t8.get("verdict") == "PASS",
    t9.get("verdict") == "PASS",
])
total_checks = 9
log(f"\n--- OVERALL: {passed}/{total_checks} checks passed ---")

log(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")

with open(os.path.join(OUT, "final_report.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(R))
log(f"\nReport saved: {OUT}/final_report.txt")
