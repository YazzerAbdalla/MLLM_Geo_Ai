"""Run all 10 validation tests efficiently"""
import os, sys, json, time
import numpy as np
import torch
import requests
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.domain.mlp_model import UrbanMLP
from app.config import FUSION_DIM

os.makedirs("evals/validation", exist_ok=True)
CKPT = "models/urban_mlp.pt"
BASE = "http://localhost:8000/api/v1"
CNAMES = {0: "Residential", 1: "Commercial", 2: "Industrial"}
R = []
def log(m): print(m); R.append(m)
def save(d, fn):
    with open(f"evals/validation/{fn}", "w") as f: json.dump(d, f, indent=2, default=str)

def load_area(bbox, mods):
    r = requests.post(f"{BASE}/load-area", json={"bbox": bbox, "grid_size": 500, "modalities": mods}, timeout=30)
    if r.status_code != 202: return None
    jid = r.json()["job_id"]
    for i in range(180):
        time.sleep(2)
        d = requests.get(f"{BASE}/area-status/{jid}", timeout=10).json()
        if d["status"] == "completed": return d.get("grid_id")
        if d["status"] == "failed": log(f"  LOAD FAIL: {d.get('error')}"); return None
    return None

def classify(gid, mods):
    r = requests.post(f"{BASE}/classify", json={"grid_id": gid, "modalities": mods, "fusion_method": "concat"}, timeout=30)
    if r.status_code != 202: return None
    jid = r.json()["job_id"]
    for i in range(180):
        time.sleep(2)
        d = requests.get(f"{BASE}/classify-status/{jid}", timeout=10).json()
        if d["status"] == "completed":
            r3 = requests.get(f"{BASE}/classification-result/{jid}", timeout=10).json()
            if isinstance(r3, dict) and "features" in r3: return r3["features"]
            if isinstance(r3, list): return r3
            return None
        if d["status"] == "failed": log(f"  CLASSIFY FAIL: {d.get('error')}"); return None
    return None

# ===== TEST 1: Checkpoint Loading =====
log("="*60)
log("TEST 1: CHECKPOINT LOADING")
log("="*60)
t1 = {"checkpoint_loaded": False, "differs_from_random": False,
      "trained_mean": [], "random_mean": [], "total_parameters": 0}
if os.path.exists(CKPT):
    sz = os.path.getsize(CKPT) / 1024
    ckpt = torch.load(CKPT, map_location="cpu", weights_only=True)
    model = UrbanMLP()
    t1["total_parameters"] = sum(p.numel() for p in model.parameters())
    log(f"  Path: {os.path.abspath(CKPT)}")
    log(f"  Size: {sz:.1f} KB, Params: {t1['total_parameters']:,}")
    try:
        model.load_state_dict(ckpt, strict=True)
        model.eval()
        t1["checkpoint_loaded"] = True
        log("  [PASS] Checkpoint loaded")
    except Exception as e:
        log(f"  [FAIL] {e}")
    rand = UrbanMLP()
    dum = torch.randn(100, FUSION_DIM)
    with torch.no_grad():
        tp, rp = model(dum).numpy(), rand(dum).numpy()
    t1["trained_mean"] = [float(v) for v in tp.mean(0)]
    t1["random_mean"] = [float(v) for v in rp.mean(0)]
    t1["differs_from_random"] = bool(np.max(np.abs(tp.mean(0) - rp.mean(0))) > 0.01)
    log(f"  Trained mean: {[f'{v:.4f}' for v in t1['trained_mean']]}")
    log(f"  Random mean:  {[f'{v:.4f}' for v in t1['random_mean']]}")
    log(f"  Differs from random: {t1['differs_from_random']}")
else:
    log("  [FAIL] Checkpoint not found")
save(t1, "test1.json")

# ===== TESTS 2-4: Area Validations =====
areas = [
    ("residential", [31.32, 30.04, 31.35, 30.07], ["poi"], "Residential"),
    ("commercial",  [31.23, 30.04, 31.24, 30.05], ["poi"], "Commercial"),
    ("industrial",  [31.15, 30.10, 31.17, 30.12], ["poi"], "Industrial"),
]
all_cells = []
area_results = {}
for name, bbox, mods, expected in areas:
    log(f"\n{'='*60}")
    log(f"AREA: {name.upper()} (expected={expected}) bbox={bbox}")
    log(f"{'='*60}")
    gid = load_area(bbox, mods)
    if not gid: log("  SKIP - load_area failed"); continue
    res = classify(gid, mods)
    if not res: log("  SKIP - classify failed"); continue
    log(f"  Cells: {len(res)}")
    cc = Counter(r["dominant_class"] for r in res)
    log(f"  Classes: {dict(cc)}")
    confs = [r["confidence"] for r in res]
    log(f"  Confidence: avg={np.mean(confs):.4f} min={np.min(confs):.4f} max={np.max(confs):.4f}")
    cells = [{"cell_id": r.get("cell_id"), "cls": r["dominant_class"], "conf": r["confidence"],
              "norms": r.get("text_embedding_norm", 0), "confidences": r.get("confidences", {}),
              "poi_top": r.get("poi_top_categories", [])} for r in res]
    all_cells.extend(cells)
    expected_pct = cc.get(expected, 0) / len(res) * 100
    verdict = "PASS" if (expected_pct >= 30 if expected != "Industrial" else cc.get("Industrial", 0) > 0) else "FAIL"
    log(f"  {expected}: {expected_pct:.1f}% (Industrial count: {cc.get('Industrial', 0)}) -> {verdict}")
    ar = {"name": name, "expected": expected, "num_cells": len(res), "class_distribution": dict(cc),
          "expected_pct": expected_pct, "industrial_count": cc.get("Industrial", 0),
          "avg_confidence": float(np.mean(confs)), "cells": cells, "verdict": verdict}
    area_results[name] = ar
    save(ar, f"test_{name}.json")

# ===== TEST 5: POI Ablation =====
log(f"\n{'='*60}")
log("TEST 5: POI ABLATION")
log(f"{'='*60}")
t5 = {"verdict": "FAIL", "change_pct": 0, "same": 0, "changed": 0}
bbox5 = [31.23, 30.04, 31.24, 30.06]
gid5 = load_area(bbox5, ["poi", "image", "graph"])
if gid5:
    rA = classify(gid5, ["poi", "image", "graph"])
    if rA:
        rB = classify(gid5, ["image", "graph"])
        if rB:
            cA = [c["dominant_class"] for c in rA]
            cB = [c["dominant_class"] for c in rB]
            same = sum(1 for a,b in zip(cA,cB) if a==b)
            changed = len(cA) - same
            t5["same"] = same; t5["changed"] = changed
            t5["change_pct"] = changed / len(cA) * 100 if len(cA) > 0 else 0
            t5["poi_enabled"] = dict(Counter(cA))
            t5["poi_disabled"] = dict(Counter(cB))
            t5["verdict"] = "PASS" if changed > 0 else "FAIL"
            log(f"  Same: {same}, Changed: {changed} ({t5['change_pct']:.1f}%) -> {t5['verdict']}")
save(t5, "test5.json")

# ===== TEST 6: Embedding Verification =====
log(f"\n{'='*60}")
log("TEST 6: EMBEDDING VERIFICATION")
log(f"{'='*60}")
t6 = {"verdict": "FAIL", "with_poi": 0, "without_poi": 0}
if "residential" in area_results:
    cells = area_results["residential"]["cells"]
    wp = [c for c in cells if c["poi_top"]]; wo = [c for c in cells if not c["poi_top"]]
    t6["with_poi"] = len(wp); t6["without_poi"] = len(wo)
    t6["w_poi_avg_norm"] = float(np.mean([c["norms"] for c in wp])) if wp else 0
    t6["wo_poi_avg_norm"] = float(np.mean([c["norms"] for c in wo])) if wo else 0
    ap = all(c["norms"] > 0.001 for c in wp) if wp else True
    az = all(c["norms"] < 0.001 for c in wo) if wo else True
    t6["all_poi_positive"] = ap; t6["all_nopoi_zero"] = az
    t6["verdict"] = "PASS" if ap and az else "FAIL"
    log(f"  w/ POI: {len(wp)}, w/o POI: {len(wo)}")
    log(f"  w/ POI avg norm: {t6['w_poi_avg_norm']:.4f}")
    log(f"  w/o POI avg norm: {t6['wo_poi_avg_norm']:.4f}")
    log(f"  All POI>0: {ap}, All no-POI~0: {az} -> {t6['verdict']}")
save(t6, "test6.json")

# ===== TEST 7: Confidence Distribution =====
log(f"\n{'='*60}")
log("TEST 7: CONFIDENCE DISTRIBUTION")
log(f"{'='*60}")
t7 = {"verdict": "WARN"}
if all_cells:
    confs = [c["conf"] for c in all_cells]
    stats = {"min": float(np.min(confs)), "max": float(np.max(confs)),
             "mean": float(np.mean(confs)), "std": float(np.std(confs))}
    bins = [(0,0.3),(0.3,0.4),(0.4,0.5),(0.5,0.6),(0.6,0.7),(0.7,0.8),(0.8,0.9),(0.9,0.95),(0.95,1.01)]
    hist = {f"{l:.2f}-{h:.2f}": sum(1 for c in confs if l <= c < h) for l,h in bins}
    hc90 = sum(1 for c in confs if c >= 0.90)
    t7["num_cells"] = len(confs); t7["stats"] = stats; t7["histogram"] = hist
    t7["high_90pct"] = hc90; t7["high_90pct_pct"] = hc90/len(confs)*100
    if stats["std"] < 0.05 and stats["mean"] > 0.90:
        t7["verdict"] = "FAIL"
        log("  [FAIL] Suspicious: near-uniform high confidence")
    elif stats["std"] > 0.10:
        t7["verdict"] = "PASS"
        log("  [PASS] Good confidence spread")
    else:
        log("  [WARN] Moderate confidence spread")
    log(f"  Stats: {stats}")
    log(f"  Histogram: {hist}")
    log(f"  >=90%: {hc90}/{len(confs)} ({t7['high_90pct_pct']:.1f}%)")
save(t7, "test7.json")

# ===== TEST 8: Industrial Stress =====
log(f"\n{'='*60}")
log("TEST 8: INDUSTRIAL STRESS")
log(f"{'='*60}")
inds = [c for ar in area_results.values() for c in ar["cells"] if c["cls"]=="Industrial"]
t8 = {"total_industrial": len(inds), "avg_conf": 0, "cells": [], "verdict": "FAIL"}
if inds:
    t8["cells"] = inds
    ics = [c["conf"] for c in inds]
    t8["avg_conf"] = float(np.mean(ics))
    t8["min_conf"] = float(np.min(ics))
    t8["max_conf"] = float(np.max(ics))
    t8["verdict"] = "PASS"
    log(f"  Total: {len(inds)}")
    log(f"  Confidence: avg={t8['avg_conf']:.4f} range=[{t8['min_conf']:.4f},{t8['max_conf']:.4f}]")
    log(f"  -> {t8['verdict']}")
else:
    log("  No Industrial predictions found -> FAIL")
save(t8, "test8.json")

# ===== TEST 9: Analytics Quality =====
log(f"\n{'='*60}")
log("TEST 9: POI CATEGORY QUALITY")
log(f"{'='*60}")
words = [w for c in all_cells for w in c.get("poi_top", [])]
t9 = {"total_entries": len(words), "top_20": [], "filler_pct": 0, "meaningful": [], "verdict": "WARN"}
if words:
    wf = Counter(words).most_common(20)
    t9["top_20"] = [(w, c) for w, c in wf]
    log("  Top 20:")
    for w, c in wf: log(f"    {w}: {c}")
    stops = {"في","من","على","إلى","عن","مع","كان","هذا","تقع","القاهرة","و","ال","ب","ل","حي","مدينة","شارع","منطقة","مدن","بها"}
    fillers = [w for w in words if w in stops]
    fp = len(fillers)/len(words)*100
    t9["filler_pct"] = fp
    t9["filler_count"] = len(fillers)
    meaningful = {"bank","hospital","school","mall","office","restaurant","cafe","shop",
                  "mosque","pharmacy","clinic","supermarket","hotel","park","university","factory"}
    found = list(set(w.lower() for w in words if w.lower() in meaningful))
    t9["meaningful"] = found
    log(f"  Fillers: {len(fillers)}/{len(words)} ({fp:.1f}%)")
    log(f"  Meaningful: {found if found else 'NONE'}")
    if fp > 50: t9["verdict"] = "FAIL"; log("  -> FAIL (too many fillers)")
    elif len(found) > 0: t9["verdict"] = "PASS"; log("  -> PASS")
    else: log("  -> WARN")
save(t9, "test9.json")

# ===== TEST 10: Final Report =====
log(f"\n{'='*60}")
log("FINAL REPORT (TEST 10)")
log(f"{'='*60}")
log(f"\n  MODEL:")
log(f"    Checkpoint: {os.path.abspath(CKPT)}")
log(f"    Params: {t1.get('total_parameters', 0):,}")
log(f"    Loaded: {t1.get('checkpoint_loaded', False)}")
log(f"    Differs from random: {t1.get('differs_from_random', False)}")

log(f"\n  DATASET:")
try:
    import pandas as pd
    df = pd.read_csv("data/raw/project.csv")
    lc = df["label"].value_counts().sort_index()
    log(f"    Total samples: {len(df)}")
    for l in sorted(lc.index): log(f"      {CNAMES.get(l, f'cls{l}')}: {lc[l]}")
except Exception as e: log(f"    Error: {e}")

log(f"\n  VALIDATION AREAS:")
for name, ar in area_results.items():
    log(f"    {name.upper()}: {ar['class_distribution']} -> {ar['verdict']}")

log(f"\n  CONFIDENCE:")
if t7.get("stats"):
    s = t7["stats"]
    log(f"    Mean={s['mean']:.4f} Std={s['std']:.4f} Min={s['min']:.4f} Max={s['max']:.4f}")
    log(f"    >=90%: {t7.get('high_90pct_pct', 0):.1f}% -> {t7['verdict']}")

log(f"\n  POI CONTRIBUTION:")
log(f"    Predictions changed without POI: {t5.get('change_pct', 0):.1f}% -> {t5['verdict']}")

log(f"\n  INDUSTRIAL:")
log(f"    Total predictions: {t8['total_industrial']} -> {t8['verdict']}")
if t8["total_industrial"] > 0:
    log(f"    Avg confidence: {t8['avg_conf']:.4f}")

log(f"\n  POI CATEGORIES:")
log(f"    Fillers: {t9.get('filler_pct', 0):.1f}%")
log(f"    Meaningful: {t9.get('meaningful', [])} -> {t9['verdict']}")

# Overall
test_keys = {"T1 Checkpoint": t1.get("differs_from_random", False),
             "T2 Residential": area_results.get("residential", {}).get("verdict") == "PASS" if "residential" in area_results else False,
             "T3 Commercial": area_results.get("commercial", {}).get("verdict") == "PASS" if "commercial" in area_results else False,
             "T4 Industrial": area_results.get("industrial", {}).get("verdict") == "PASS" if "industrial" in area_results else False,
             "T5 POI Ablation": t5.get("verdict") == "PASS",
             "T6 Embeddings": t6.get("verdict") == "PASS",
             "T7 Confidence": t7.get("verdict") == "PASS",
             "T8 Industrial Stress": t8.get("verdict") == "PASS",
             "T9 POI Quality": t9.get("verdict") == "PASS"}
passed = sum(1 for v in test_keys.values() if v)
failed = sum(1 for v in test_keys.values() if not v)
log(f"\n  OVERALL: {passed} passed, {failed} failed")
for tn, r in test_keys.items(): log(f"    {tn}: {'PASS' if r else 'FAIL'}")
log(f"\n  Finished: {time.strftime('%Y-%m-%d %H:%M:%S')}")

with open("evals/validation/final_report.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(R))
log(f"\n  Full report: evals/validation/final_report.txt")
