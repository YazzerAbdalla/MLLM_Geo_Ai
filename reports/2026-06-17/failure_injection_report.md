# Failure Injection Report | Date: 2026-06-17 | MLLM-Geo-AI Project

## 1. Load Area Negative Tests

| Test | Input | Expected | Actual | Status |
|------|-------|----------|--------|--------|
| Invalid bbox | bbox=[] | 400 | Not tested | UNVERIFIABLE |
| Invalid grid size | grid_size=-1 | 400 | Not tested | UNVERIFIABLE |
| Empty modalities | modalities=[] | 202 (works) | 202 Accepted | ✅ WORKING |
| Huge area | bbox covering all of Egypt | 413 Too Large | Not tested | UNVERIFIABLE |

## 2. Classification Negative Tests

| Test | Input | Expected | Actual | Status |
|------|-------|----------|--------|--------|
| Invalid grid_id | grid_id="nonexistent" | 404 | 404 Not Found | ✅ WORKING |
| Missing grid | grid_id="" | 400/404 | Not tested | UNVERIFIABLE |
| Empty modalities | modalities=[] | 400 | 400 Bad Request | ✅ WORKING |

## 3. Export Negative Tests

| Test | Input | Expected | Actual | Status |
|------|-------|----------|--------|--------|
| Invalid format | format="pdf" | 400 | 400 (from code) | ⚠️ CODE VERIFIED |
| Missing job | nonexistent job_id | 404 | 404 Not Found | ✅ WORKING |

## 4. Training Negative Tests (mllm/train)

| Test | Input | Expected | Actual | Status |
|------|-------|----------|--------|--------|
| Missing dataset | dataset_path="nonexistent.csv" | 400 | 400 Not Found | ✅ WORKING |
| Invalid extension | dataset_path="file.txt" | 400 | 400 (from code) | ⚠️ CODE VERIFIED |
| Invalid epochs | epochs=0 | 400 | 400 (from code) | ⚠️ CODE VERIFIED |
| Invalid batch_size | batch_size=0 | 400 | 400 (from code) | ⚠️ CODE VERIFIED |

## 5. Evaluation Negative Tests

| Test | Input | Expected | Actual | Status |
|------|-------|----------|--------|--------|
| Missing ground truth | No file | 400 | 400 (from code) | ⚠️ CODE VERIFIED |
| Invalid job | unknown_job | 404 | 404 (from code) | ⚠️ CODE VERIFIED |

## 6. Jobs Negative Tests

| Test | Input | Expected | Actual | Status |
|------|-------|----------|--------|--------|
| Delete missing job | nonexistent | 404 | 404 Not Found | ✅ WORKING |
| Delete completed job | completed job | 200 | Not tested | UNVERIFIABLE |

## 7. Evidence Matrix

| Item | Code Verified | Runtime Verified | Evidence Attached |
|------|:-------------:|:----------------:|:-----------------:|
| Load Area - Empty modalities | YES | YES | YES |
| Classify - Invalid grid | YES | YES | YES |
| Classify - Empty modalities | YES | YES | YES |
| Export - Missing job | YES | YES | YES |
| Training - Missing dataset | YES | YES | YES |
| Delete - Missing job | YES | YES | YES |
| Other failures | YES | NO | NO |
