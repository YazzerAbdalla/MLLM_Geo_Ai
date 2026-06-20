"""Quick API pipeline test"""
import requests, time, sys

BASE = "http://localhost:8000/api/v1"

r = requests.post(f"{BASE}/load-area", json={
    "bbox": [31.20, 30.00, 31.22, 30.02],
    "grid_size": 500,
    "modalities": ["poi"]
}, timeout=10)
print(f"Load area: {r.status_code}")
if r.status_code != 202:
    print(f"  Failed: {r.text}")
    sys.exit(1)
jid = r.json()["job_id"]
print(f"  Job: {jid}")

for i in range(120):
    time.sleep(2)
    r2 = requests.get(f"{BASE}/area-status/{jid}", timeout=10)
    d = r2.json()
    print(f"  [{i}] {d['status']} step={d.get('step')} progress={d.get('progress')}")
    if d["status"] == "completed":
        grid_id = d.get("grid_id")
        print(f"  Grid ID: {grid_id}")
        r3 = requests.post(f"{BASE}/classify", json={
            "grid_id": grid_id, "modalities": ["poi"], "fusion_method": "concat"
        }, timeout=10)
        print(f"  Classify: {r3.status_code}")
        if r3.status_code == 202:
            cjid = r3.json()["job_id"]
            for j in range(120):
                time.sleep(2)
                r4 = requests.get(f"{BASE}/classify-status/{cjid}", timeout=10)
                cd = r4.json()
                print(f"    [{j}] {cd['status']} step={cd.get('step')}")
                if cd["status"] == "completed":
                    r5 = requests.get(f"{BASE}/classification-result/{cjid}", timeout=10)
                    res = r5.json()
                    if isinstance(res, dict) and "features" in res:
                        feats = res["features"]
                    elif isinstance(res, list):
                        feats = res
                    else:
                        feats = []
                    print(f"    Cells classified: {len(feats)}")
                    if feats:
                        for f in feats[:5]:
                            print(f"      {f.get('cell_id')}: {f['dominant_class']} ({f['confidence']:.4f})")
                    sys.exit(0)
                elif cd["status"] == "failed":
                    print(f"    FAILED: {cd.get('error')}")
                    sys.exit(1)
        break
    elif d["status"] == "failed":
        print(f"  FAILED: {d.get('error')}")
        sys.exit(1)
print("TIMEOUT")
