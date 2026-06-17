import requests
import time
import json
import os
import sys

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

os.makedirs("audit/api_responses", exist_ok=True)
os.makedirs("audit/performance", exist_ok=True)
os.makedirs("audit/security", exist_ok=True)

report = []
def log(msg):
    print(msg)
    report.append(msg)

def test_endpoint(method, url, **kwargs):
    start = time.time()
    try:
        if method == "GET":
            resp = requests.get(url, **kwargs)
        elif method == "POST":
            resp = requests.post(url, **kwargs)
        elif method == "DELETE":
            resp = requests.delete(url, **kwargs)
        duration = time.time() - start
        
        path_name = url.replace(BASE_URL, "").replace("/", "_").replace("?", "_")
        if path_name.startswith("_"):
            path_name = path_name[1:]
            
        with open(f"audit/api_responses/{method}_{path_name[:50]}.json", "w") as f:
            try:
                json.dump({"status": resp.status_code, "body": resp.json(), "duration": duration}, f, indent=2)
            except:
                f.write(f"Status: {resp.status_code}\nDuration: {duration}\nBody: {resp.text}")
                
        return resp, duration
    except Exception as e:
        log(f"FAILED {method} {url}: {e}")
        return None, 0

log("Starting API Audit...")

# 1. Health
resp, duration = test_endpoint("GET", f"{BASE_URL}/health")
log(f"GET /health: {resp.status_code if resp else 'Error'} in {duration:.3f}s")

# 2. Load Area (Scenario A)
load_payload = {
    "bbox": [31.20, 30.00, 31.22, 30.02],
    "grid_size": 500,
    "modalities": []
}
resp, duration = test_endpoint("POST", f"{API_BASE}/load-area", json=load_payload)
log(f"POST /load-area: {resp.status_code if resp else 'Error'}")

job_id = None
if resp and resp.status_code == 202:
    job_id = resp.json().get("job_id")
    log(f"Got Job ID: {job_id}")

    # Wait for completion
    grid_id = None
    for i in range(30):
        time.sleep(2)
        r, _ = test_endpoint("GET", f"{API_BASE}/area-status/{job_id}")
        if r and r.status_code == 200:
            data = r.json()
            if data["status"] == "completed":
                grid_id = data.get("grid_id")
                log(f"Load Area Completed. Grid ID: {grid_id}")
                break
            elif data["status"] == "failed":
                log(f"Load Area Failed: {data.get('error')}")
                break
            log(f"Load Area Pending... {data.get('progress')}%")
        
    if grid_id:
        log(f"Testing Grid details for Grid ID: {grid_id}")
        # Test Grid Details
        test_endpoint("GET", f"{API_BASE}/grid/{grid_id}/details")
        # Test Grid POIs
        test_endpoint("GET", f"{API_BASE}/grid/{grid_id}/pois")
        # Test Graph Topology
        test_endpoint("GET", f"{API_BASE}/grid/{grid_id}/graph-topology?max_nodes=500&simplify=true")

        # Scenario B - Classify
        classify_payload = {
            "grid_id": grid_id,
            "modalities": [],
            "fusion_method": "concat"
        }
        r_cls, _ = test_endpoint("POST", f"{API_BASE}/classify", json=classify_payload)
        if r_cls and r_cls.status_code == 202:
            cls_job_id = r_cls.json().get("job_id")
            log(f"Started classification job: {cls_job_id}")
            for i in range(30):
                time.sleep(2)
                r, _ = test_endpoint("GET", f"{API_BASE}/classify-status/{cls_job_id}")
                if r and r.status_code == 200:
                    data = r.json()
                    if data["status"] == "completed":
                        log("Classification Completed")
                        # Get result
                        test_endpoint("GET", f"{API_BASE}/classification-result/{cls_job_id}")
                        # Export
                        test_endpoint("GET", f"{API_BASE}/export/{cls_job_id}?format=geojson")
                        break
                    elif data["status"] == "failed":
                        log(f"Classification Failed: {data.get('error')}")
                        break
                    log(f"Classify Pending... {data.get('progress')}%")
                        
        # Scenario E - Cancel job
        r_cancel, _ = test_endpoint("POST", f"{API_BASE}/classify", json=classify_payload)
        if r_cancel and r_cancel.status_code == 202:
            cancel_job_id = r_cancel.json().get("job_id")
            time.sleep(1)
            test_endpoint("DELETE", f"{API_BASE}/jobs/{cancel_job_id}")
            r_c_status, _ = test_endpoint("GET", f"{API_BASE}/classify-status/{cancel_job_id}")
            if r_c_status:
                log(f"Cancelled job status: {r_c_status.json().get('status')}")

# Test Negative
test_endpoint("POST", f"{API_BASE}/load-area", json={"bbox": "invalid"})
test_endpoint("GET", f"{API_BASE}/jobs/invalid_job_id")

with open("audit/audit_log.txt", "w") as f:
    f.write("\n".join(report))
log("Audit script completed.")
