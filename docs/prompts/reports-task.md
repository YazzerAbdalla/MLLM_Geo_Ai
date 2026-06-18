# 🤖 AI AGENT FINAL SYSTEM AUDIT & DEFENSE READINESS PROMPT

## MLLM-Geo-AI Urban Classification System
### Complete Backend Audit, Infrastructure Verification, E2E Validation, Async Testing & Defense Readiness Assessment

**Date:** 2026-06-17  
**Project:** MLLM-Geo-AI  
**Version:** Urban AI Dashboard v3.0

---

# ⚠️ CRITICAL AGENT DIRECTIVE

You are acting as:

- Senior Backend Engineer
- Senior AI Engineer
- Senior GIS Engineer
- Infrastructure Engineer
- QA Engineer
- Technical Auditor

Your task is to perform a COMPLETE AUDIT of the MLLM-Geo-AI system.

You must verify everything through:

1. Source Code Inspection
2. Runtime Verification
3. Infrastructure Validation
4. End-to-End Testing
5. Async Processing Verification
6. Failure Injection Testing
7. Database Validation
8. Export Validation
9. Spatial Validation
10. Defense Simulation

---

# HONESTY RULES

Never trust:

- Documentation
- Comments
- Previous reports
- Claimed fixes

Only trust:

- Actual code
- Actual runtime behavior
- Actual generated artifacts

If code exists but fails:

Mark:

⚠️ IMPLEMENTED BUT BROKEN

NOT:

✅ IMPLEMENTED

If verification cannot be performed:

Mark:

UNVERIFIABLE

and explain why.

Never fabricate metrics.

Never assume functionality.

---

# STEP 0 — READ PROJECT CONTEXT

Read and understand all of the following before beginning the audit.

## Required Documents

1. remaining_phases_report.md
2. reports/*/master_summary*.md
3. reports/*/health_check*.md
4. reports/*/tasks_status_report*.md
5. Step 2 Student Project Document
6. onboarding_team_arabic.pdf
7. PRD Urban AI Dashboard v3
8. upgrade-poi-only-mllm-to-multi-modal-geo-ai
9. api-contract-scalability-multi-modal-urban-ai

These documents are historical references only.

Actual code and runtime behavior override documentation.

---

# STEP 1 — LIVE CODEBASE AUDIT

Inspect the entire repository.

---

## Application Structure Audit

Recursively inspect:

app/

Report:

- Newly added files
- Removed files
- Architecture changes
- New modules
- Deprecated modules

---

## API Audit

Inspect:

app/interfaces/api.py

List:

Method + Route

For every endpoint verify:

- Request schema
- Response schema
- Route registration
- Dependencies

---

## Infrastructure Audit

Inspect:

- celery_app.py
- .env
- docker-compose.yml
- Dockerfiles
- requirements.txt
- pyproject.toml

Verify:

- Redis configuration
- Celery configuration
- SQLite configuration
- Environment variables
- Queue configuration

---

## AI Pipeline Audit

Inspect:

- Training scripts
- Evaluation scripts
- Fusion pipeline
- Graph processing
- Image processing
- Text embedding pipeline

Verify:

- Model checkpoints
- Training history
- Evaluation outputs
- Feature dimensions

---

## Dataset Audit

Inspect:

data/raw/project.csv

Report:

- Total rows
- Label distribution
- Missing labels
- Duplicate rows
- Multi-class status

---

## Road Network Audit

Inspect:

data/raw/roads.graphml

Verify:

- Exists
- Readable
- File size
- Graph statistics

---

## Satellite Images Audit

Inspect:

data/sat_images/

Report:

- Image count
- Missing images
- Corrupted images

---

## Models Audit

Inspect:

models/
data/models/

Report:

- Checkpoint count
- Checkpoint names
- Hidden dimensions
- Metadata

---

## Evaluation Artifacts Audit

Inspect:

evals/

Verify:

- training_history.json
- evaluation outputs
- confusion matrix
- ablation reports

---

## Test Audit

Inspect:

tests/

Report:

- Unit tests
- Integration tests
- E2E tests
- Regression tests

Run tests and report:

- Passed
- Failed
- Skipped

---

# STEP 1.5 — INFRASTRUCTURE RUNTIME AUDIT

Start and verify runtime components.

Required:

1. Redis
2. FastAPI
3. Celery Worker
4. SQLite

---

## Redis Verification

Verify:

- Reachable
- Read working
- Write working
- Persistence working

---

## Celery Verification

Verify:

Worker online.

Run:

celery inspect active

celery inspect registered

celery inspect stats

Expected tasks:

- tasks.load_area.load_area_task
- tasks.classify.classify_task
- tasks.train_mllm.train_mllm_task

Report:

- Active workers
- Registered tasks
- Queue health

---

## SQLite Verification

Verify:

- Database exists
- Tables exist
- Read/write working

Check:

- Grid table
- Job table
- Evaluation table

---

## Docker Runtime Verification

Run:

docker compose up

Verify:

- API container healthy
- Redis container healthy
- Celery container healthy

Generate:

docker_runtime_report.md

---

# STEP 1.6 — DATABASE INTEGRITY AUDIT

Verify:

Grid table

Job table

Evaluation table

Check:

- orphan records
- duplicate IDs
- missing references
- completed jobs without grids
- evaluations without outputs

Generate:

database_integrity_report.md

---

# STEP 2 — API RUNTIME VERIFICATION

Actually call every endpoint.

Do not rely on code inspection.

For every endpoint verify:

- Route exists
- Status code
- Response schema
- Error handling

Mark:

✅ IMPLEMENTED & WORKING

⚠️ IMPLEMENTED BUT BROKEN

⚠️ PARTIAL

❌ MISSING

---

# STEP 2.1 — ASYNC PROCESSING VERIFICATION

Verify async behavior for:

- load-area
- classify
- train
- mllm/train

For each async endpoint verify:

Job lifecycle:

PENDING

↓

QUEUED

↓

RUNNING

↓

COMPLETED

or

FAILED

Capture:

- job_id
- celery_task_id
- Redis entry
- SQLite entry
- execution duration

If eager mode enabled:

Mark:

⚠️ ASYNC NOT VERIFIED (EAGER MODE)

Generate:

async_processing_report.md

---

# STEP 2.2 — WEBSOCKET VERIFICATION

Verify:

WS /api/v1/ws/progress/{job_id}

Check:

- Connection accepted
- Progress events received
- Completion event received
- Disconnect handling

Mark:

✅ WORKING

⚠️ CONNECTS BUT NO EVENTS

❌ BROKEN

Generate:

websocket_report.md

---

# STEP 2.3 — MLLM TRAINING FLOW AUDIT

Execute:

POST /api/v1/mllm/train

↓

GET /api/v1/mllm/status/{job_id}

↓

GET /api/v1/mllm/export/{job_id}

↓

GET /api/v1/mllm/model-card/{job_id}

Verify:

- Job created
- Training started
- Metrics generated
- Export generated
- Model card generated

If mocked:

Mark:

⚠️ PARTIAL

Generate:

mllm_training_report.md

---

# STEP 2.4 — EXPORT VALIDATION

Verify:

CSV

GeoJSON

Shapefile

Check:

- File exists
- File readable
- Schema valid
- File non-empty

Generate:

export_validation_report.md

---

# STEP 2.5 — FAILURE INJECTION TESTING

Execute negative tests.

---

## Load Area

- Huge area
- Invalid bbox
- Invalid grid size
- Empty modalities

---

## Classification

- Invalid grid_id
- Missing grid
- Unsupported modality
- Empty modalities

---

## Export

- Invalid format
- Missing job
- Failed job

---

## Training

- Missing dataset
- Invalid path
- Invalid extension
- Invalid epochs
- Invalid batch size

---

## Evaluation

- Invalid job
- Invalid ground truth

---

## Jobs

- Delete missing job
- Delete completed job
- Delete running job

Generate:

failure_injection_report.md

---

# STEP 2.6 — FULL BACKEND E2E FLOW TEST

Execute complete workflow.

---

## Classification Workflow

POST /load-area

↓

Wait for completion

↓

GET area-status

↓

GET grid-preview

↓

GET grid-details

↓

GET graph-topology

↓

POST classify

↓

Wait for completion

↓

GET classify-status

↓

GET classification-result

↓

GET export geojson

↓

POST evaluate

↓

GET evaluation export

---

Capture:

- Endpoint
- Payload
- Response
- Status code
- Latency
- Generated files
- Redis records
- SQLite records

Generate:

e2e_flow_report.md

---

# STEP 2.7 — PERFORMANCE AUDIT

Measure:

---

## API

- Average latency
- P95 latency
- Max latency

---

## Celery

- Queue delay
- Execution time

---

## Resources

- CPU
- RAM
- Disk

Identify bottlenecks.

Generate:

performance_report.md

---

# STEP 2.8 — SPATIAL VALIDATION AUDIT

Verify geospatial correctness.

---

## CRS Validation

Ensure:

Projected CRS used

NOT:

geometry.area in EPSG:4326

---

## Road Density Validation

Flag CRITICAL if:

road_density > 1000 km/km²

---

## Graph Metrics Validation

Validate:

- node_count
- edge_count
- clustering coefficient
- centrality

Generate:

spatial_validation_report.md

---

# STEP 2.9 — CLASSIFICATION OUTPUT AUDIT

Verify output schema.

Required fields:

- grid_id
- dominant_class
- confidence
- geometry
- road_density

Check:

- dominant_class not null
- confidence within [0,1]
- geometry valid GeoJSON

Generate:

classification_output_report.md

---

# STEP 2.10 — MODEL CONSISTENCY AUDIT

Verify:

Training hidden_dim

matches

Inference hidden_dim

Verify:

Feature dimensions match:

- POI
- Graph
- Satellite
- Text

Report mismatches as:

🚨 CRITICAL MODEL COMPATIBILITY ISSUE

Generate:

model_consistency_report.md

---

# STEP 2.11 — LEGACY FAILURE VERIFICATION

Investigate previously known failures.

Check status of:

1. torch_geometric dependency issue
2. mock API mismatch
3. missing evaluation function

Mark:

✅ FIXED

⚠️ PARTIAL

❌ STILL FAILING

Generate:

legacy_failures_report.md

---

# STEP 2.12 — DEFENSE DEMO SIMULATION

Simulate graduation defense.

Workflow:

1. Select Area
2. Load Area
3. View Grid
4. Run Classification
5. Open Grid Details
6. Export Results
7. Run Evaluation
8. Show Metrics

Capture:

- Total execution time
- Failures
- Manual interventions
- User-facing issues

Generate:

defense_demo_report.md

---

# STEP 3 — CREATE REPORT DIRECTORY

Create:

reports/2026-06-17/

---

# STEP 4 — MASTER AUDIT REPORT

Create:

reports/2026-06-17/progress_report_2026-06-17.md

Include:

## Section 1
What Changed Since Last Audit

## Section 2
P0 Critical Fixes Status

## Section 3
P1 Recommended Fixes Status

## Section 4
Phase 2–12 Completion

## Section 5
API Coverage Matrix

## Section 6
Infrastructure Status

## Section 7
Async Processing Findings

## Section 8
Failure Injection Findings

## Section 9
Performance Findings

## Section 10
Spatial Validation Findings

## Section 11
Classification Output Findings

## Section 12
Model Consistency Findings

## Section 13
Technical Assessment

Answer:

- Biggest defense risk
- Most surprising finding
- Top 3 priorities before defense
- Realistic P2 features
- Honest readiness score

## Section 14
Defense Readiness Score

| Dimension | Previous | Current | Delta |
|------------|-----------|----------|--------|
| ML Training Quality | | | |
| Output Schema Completeness | | | |
| API Coverage | | | |
| Phase Completion | | | |
| Demo Stability | | | |
| Infrastructure Readiness | | | |
| Async Reliability | | | |
| TOTAL | | | |

---

# STEP 5 — UPDATE remaining_phases_report.md

Update in place.

Do not replace.

Add:

## Updated 2026-06-17

Include:

- Updated readiness score
- Progress report link
- Updated statuses
- Update log

Mark each item:

✅ DONE

⚠️ PARTIAL

❌ MISSING

---

# REQUIRED DELIVERABLES

The audit is incomplete unless ALL files exist.

1. progress_report_2026-06-17.md
2. infrastructure_report.md
3. async_processing_report.md
4. websocket_report.md
5. e2e_flow_report.md
6. failure_injection_report.md
7. performance_report.md
8. spatial_validation_report.md
9. classification_output_report.md
10. model_consistency_report.md
11. database_integrity_report.md
12. export_validation_report.md
13. mllm_training_report.md
14. defense_demo_report.md
15. legacy_failures_report.md
16. docker_runtime_report.md
17. remaining_phases_report.md (updated)

---

# FINAL CONFIRMATION

Only after every step is completed print:

✅ Audit complete.

Files written:

- reports/2026-06-17/progress_report_2026-06-17.md
- reports/2026-06-17/infrastructure_report.md
- reports/2026-06-17/async_processing_report.md
- reports/2026-06-17/websocket_report.md
- reports/2026-06-17/e2e_flow_report.md
- reports/2026-06-17/failure_injection_report.md
- reports/2026-06-17/performance_report.md
- reports/2026-06-17/spatial_validation_report.md
- reports/2026-06-17/classification_output_report.md
- reports/2026-06-17/model_consistency_report.md
- reports/2026-06-17/database_integrity_report.md
- reports/2026-06-17/export_validation_report.md
- reports/2026-06-17/mllm_training_report.md
- reports/2026-06-17/defense_demo_report.md
- reports/2026-06-17/legacy_failures_report.md
- reports/2026-06-17/docker_runtime_report.md
- remaining_phases_report.md (updated)

# 🚨 RUNTIME EVIDENCE REQUIREMENT (MANDATORY)

This audit is considered FAILED unless runtime evidence is provided.

Code inspection alone is NOT verification.

Documentation alone is NOT verification.

Previous reports are NOT verification.

For every claim marked:

✅ IMPLEMENTED

or

✅ WORKING

the agent MUST provide runtime evidence.

---

## Evidence Rules

Every verification must include at least one of:

### Runtime Evidence

* terminal output
* curl output
* http response
* celery inspect output
* redis-cli output
* sqlite query output
* docker output
* websocket message capture
* generated file proof

---

## Forbidden Behavior

The following are NOT valid evidence:

* "verified via code inspection"
* "appears implemented"
* "looks correct"
* "route exists in source code"
* "task registered in file"
* "endpoint handler exists"

These may only justify:

UNVERIFIABLE

or

IMPLEMENTED BUT NOT TESTED

Never:

✅ WORKING

---

# Evidence Matrix

Every report must include:

| Item    | Code Verified | Runtime Verified | Evidence Attached |
| ------- | ------------- | ---------------- | ----------------- |
| Feature | YES/NO        | YES/NO           | YES/NO            |

If Runtime Verified = NO

Feature cannot be marked:

✅ WORKING

---

# Mandatory Evidence Collection

The audit is incomplete unless the following outputs are attached.

## Celery

Run:

celery inspect active

celery inspect registered

celery inspect stats

Paste actual output into report.

Not summary.

Actual output.

---

## Redis

Run:

redis-cli ping

redis-cli keys "job:*"

redis-cli get job:<sample_id>

Paste output.

---

## SQLite

Run:

SELECT COUNT(*) FROM grids;
SELECT COUNT(*) FROM jobs;
SELECT COUNT(*) FROM evaluations;

Paste output.

---

## Docker

Run:

docker ps

docker compose ps

Paste output.

---

## API

For every endpoint tested include:

Request

Response

Status Code

Latency

Actual Payload

Actual Response Body

---

## WebSocket

Capture actual messages received.

Example:

{
"status":"running",
"progress":0.42
}

Paste messages.

---

## Export Verification

Open exported files.

Verify:

* readable
* non-empty
* schema valid

Attach evidence.

---

## Model Verification

Load actual model.

Run actual inference.

Attach output.

Example:

torch.load(...)
model.eval()
prediction=...

Paste result.

---

# E2E Flow Evidence Requirement

A workflow is NOT considered completed unless:

Every step has:

* timestamp
* request
* response
* status code

If any step times out:

Mark:

⚠️ E2E FAILED

Do NOT write:

"verified via code inspection"

Do NOT continue marking downstream steps as successful.

---

# Async Verification Requirement

For every async endpoint capture:

job_id

celery_task_id

Redis entry

Worker logs

Start timestamp

Finish timestamp

Duration

If these are missing:

Mark:

⚠️ ASYNC NOT VERIFIED

---

# Failure Injection Requirement

For every negative test provide:

Input

Expected Result

Actual Result

Status Code

If not executed:

Mark:

UNVERIFIABLE

---

# Report Grading Rules

Feature Status Rules:

Code Exists + Runtime Pass
→ ✅ IMPLEMENTED & WORKING

Code Exists + Runtime Fail
→ ⚠️ IMPLEMENTED BUT BROKEN

Code Exists + Runtime Not Executed
→ UNVERIFIABLE

No Code
→ ❌ MISSING

Any violation of these rules invalidates the audit.

---

# Final Audit Gate

The agent is NOT allowed to print:

✅ Audit complete

unless:

1. Runtime evidence exists
2. Celery outputs attached
3. Redis outputs attached
4. SQLite outputs attached
5. Docker outputs attached
6. API responses attached
7. WebSocket messages attached
8. E2E completed without skipped steps

Otherwise print:

🚨 AUDIT INCOMPLETE — RUNTIME EVIDENCE MISSING

If any step is skipped, timed out, or replaced with code inspection:

The entire E2E flow must be marked:

⚠️ E2E FLOW FAILED

not:

⚠️ Partial

not:

✅ Working