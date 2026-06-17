````markdown
# 🚨 CRITICAL REMEDIATION SPRINT PROMPT
## MLLM-Geo-AI Backend – Validation, Evaluation, Data Integrity & Defense Readiness Fixes

You are a Senior Backend Engineer, QA Engineer, DevOps Engineer, and Software Auditor working on the MLLM-Geo-AI project.

Your mission is to investigate, fix, validate, and document ALL remaining backend defects discovered during the latest E2E audit.

DO NOT stop after implementing fixes.

You must:

1. Investigate root cause.
2. Implement fixes.
3. Create regression tests.
4. Execute tests.
5. Re-run failure injection tests.
6. Produce a detailed remediation report.

No assumptions.
Verify everything from code.

---

# PHASE 1 — ROOT CAUSE ANALYSIS

Before changing code:

Create:

audit/REMAINING_ISSUES_ROOT_CAUSE.md

For each issue:

- Identify affected files
- Root cause
- Impact
- Current behavior
- Expected behavior
- Proposed fix

---

# PHASE 2 — FIX ALL REMAINING DEFECTS

---

## DEF-007 — Large Area Validation Not Triggering

### Current Behavior

Large bbox requests timeout instead of returning:

HTTP 413

### Expected

Reject immediately before any expensive processing begins.

### Requirements

Investigate:

- load-area endpoint
- grid generation flow
- bbox validation
- cell count calculation

Verify:

Maximum allowed cells = 500

Before:

- graph loading
- OSM processing
- satellite downloads
- Celery task creation

Calculate:

cell_count

If > limit:

Return:

HTTP 413

```json
{
  "detail": "Area exceeds maximum allowed cell count"
}
````

Add tests.

---

## DEF-008 — Invalid Grid ID Accepted

### Current Behavior

```json
{
  "grid_id":"fake_grid"
}
```

returns:

```http
202 Accepted
```

and fails later in Celery.

### Expected

Validate before queueing.

Return:

```http
404
```

or

```http
400
```

with explicit message.

### Requirements

Investigate:

* classify endpoint
* grid repository
* grid storage

Before creating job:

Verify grid exists.

If not:

Reject request immediately.

Add tests.

---

## DEF-009 — Empty Modalities Validation Missing

### Current Behavior

```json
{
  "modalities":[]
}
```

still accepted.

### Expected

Reject.

```http
400
```

```json
{
  "detail":"At least one modality required"
}
```

### Requirements

Check:

* request schema
* Pydantic models
* endpoint validation
* task validation

Ensure validation exists in:

API layer
AND
service layer

Add tests.

---

## DEF-010 — DELETE Job Endpoint Inconsistent

### Current Behavior

Some test runs return:

```http
405 Method Not Allowed
```

### Requirements

Verify:

```python
DELETE /api/v1/jobs/{job_id}
```

exists.

Investigate:

* router registration
* FastAPI include_router
* path conflicts
* deployment mismatch

Expected:

Delete endpoint always available.

Return:

404 for missing job.

200 for deleted job.

Add tests.

---

## DEF-011 — MLLM Training Validation Not Active

### Current Behavior

Invalid datasets:

```text
nonexistent.csv
```

or

```text
dataset.graphml
```

still create Celery jobs.

### Expected

Reject before queueing.

### Requirements

Validate:

* path exists
* supported extensions
* readable file
* epochs range
* batch size range

Allowed:

.csv
.json
.geojson

Reject everything else.

Return:

HTTP 400

with clear error.

Add tests.

---

## DEF-012 — Evaluation Endpoint Broken

### Current Behavior

Evaluation fails with:

```json
{
  "detail":"Could not detect prediction label column"
}
```

### Requirements

Investigate:

POST /api/v1/evaluate

Inspect:

* classification outputs
* exported files
* evaluator logic

Verify actual prediction column names.

Support:

predicted_label
prediction
pred_label
class
label
land_use
landuse
category

If none exist:

Return explicit error.

Make evaluator work with actual classification outputs.

Add tests.

---

## DEF-013 — num_cells Data Integrity Issue

### Current Behavior

Area status returns:

```json
{
  "num_cells":0
}
```

while grid actually contains:

25+
cells.

### Requirements

Trace lifecycle:

create_job()
update_job()
get_job()

Verify:

Redis store
SQLite store
JobStore abstraction

Fix persistence.

Add tests.

---

## DEF-014 — Road Density Calculation Invalid

### Current Behavior

Values such as:

802693272762

appear.

Clearly incorrect.

### Root Cause Suspected

Area computed in geographic degrees.

### Requirements

Inspect:

fusion_service.py
spatial_service.py

Verify CRS.

Convert geometry into projected CRS.

Use:

EPSG:3857

or proper UTM zone.

Calculate area in square meters.

Recompute:

road density

Validate values are realistic.

Add tests.

---

# PHASE 3 — FULL REGRESSION TEST SUITE

Create:

tests/test_remaining_issue_fixes.py

Must include tests for:

* Large area rejection
* Invalid grid rejection
* Empty modalities rejection
* Delete endpoint
* Invalid dataset path
* Invalid dataset extension
* Evaluation endpoint
* num_cells persistence
* Road density calculation

All tests must pass.

---

# PHASE 4 — FAILURE INJECTION RETEST

Re-run all previously failing scenarios.

Execute:

| Scenario              |
| --------------------- |
| Oversized area        |
| Invalid grid          |
| Empty modalities      |
| Invalid export        |
| Invalid dataset path  |
| Invalid extension     |
| Invalid job           |
| Evaluate invalid data |

Record:

Expected vs Actual

Create:

audit/FAILURE_INJECTION_RETEST.md

---

# PHASE 5 — END-TO-END BACKEND RETEST

Execute full backend flow:

1. Health check

2. Load Area

3. Poll status

4. Preview grid

5. Grid details

6. Graph topology

7. Classification

8. Classification status

9. Classification result

10. Export

11. Evaluation

12. MLLM training

13. MLLM status

14. Delete job

Verify:

* HTTP code
* response schema
* data integrity
* Celery execution
* Redis updates

Create:

audit/BACKEND_E2E_RETEST.md

---

# PHASE 6 — FINAL REMEDIATION REPORT

Create:

audit/FINAL_REMEDIATION_REPORT.md

Include:

## Executive Summary

| Metric | Before | After |
| ------ | ------ | ----- |

---

## Fix Matrix

| Defect  | Status |
| ------- | ------ |
| DEF-007 |        |
| DEF-008 |        |
| DEF-009 |        |
| DEF-010 |        |
| DEF-011 |        |
| DEF-012 |        |
| DEF-013 |        |
| DEF-014 |        |

---

## Files Modified

List every file changed.

---

## Tests Added

List all new tests.

---

## Remaining Risks

Anything still unresolved.

---

## Defense Readiness Score

Score:

* Infrastructure
* API
* AI Pipeline
* Data Integrity
* Evaluation
* Stability

Provide overall score out of 100.

---

# IMPORTANT RULES

* Do not claim a fix without proving it.
* Every fix must have a corresponding regression test.
* Every test result must be included in the report.
* Verify behavior through actual execution.
* Do not stop after coding.
* Run tests after every fix.
* Produce all reports even if some issues remain unresolved.

Final output must contain:

✅ Files Modified

✅ Tests Added

✅ Tests Passed

✅ Issues Fixed

✅ Remaining Issues

✅ Updated Defense Readiness Score

```
