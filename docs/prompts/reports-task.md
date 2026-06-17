# 🤖 AI AGENT FULL SYSTEM AUDIT PROMPT

## MLLM-Geo-AI Urban Classification System — Complete Backend Audit, E2E Verification & Defense Readiness Assessment

**Date: 2026-06-17**
**Project: MLLM-Geo-AI**
**Version: Urban AI Dashboard v3.0**

---

# ⚠️ CRITICAL AGENT DIRECTIVE

You are acting as a Senior AI Engineer, Backend Engineer, QA Engineer, Infrastructure Engineer, and Technical Auditor.

Your objective is to perform a COMPLETE audit of the MLLM-Geo-AI system.

DO NOT trust documentation.

DO NOT trust code comments.

DO NOT trust previous reports.

Everything must be verified through:

1. Source Code Inspection
2. Runtime Verification
3. Infrastructure Validation
4. End-to-End Testing
5. Failure Injection Testing

If something exists in code but fails during execution:

Mark it:

⚠️ IMPLEMENTED BUT BROKEN

NOT:

✅ IMPLEMENTED

Never fabricate results.

If something cannot be verified:

UNVERIFIABLE — explain why.

Do not stop until every deliverable listed in this prompt is generated.

---

# STEP 0 — READ PROJECT CONTEXT

Read and understand the following files completely before performing any audit.

## Required Documents

1. remaining_phases_report.md
2. reports/*/master_summary*.md
3. reports/*/health_check*.md
4. reports/*/tasks_status_report*.md
5. Step 2 student project document
6. onboarding_team_arabic.pdf
7. PRD Urban AI Dashboard v3
8. upgrade-poi-only-mllm-to-multi-modal-geo-ai
9. api-contract-scalability-multi-modal-urban-ai

These documents are historical context only.

Actual code and runtime behavior override documentation.

---

# STEP 1 — LIVE CODEBASE AUDIT

Inspect the entire repository.

## Check

### Application Structure

List all files under:

app/

recursively.

Identify:

* newly added files
* deleted files
* major architecture changes

---

### API Inspection

Inspect:

app/interfaces/api.py

List every route:

Method + Path

Verify:

* route registration
* request models
* response models

---

### Infrastructure

Verify:

* Redis configuration
* Celery configuration
* Worker queues
* Environment variables
* SQLite configuration

Inspect:

* celery_app.py
* .env
* docker files
* requirements

---

### AI Pipeline

Inspect:

* training scripts
* evaluation scripts
* fusion logic
* graph processing
* image processing

Verify:

* model paths
* checkpoints
* training history
* evaluation outputs

---

### Dataset Audit

Inspect:

data/raw/project.csv

Report:

* total rows
* class distribution
* missing labels
* duplicate rows

---

### Road Network

Inspect:

data/raw/roads.graphml

Verify:

* exists
* file size
* readable

---

### Satellite Images

Inspect:

data/sat_images/

Report:

* image count
* missing images

---

### Tests

Inspect:

tests/

Report:

* test files
* integration tests
* E2E tests
* coverage status

---

### Evaluation Artifacts

Inspect:

evals/

Verify:

* training_history.json
* ablation results
* evaluation outputs

---

### Models

Inspect:

models/
data/models/

Report:

* checkpoint count
* model names
* hidden dimensions
* training metadata

---

# STEP 1.5 — INFRASTRUCTURE AUDIT

Start and validate the runtime stack.

Required Components:

1. Redis
2. FastAPI
3. Celery Worker
4. SQLite

Verify:

## Redis

* reachable
* read/write working

## Celery

Verify:

* worker online
* queues active

Run:

celery inspect active
celery inspect registered
celery inspect stats

Expected Tasks:

tasks.load_area.load_area_task

tasks.classify.classify_task

tasks.train_mllm.train_mllm_task

Report:

* registered tasks
* active workers
* queue health

---

# STEP 2 — API RUNTIME VERIFICATION

Do not rely on source code.

Actually call endpoints.

For each endpoint verify:

* route exists
* status code
* response schema
* error handling

Mark:

✅ IMPLEMENTED & WORKING

⚠️ IMPLEMENTED BUT BROKEN

⚠️ PARTIALLY IMPLEMENTED

❌ MISSING

---

# STEP 2.5 — FAILURE INJECTION TESTING

Execute negative tests.

## Test Cases

### Load Area

* huge area
* invalid bbox
* invalid grid size

### Classification

* invalid grid_id
* missing grid
* empty modalities
* unsupported modality

### Export

* invalid format
* invalid job id

### Training

* missing dataset
* invalid dataset path
* unsupported extension
* invalid epochs
* invalid batch size

### Evaluation

* invalid job id
* invalid ground truth

### Jobs

* delete invalid job
* delete completed job
* delete running job

Generate:

failure_injection_report.md

---

# STEP 2.6 — FULL BACKEND END-TO-END FLOW TEST

Execute a complete workflow.

## Flow

POST load-area

↓

wait until completed

↓

GET area-status

↓

GET grid preview

↓

GET grid details

↓

POST classify

↓

wait until completed

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

For every step capture:

* endpoint
* payload
* response
* status code
* latency
* generated files
* generated Redis records
* generated SQLite records

Generate:

e2e_flow_report.md

---

# STEP 2.7 — PERFORMANCE AUDIT

Measure:

## API

* average latency
* max latency

## Celery

* queue delays
* processing time

## Resources

* CPU
* RAM
* Disk

Identify bottlenecks.

Generate:

performance_report.md

---

# STEP 2.8 — SPATIAL VALIDATION AUDIT

Verify geospatial correctness.

## Check

### Cell Area

Verify area uses projected CRS.

Not:

geometry.area in WGS84.

### Road Density

Validate values.

Flag CRITICAL if:

road_density > 1000 km/km²

### Graph Metrics

Validate:

* node_count
* edge_count
* clustering
* centrality

Generate:

spatial_validation_report.md

---

# STEP 3 — CREATE REPORT DIRECTORY

Create:

reports/2026-06-17/

---

# STEP 4 — WRITE MASTER PROGRESS REPORT

Create:

reports/2026-06-17/progress_report_2026-06-17.md

---

## Section 1

What Changed Since Last Audit

Compare previous audit state vs current state.

---

## Section 2

P0 Critical Fixes Status

Mark:

✅ Done

⚠️ Partial

❌ Missing

Provide evidence.

---

## Section 3

P1 Recommended Fixes Status

Provide evidence.

---

## Section 4

Student Phase Completion

Map actual implementation to:

Phase 2 → Phase 12

---

## Section 5

API Coverage Matrix

List every endpoint.

Status:

✅ Working

⚠️ Broken

⚠️ Partial

❌ Missing

Summary:

X / 20 fully working.

---

## Section 6

Infrastructure Status

Redis

Celery

SQLite

Files

Workers

Queues

---

## Section 7

Failure Injection Findings

Summarize:

* validation issues
* runtime issues
* missing protections

---

## Section 8

Performance Findings

Summarize bottlenecks.

---

## Section 9

Spatial Validation Findings

Summarize GIS correctness.

---

## Section 10

Agent Technical Assessment

Answer:

### Biggest defense risk

### Most surprising finding

### Top 3 priorities before defense

### Realistic P2 features

### Honest defense readiness score

---

## Section 11

Defense Readiness Score

| Dimension                  | Previous | Current | Delta |
| -------------------------- | -------- | ------- | ----- |
| ML Training Quality        |          |         |       |
| Output Schema Completeness |          |         |       |
| API Coverage               |          |         |       |
| Phase Completion           |          |         |       |
| Demo Stability             |          |         |       |
| TOTAL                      |          |         |       |

---

# STEP 5 — UPDATE remaining_phases_report.md

Update in place.

Do not replace.

Add:

## Updated 2026-06-17

Include:

* new readiness score
* progress link
* updated statuses
* update log

Mark each item:

✅ DONE

⚠️ PARTIAL

❌ MISSING

---

# REQUIRED DELIVERABLES

The audit is incomplete unless ALL files exist.

1. progress_report_2026-06-17.md
2. e2e_flow_report.md
3. failure_injection_report.md
4. infrastructure_report.md
5. performance_report.md
6. spatial_validation_report.md
7. updated remaining_phases_report.md

---

# HONESTY RULES

Never mark:

✅ DONE

unless verified through code inspection AND runtime testing.

If code exists but runtime fails:

⚠️ IMPLEMENTED BUT BROKEN

If verification cannot be performed:

UNVERIFIABLE

with explanation.

---

# FINAL CONFIRMATION

Only after every step is complete print:

✅ Audit complete.

Files written:

* reports/2026-06-17/progress_report_2026-06-17.md
* reports/2026-06-17/e2e_flow_report.md
* reports/2026-06-17/failure_injection_report.md
* reports/2026-06-17/infrastructure_report.md
* reports/2026-06-17/performance_report.md
* reports/2026-06-17/spatial_validation_report.md
* remaining_phases_report.md (updated)
