"""
Post-Retrain Validation & Model Sanity Check.
"""
import os, sys, json, time, math
import numpy as np
import torch
import requests
from collections import Counter

os.environ["PYTHONIOENCODING"] = "utf-8"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.domain.mlp_model import UrbanMLP
from app.config import FUSION_DIM

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"
CHECKPOINT_PATH = "models/urban_mlp.pt"
CLASS_NAMES = {0: "Residential", 1: "Commercial", 2: "Industrial"}
RESULTS_DIR = "evals/validation"
os.makedirs(RESULTS_DIR, exist_ok=True)

report_lines = []
def log(msg):
    print(msg)
    report_lines.append(msg)

def save_json(data, name):
    path = os.path.join(RESULTS_DIR, name)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    log(f"  Saved: {path}")

def api_get(path):
    try:
        r = requests.get(f"{API_BASE}/{path}", timeout=30)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def api_post(path, payload, timeout=30):
    try:
        r = requests.post(f"{API_BASE}/{path}", json=payload, timeout=timeout)
        return r
    except Exception as e:
        log(f"  API POST error: {e}")
        return None

def wait_job(job_id, ep, timeout=180):
    for i in range(timeout):
        time.sleep(2)
        d = api_get(f"{ep}/{job_id}")
        if d:
            s = d.get("status")
            if s == "completed": return d
            if s == "failed": log(f"  Job failed: {d.get('error')}"); return d
    log("  TIMEOUT"); return None

def load_area(bbox, mods):
    r = api_post("load-area", {"bbox": bbox, "grid_size": 500, "modalities": mods})
    if not r or r.status_code != 202: return None
    jid = r.json()["job_id"]
    log(f"  load_area: {jid}")
    res = wait_job(jid, "area-status")
    return res.get("grid_id") if res and res["status"] == "completed" else None

def classify(grid_id, mods, fusion="concat"):
    r = api_post("classify", {"grid_id": grid_id, "modalities": mods, "fusion_method": fusion})
    if not r or r.status_code != 202: return None
    jid = r.json()["job_id"]
    log(f"  classify: {jid}")
    res = wait_job(jid, "classify-status")
    if res and res["status"] == "completed":
        r2 = api_get(f"classification-result/{jid}")
        if r2:
            if isinstance(r2, dict) and "features" in r2: return r2["features"]
            return r2 if isinstance(r2, list) else None
    return None


# ============================================================
# TEST 1 — Checkpoint Loading Verification
# ============================================================
def test1():
    log("\n" + "=" * 60)
    log("  TEST 1: CHECKPOINT LOADING VERIFICATION")
    log("=" * 60)
    if not os.path.exists(CHECKPOINT_PATH):
        log("  [FAIL] Checkpoint not found"); return {"checkpoint_exists": False}
    sz = os.path.getsize(CHECKPOINT_PATH) / 1024
    log(f"  Path: {os.path.abspath(CHECKPOINT_PATH)}")
    log(f"  Size: {sz:.1f} KB")

    ckpt = torch.load(CHECKPOINT_PATH, map_location="cpu", weights_only=True)
    log(f"  Keys: {list(ckpt.keys())}")

    model = UrbanMLP()
    total_p = sum(p.numel() for p in model.parameters())
    log(f"  Params: {total_p:,}")
    log(f"  Arch: input={FUSION_DIM}, hidden=256, output=3")

    try:
        model.load_state_dict(ckpt, strict=True)
        model.eval()
        log("  [PASS] Checkpoint loaded successfully")
        loaded = True
    except Exception as e:
        log(f"  [FAIL] {e}"); loaded = False

    # Compare vs random
    rand = UrbanMLP()
    dum = torch.randn(100, FUSION_DIM)
    with torch.no_grad():
        tp = model(dum).numpy(); rp = rand(dum).numpy()
    tm, rm = tp.mean(axis=0), rp.mean(axis=0)
    log(f"  Trained mean: {[f'{v:.4f}' for v in tm]}")
    log(f"  Random mean:  {[f'{v:.4f}' for v in rm]}")
    diff = bool(np.max(np.abs(tm - rm)) > 0.01)
    if diff: log("  [PASS] Output differs from random init")
    else: log("  [FAIL] Output same as random - checkpoint ineffective")

    res = {"checkpoint_path": os.path.abspath(CHECKPOINT_PATH), "size_kb": sz,
           "total_parameters": total_p, "checkpoint_loaded": loaded,
           "trained_mean": [float(v) for v in tm], "random_mean": [float(v) for v in rm],
           "differs_from_random": diff}
    save_json(res, "test1.json"); return res


# ============================================================
# TEST 2-4: Area Validations (single load_area + classify per area)
# ============================================================
def run_area(name, bbox, mods):
    log(f"\n{'='*60}")
    log(f"  AREA: {name.upper()} ({bbox})")
    log(f"{'='*60}")
    gid = load_area(bbox, mods)
    if not gid: log("  [SKIP] load failed"); return None
    res = classify(gid, mods)
    if not res: log("  [SKIP] classify failed"); return None
    log(f"  Cells: {len(res)}")
    cc = Counter(r["dominant_class"] for r in res)
    log(f"  Classes: {dict(cc)}")
    confs = [r["confidence"] for r in res]
    log(f"  Confidence: avg={np.mean(confs):.4f}, min={np.min(confs):.4f}, max={np.max(confs):.4f}")
    return {
        "name": name, "bbox": bbox, "grid_id": gid, "num_cells": len(res),
        "class_distribution": dict(cc), "avg_confidence": float(np.mean(confs)),
        "cells": [{"cid": r.get("cell_id"), "cls": r["dominant_class"],
                   "conf": r["confidence"], "norms": r.get("text_embedding_norm", 0),
                   "poi_top": r.get("poi_top_categories", []),
                   "confs": r.get("confidences", {})} for r in res]
    }


# ============================================================
# TEST 5 — POI Ablation (same grid, with and without POI)
# ============================================================
def test5():
    log("\n" + "=" * 60)
    log("  TEST 5: POI ABLATION TEST")
    log("=" * 60)
    bbox = [31.23, 30.04, 31.24, 30.06]
    gid = load_area(bbox, ["poi", "image", "graph"])
    if not gid: log("  [FAIL] load failed"); return None
    ra = classify(gid, ["poi", "image", "graph"])
    if not ra: log("  [FAIL] classify A failed"); return None
    log("  Run B: POI disabled")
    rb = classify(gid, ["image", "graph"])
    if not rb: log("  [FAIL] classify B failed"); return None

    ca = [r["dominant_class"] for r in ra]; cb = [r["dominant_class"] for r in rb]
    same = sum(1 for a,b in zip(ca,cb) if a==b); changed = len(ca)-same
    log(f"  Same: {same}/{len(ca)}, Changed: {changed}/{len(ca)} ({changed/len(ca)*100:.1f}%)")
    res = {"bbox": bbox, "grid_id": gid, "num_cells": len(ra),
           "poi_enabled": {"classes": dict(Counter(ca)), "avg_conf": float(np.mean([r["confidence"] for r in ra]))},
           "poi_disabled": {"classes": dict(Counter(cb)), "avg_conf": float(np.mean([r["confidence"] for r in rb]))},
           "changed": changed, "same": same, "change_pct": changed/len(ca)*100}
    if changed > 0: log("  [PASS] POI affects predictions"); res["verdict"]="PASS"
    else: log("  [FAIL] POI has no effect"); res["verdict"]="FAIL"
    save_json(res, "test5.json"); return res


# ============================================================
# TEST 6 — Embedding Verification
# ============================================================
def test6(results):
    log("\n" + "=" * 60)
    log("  TEST 6: EMBEDDING VERIFICATION")
    log("=" * 60)
    norms = [(r.get("text_embedding_norm", 0), bool(r.get("poi_top", []))) for r in results]
    wp = [n for n,h in norms if h]; wo = [n for n,h in norms if not h]
    log(f"  Cells w/ POI: {len(wp)}, w/o POI: {len(wo)}")
    if wp: log(f"  w/ POI norms: avg={np.mean(wp):.4f}, range=[{min(wp):.4f},{max(wp):.4f}]")
    if wo: log(f"  w/o POI norms: avg={np.mean(wo):.4f}, range=[{min(wo):.4f},{max(wo):.4f}]")
    ap = all(n > 0.001 for n in wp) if wp else True
    az = all(n < 0.001 for n in wo) if wo else True
    res = {"with_poi": {"count": len(wp), "min": float(min(wp)) if wp else 0, "max": float(max(wp)) if wp else 0, "avg": float(np.mean(wp)) if wp else 0},
           "without_poi": {"count": len(wo), "min": float(min(wo)) if wo else 0, "max": float(max(wo)) if wo else 0, "avg": float(np.mean(wo)) if wo else 0},
           "all_poi_positive": ap, "all_nopoi_zero": az}
    if ap: log("  [PASS] All w/ POI have norm > 0")
    else: log("  [FAIL] Some w/ POI have norm ~0")
    if az: log("  [PASS] All w/o POI have norm ~0")
    else: log("  [FAIL] Some w/o POI have norm > 0")
    save_json(res, "test6.json"); return res


# ============================================================
# TEST 7 — Confidence Distribution (aggregate all results)
# ============================================================
def test7(all_cells):
    log("\n" + "=" * 60)
    log("  TEST 7: CONFIDENCE DISTRIBUTION")
    log("=" * 60)
    confs = [c["conf"] for c in all_cells]
    s = {"min": float(np.min(confs)), "max": float(np.max(confs)),
         "mean": float(np.mean(confs)), "std": float(np.std(confs))}
    log(f"  Stats: {s}")
    bins = [(0,0.3),(0.3,0.4),(0.4,0.5),(0.5,0.6),(0.6,0.7),(0.7,0.8),(0.8,0.9),(0.9,0.95),(0.95,1.0)]
    hist = {f"{l:.2f}-{h:.2f}": sum(1 for c in confs if l <= c < h) for l,h in bins}
    log(f"  Histogram: {hist}")
    hc = sum(1 for c in confs if c >= 0.90)
    log(f"  >=90%: {hc}/{len(confs)} ({hc/len(confs)*100:.1f}%)")
    res = {"num_cells": len(confs), "stats": s, "histogram": hist,
           "high_90pct": hc, "high_90pct_pct": hc/len(confs)*100}
    if s["std"] < 0.05 and s["mean"] > 0.90: res["verdict"]="FAIL"; log("  [FAIL] Suspicious uniform confidence")
    elif s["std"] > 0.10: res["verdict"]="PASS"; log("  [PASS] Good spread")
    else: res["verdict"]="WARN"; log("  [WARN] Moderate spread")
    save_json(res, "test7.json"); return res


# ============================================================
# TEST 8 — Industrial Class Stress
# ============================================================
def test8(area_results):
    log("\n" + "=" * 60)
    log("  TEST 8: INDUSTRIAL CLASS STRESS")
    log("=" * 60)
    inds = [c for ar in area_results.values() if ar for c in ar.get("cells",[]) if c["cls"]=="Industrial"]
    log(f"  Total Industrial: {len(inds)}")
    if inds:
        ics = [c["conf"] for c in inds]
        log(f"  Confidence: avg={np.mean(ics):.4f}, range=[{min(ics):.4f},{max(ics):.4f}]")
        for c in inds:
            com = c["confs"].get("commercial", 0)
            if com > 0.3: log(f"    [WARN] Cell {c['cid']}: Industrial but Commercial prob={com:.4f}")
    else:
        log("  [FAIL] No Industrial predictions anywhere")
    res = {"total_industrial": len(inds),
           "confidence": {"min": float(np.min([c["conf"] for c in inds])) if inds else 0,
                          "max": float(np.max([c["conf"] for c in inds])) if inds else 0,
                          "avg": float(np.mean([c["conf"] for c in inds])) if inds else 0},
           "industrial_cells": inds}
    if len(inds) > 0: res["verdict"]="PASS"; log("  [PASS] Industrial class appears")
    else: res["verdict"]="FAIL"; log("  [FAIL] Industrial never appears")
    save_json(res, "test8.json"); return res


# ============================================================
# TEST 9 — Analytics Quality (POI top categories)
# ============================================================
def test9(all_cells):
    log("\n" + "=" * 60)
    log("  TEST 9: ANALYTICS QUALITY (POI TOP CATS)")
    log("=" * 60)
    words = []
    for c in all_cells:
        words.extend(c.get("poi_top", []))
    log(f"  Total entries: {len(words)}")
    wf = Counter(words).most_common(20)
    log("  Top 20:"); [log(f"    {w}: {c}") for w,c in wf]

    stops = {"في","من","على","إلى","عن","مع","كان","هذا","تقع","القاهرة","و","ال","ب","ل","حي","مدينة","شارع"}
    fillers = [w for w in words if w in stops]
    fp = len(fillers)/len(words)*100 if words else 0
    log(f"  Fillers/stopwords: {len(fillers)}/{len(words)} ({fp:.1f}%)")

    meaningful = {"bank","hospital","school","mall","office","restaurant","cafe","shop",
                  "mosque","pharmacy","clinic","supermarket","hotel","park","university","factory"}
    found = set(w.lower() for w in words if w.lower() in meaningful)
    log(f"  Meaningful: {found if found else 'NONE'}")

    res = {"total_entries": len(words), "top_20": [(w,c) for w,c in wf],
           "filler_count": len(fillers), "filler_pct": fp,
           "meaningful_found": list(found)}
    if fp > 50: res["verdict"]="FAIL"; log("  [FAIL] Too many filler words")
    elif len(found)==0: res["verdict"]="WARN"; log("  [WARN] No meaningful categories")
    else: res["verdict"]="PASS"; log("  [PASS] Meaningful categories present")
    save_json(res, "test9.json"); return res


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    log("=" * 60)
    log("  POST-RETRAIN VALIDATION")
    log("=" * 60)
    log(f"  Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        log(f"  Server: {r.json()}")
    except Exception as e:
        log(f"  Server unreachable: {e}"); sys.exit(1)

    all_r = {}

    # Test 1: Direct checkpoint test
    all_r["test1"] = test1()

    # Areas to validate (minimal modality for speed)
    mods_poi = ["poi"]
    test_areas = {
        "residential": [31.32, 30.04, 31.35, 30.07],   # Nasr City
        "commercial":  [31.23, 30.04, 31.24, 30.05],    # Downtown Cairo
        "industrial":  [31.15, 30.10, 31.17, 30.12],    # Industrial zone
    }

    area_results = {}
    for name, bbox in test_areas.items():
        r = run_area(name, bbox, mods_poi)
        area_results[name] = r

    # Collect all cells for aggregate analysis
    all_cells = []
    for ar in area_results.values():
        if ar: all_cells.extend(ar.get("cells", []))

    log(f"\nTotal cells across all areas: {len(all_cells)}")

    # Tests 2-4: Area verdicts
    for name, r in area_results.items():
        if r is None:
            log(f"\n  {name.upper()}: SKIPPED"); continue
        dist = r["class_distribution"]
        maj_cls = max(dist, key=dist.get) if dist else "none"
        maj_pct = dist.get(maj_cls, 0)/r["num_cells"]*100
        log(f"\n  {name.upper()}: majority={maj_cls} ({maj_pct:.1f}%)")

    if area_results.get("residential"):
        dist = area_results["residential"]["class_distribution"]
        rp = dist.get("Residential", 0)/area_results["residential"]["num_cells"]*100
        if rp >= 40: all_r["test2"] = {"verdict":"PASS","pct":rp,"data":area_results["residential"]}
        else: all_r["test2"] = {"verdict":"FAIL","pct":rp,"data":area_results["residential"]}
        log(f"  -> T2 verdict: {all_r['test2']['verdict']}")

    if area_results.get("commercial"):
        dist = area_results["commercial"]["class_distribution"]
        cp = dist.get("Commercial", 0)/area_results["commercial"]["num_cells"]*100
        if cp >= 40: all_r["test3"] = {"verdict":"PASS","pct":cp,"data":area_results["commercial"]}
        else: all_r["test3"] = {"verdict":"FAIL","pct":cp,"data":area_results["commercial"]}
        log(f"  -> T3 verdict: {all_r['test3']['verdict']}")

    if area_results.get("industrial"):
        dist = area_results["industrial"]["class_distribution"]
        ip = dist.get("Industrial", 0)
        if ip > 0: all_r["test4"] = {"verdict":"PASS","count":ip,"data":area_results["industrial"]}
        else: all_r["test4"] = {"verdict":"FAIL","count":0,"data":area_results["industrial"]}
        log(f"  -> T4 verdict: {all_r['test4']['verdict']} (Industrial: {ip})")

    # Tests 5-9
    if len(all_cells) > 0:
        all_r["test5"] = test5()
        if "residential" in area_results and area_results["residential"]:
            all_r["test6"] = test6(area_results["residential"]["cells"])
        all_r["test7"] = test7(all_cells)
        all_r["test8"] = test8(area_results)
        all_r["test9"] = test9(all_cells)

    # FINAL REPORT
    log("\n" + "=" * 60)
    log("  FINAL REPORT")
    log("=" * 60)
    log(f"\n  MODEL:")
    if all_r.get("test1"):
        log(f"    Checkpoint: {all_r['test1'].get('checkpoint_path','N/A')}")
        log(f"    Parameters: {all_r['test1'].get('total_parameters','N/A'):,}")
        log(f"    Loaded: {all_r['test1'].get('checkpoint_loaded','N/A')}")

    log(f"\n  DATASET:")
    try:
        import pandas as pd
        df = pd.read_csv("data/raw/project.csv")
        lc = df["label"].value_counts().sort_index()
        for l in sorted(lc.index): log(f"    {CLASS_NAMES.get(l,f'cls{l}')}: {lc[l]}")
    except: log("    Could not load dataset")

    log(f"\n  VALIDATION AREAS:")
    for t in ["test2","test3","test4"]:
        d = all_r.get(t)
        if d and d.get("data"):
            na = d["data"]["name"]; v = d.get("verdict","?")
            dd = d["data"]["class_distribution"]
            log(f"    {na.upper()}: {v}  dist={dd}")

    log(f"\n  CONFIDENCE:")
    if all_r.get("test7"):
        s = all_r["test7"].get("stats",{})
        log(f"    Mean={s.get('mean',0):.4f} Std={s.get('std',0):.4f}")
        log(f"    >=90%: {all_r['test7'].get('high_90pct_pct',0):.1f}%")
        log(f"    Verdict: {all_r['test7'].get('verdict','?')}")

    log(f"\n  POI CONTRIBUTION:")
    if all_r.get("test5"):
        log(f"    Changed: {all_r['test5'].get('change_pct',0):.1f}%")
        log(f"    Verdict: {all_r['test5'].get('verdict','?')}")

    log(f"\n  INDUSTRIAL RELIABILITY:")
    if all_r.get("test8"):
        log(f"    Total: {all_r['test8'].get('total_industrial',0)}")
        log(f"    Verdict: {all_r['test8'].get('verdict','?')}")

    log(f"\n  POI CATEGORIES:")
    if all_r.get("test9"):
        log(f"    Filler: {all_r['test9'].get('filler_pct',0):.1f}%")
        log(f"    Meaningful: {all_r['test9'].get('meaningful_found',[])}")
        log(f"    Verdict: {all_r['test9'].get('verdict','?')}")

    passed = sum(1 for r in all_r.values() if isinstance(r,dict) and r.get("verdict")=="PASS")
    failed = sum(1 for r in all_r.values() if isinstance(r,dict) and r.get("verdict")=="FAIL")
    log(f"\n  OVERALL: {passed} passed, {failed} failed")
    if failed == 0: log("  STATUS: ALL CHECKS PASSED")
    else: log(f"  STATUS: {failed} CHECK(S) FAILED")

    log(f"\n  Finished: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    with open(os.path.join(RESULTS_DIR,"final_report.txt"),"w",encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    log(f"\n  Report: {RESULTS_DIR}/final_report.txt")
