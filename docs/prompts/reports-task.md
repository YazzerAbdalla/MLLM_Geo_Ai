# 🤖 AI AGENT PROGRESS AUDIT PROMPT
## MLLM-Geo-AI Urban Classification System — Progress Check, Report & Remaining Phases Update
**Date: 2026-05-24 | Project: MLLM-Geo-AI | Version: Urban AI Dashboard v3.0**

---

> **⚠️ CRITICAL AGENT DIRECTIVE — READ FIRST:**
> You are a senior full-stack AI engineer and technical writer assigned to audit the current state of the MLLM-Geo-AI project and produce a concise progress report. **Do NOT stop until every single step in this prompt is complete and saved to disk.** If you encounter a blocker, document it clearly and move on. Today's date is **2026-05-24**.

---

## 🧠 STEP 0 — ORIENT YOURSELF FIRST (READ BEFORE WRITING ANYTHING)

Before producing any report, read and fully understand the following files in this exact order. These are your ground truth. Do not rely on memory or assumptions.

### Reference Documents to Read

1. **`remaining_phases_report.md`** — The last known gap analysis (May 4 2026). This is your baseline. Every task mentioned here is either Done, Partial, or Still Missing. You will update this file at the end.

2. **`reports/2026-05-06/07_master_summary_2026-05-06.md`** — The master summary from the last audit sprint (May 6 2026). Understand what was working and what was not at that point.

3. **`reports/2026-05-06/01_app_health_check_2026-05-06.md`** — Last health check. Know which endpoints existed, which were missing, and what the overall health score was.

4. **`reports/2026-05-06/06_tasks_status_report_2026-05-06.md`** — Last task status breakdown. Know what was Completed / In Progress / Not Started per team.

5. **`Step_2_مشروع_الطالب_التصنيف_العمراني_Step_2__1_.docx`** — The student project plan (Phase 2 through 12). This defines what the project is supposed to deliver. Every phase here is a success criterion.

6. **`onboarding_team_arabic.pdf`** — Team onboarding document. Read it to understand team structure, responsibilities, and any onboarding tasks that should have been completed.

7. **`PRD_Urban_AI_Dashboard_v3.docx`** — The full product requirements document (v3.0). Your source of truth for what the dashboard must do.

8. **`upgrade-poi-only-mllm-to-multi-modal-geo-ai.md`** — The technical upgrade plan (POI-only → Multi-Modal). Shows what phases of backend work were planned.

9. **`api-contract-scalability-multi-modal-urban-ai.md`** — The agreed API contract. Every endpoint here should exist in the app.

> **After reading all of the above**, you have the full context. Now proceed with the steps below.

---

## 📁 STEP 1 — INSPECT THE LIVE CODEBASE

Scan the actual project files to determine the real current state. Do not trust documentation — verify by reading code.

### What to check:

1. **List all files** under `app/` recursively. Note any new files added since the last audit.
2. **Check API routes** in `app/interfaces/api.py` — list every registered endpoint (method + path).
3. **Check for Redis/Celery**: Is `celery_app.py` or equivalent present and configured? Is Redis connection configured in `.env`?
4. **Check for new model files**: Any new `.pt` weights, new training scripts, or new eval scripts?
5. **Check `data/raw/project.csv`**: What is the label distribution now? (Use Python/bash to count rows per label.)
6. **Check `data/raw/roads.graphml`**: Does this file exist and is it non-empty?
7. **Check `data/sat_images/`**: How many satellite images exist?
8. **Check `tests/`**: What test files exist? Were the test files from the previous audit (`test_api_integration.py`, `test_celery_tasks.py`) added?
9. **Check `evals/`**: Does `training_history.json` exist? Any ablation results?
10. **Check `models/`**: What model weight files exist? What is the hidden_dim used in `mlp_model.py`?

---

## 📋 STEP 2 — CREATE TODAY'S REPORT FOLDER AND WRITE THE PROGRESS REPORT

### Folder to create:
```
reports/2026-05-24/
```

### File to create:
```
reports/2026-05-24/progress_report_2026-05-24.md
```

---

### Report Structure

#### Header
```
# Progress Report | Date: 2026-05-24 | MLLM-Geo-AI Project
Sprint: Post-Audit Progress Check
Reference: remaining_phases_report.md (May 4, 2026) + last audit (May 6, 2026)
```

---

#### Section 1 — What Changed Since Last Audit (May 6, 2026)

Compare what you found in Step 1 against the last known state from the reports you read in Step 0. Be concrete:

- New files added?
- Endpoints added or removed?
- Dataset relabeled?
- Tests added?
- Model weights updated?
- Infrastructure changes (Redis, Celery)?

Use a simple table:

| Area | Last State (May 6) | Current State (May 24) | Changed? |
|------|-------------------|------------------------|----------|
| API endpoints | 9/20 | ? | ? |
| Label distribution | All label=0 | ? | ? |
| roads.graphml | Missing | ? | ? |
| Test files | 2 files planned | ? | ? |
| Redis running | ❌ Not running | ? | ? |
| ... | ... | ... | ... |

---

#### Section 2 — P0 Critical Fixes Status (from remaining_phases_report.md)

Check each P0 item from the remaining phases report. For each one, say whether it is Done ✅, Partial ⚠️, or Still Missing ❌, and explain briefly WHY based on what you found in the code.

| ID | Fix | File | Status | Evidence |
|----|-----|------|--------|----------|
| P0-1 | Dataset relabeling (multi-class labels) | data/raw/project.csv | ? | |
| P0-2 | MLP hidden_dim mismatch fix | domain/mlp_model.py | ? | |
| P0-3 | encode() → embed_texts() fix | train_multimodal.py | ? | |
| P0-4 | Validation monitoring loop | train_multimodal.py | ? | |
| P0-5 | roads.graphml pre-cached | data/raw/roads.graphml | ? | |

---

#### Section 3 — P1 Recommended Fixes Status

Same format as Section 2 but for P1 items.

| ID | Fix | Status | Evidence |
|----|-----|--------|----------|
| P1-6 | Ablation --modalities flag | ? | |
| P1-7 | graph/text embedding norm in output schema | ? | |
| P1-8 | Training history saved to JSON | ? | |
| P1-9 | Spatial Accuracy (8-neighbor) metric | ? | |
| P1-10 | DELETE /jobs/{job_id} endpoint | ? | |

---

#### Section 4 — Step 2 Student Document Phase Completion

Cross-reference the student project phases (from the Step 2 document you read) against what exists in the codebase now.

| Phase | Description | Status | Notes |
|-------|-------------|--------|-------|
| Phase 2 | Multi-modal data collection (POI, roads, satellite) | ? | |
| Phase 3 | Data cleaning (WGS84 unified) | ? | |
| Phase 4 | Graph G=(V,E) construction | ? | |
| Phase 6 | Feature fusion (X = POI+Image+Graph+Text) | ? | |
| Phase 7 | Base models (GNN + CNN + Text Encoder) | ? | |
| Phase 8 | Custom MLLM Builder | ? | |
| Phase 9 | Training pipeline | ? | |
| Phase 10 | Evaluation (Accuracy, F1, Spatial Accuracy) | ? | |
| Phase 11 | Digital Twin NL query | ? | |
| Phase 12 | Geo-MLLM export + demo | ? | |

---

#### Section 5 — API Coverage Update

List every endpoint from the API contract. Mark each as ✅ Implemented | ❌ Missing | ⚠️ Partial.

| # | Method | Route | Status | Notes |
|---|--------|-------|--------|-------|
| 1 | POST | /api/v1/load-area | ? | |
| 2 | GET | /api/v1/area-status/{job_id} | ? | |
| 3 | GET | /api/v1/grid/{grid_id}/preview | ? | |
| 4 | GET | /api/v1/grid/{grid_id}/graph-topology | ? | |
| 5 | POST | /api/v1/classify | ? | |
| 6 | GET | /api/v1/classify-status/{job_id} | ? | |
| 7 | GET | /api/v1/classification-result/{job_id} | ? | |
| 8 | POST | /api/v1/evaluate | ? | |
| 9 | GET | /api/v1/evaluate/{job_id}/export | ? | |
| 10 | POST | /api/v1/mllm/train | ? | |
| 11 | GET | /api/v1/mllm/status/{job_id} | ? | |
| 12 | GET | /api/v1/mllm/export/{job_id} | ? | |
| 13 | GET | /api/v1/mllm/model-card/{job_id} | ? | |
| 14 | POST | /api/v1/query | ? | |
| 15 | POST | /api/v1/train | ? | |
| 16 | GET | /api/v1/train-status/{job_id} | ? | |
| 17 | GET | /api/v1/export/{job_id} | ? | |
| 18 | GET | /api/v1/thumbnails/{grid_id}/{cell}.jpg | ? | |
| 19 | DELETE | /api/v1/jobs/{job_id} | ? | |
| 20 | WS | /api/v1/ws/progress/{job_id} | ? | |

**Summary: X of 20 endpoints implemented.**

---

#### Section 6 — Onboarding Tasks Check

Based on the onboarding PDF you read: list any onboarding steps or team setup tasks and confirm whether they appear to have been completed (based on what you can observe in the codebase and file structure).

---

#### Section 7 — Agent Thinking & Analysis

> This section is your honest technical assessment. Write it as if you are briefing a senior engineer who wasn't there. Be direct. Do not sugarcoat.

Answer these questions in plain prose:

1. **What is the single biggest risk to a successful defense?** (be specific — not "technical debt" but exactly what would go wrong if someone ran the demo right now)
2. **What is the most surprising finding from today's audit?** (something that was expected to be done but isn't, or something that was broken but now works)
3. **If the team had exactly 3 days before defense, what should they work on first, second, and third?** Justify your priority order.
4. **What P2 items (originally future work) are now realistic to include given the current state?**
5. **What is the honest defense readiness score today (X/50)?** Use the same 5 dimensions as the remaining_phases_report.md. Show your working.

---

#### Section 8 — Updated Defense Readiness Score

Use the exact same scoring table format as remaining_phases_report.md:

| Dimension | Score (May 4) | Score (May 24) | Delta | Key Change |
|-----------|--------------|---------------|-------|------------|
| ML Training Quality | 3/10 | ? | ? | |
| Output Schema Completeness | 7/10 | ? | ? | |
| API Coverage | 6/10 | ? | ? | |
| Step 2 Phase Completion | 5/10 | ? | ? | |
| Demo Stability | 1/10 | ? | ? | |
| **TOTAL** | **22/50** | **?/50** | **?** | |

---

## 📋 STEP 3 — UPDATE remaining_phases_report.md

After writing the progress report, **update the existing `remaining_phases_report.md`** file directly. Do NOT replace it — edit it in place.

### What to add/change:

1. **At the very top of the file**, add a new status banner:

```markdown
---
## 🔄 Updated: 2026-05-24

| Defense Readiness Score (Updated) | Previous Score |
| :---: | :---: |
| **X / 50 — [STATUS]** | **22 / 50 — NOT READY** |

> See full update report: `reports/2026-05-24/progress_report_2026-05-24.md`
---
```

2. **In Section 1 (Current Status table)**, update the "Now" column for every item based on what you actually found. Change "BROKEN" → "FIXED" where fixed, or "BROKEN" → "PARTIAL" where partially done. Add today's date next to each changed item.

3. **In Section 2 (P0 fixes)**, add a ✅ DONE or ⚠️ PARTIAL or ❌ STILL MISSING marker at the start of each P0 section heading.

4. **In Section 3 (P1 fixes)**, do the same — add status marker to each P1 section heading.

5. **In Section 5 (Phase Completion Map)**, update the Status column for each phase row.

6. **At the bottom of the file**, add a new section:

```markdown
---
## Update Log

| Date | Action | Changed By |
|------|--------|------------|
| 2026-05-04 | Initial gap analysis | AI Engineering Team |
| 2026-05-24 | Progress audit update | AI Agent (automated audit) |
```

---

## 🔧 EXECUTION RULES

### File Creation Rules
- Create folder `reports/2026-05-24/` before writing any file.
- Report file: `reports/2026-05-24/progress_report_2026-05-24.md`
- Update (do not replace) `remaining_phases_report.md`
- Use Markdown format. Use tables for comparisons. Use ✅ ❌ ⚠️ consistently.

### Honesty Rules
- Do NOT fabricate metrics. If something cannot be verified, write: `UNVERIFIABLE — Reason: [explain]`
- Do NOT mark something ✅ Done unless you can cite the file and line/section that proves it.
- If the code exists but is broken or incomplete, mark it ⚠️ Partial, not ✅ Done.

### Agent Behavior Rules
- Read ALL reference documents in Step 0 before writing anything.
- Complete all 3 Steps before stopping.
- After completing everything, print a final confirmation:

```
✅ Audit complete. Files written:
- reports/2026-05-24/progress_report_2026-05-24.md
- remaining_phases_report.md (updated)
```

---

## 🏁 FINAL CHECKLIST

Before stopping, verify:

- [ ] All Step 0 reference documents were read
- [ ] Live codebase was inspected (Step 1)
- [ ] Folder `reports/2026-05-24/` was created
- [ ] `reports/2026-05-24/progress_report_2026-05-24.md` was written with all 8 sections
- [ ] `remaining_phases_report.md` was updated (not replaced) with status markers and update log

**You are not done until all 5 boxes above are checked.**

---

*Prompt version: 2026-05-24 | MLLM-Geo-AI Project | Progress Audit Sprint*
*Reference docs: remaining_phases_report.md, Step 2 student doc, onboarding PDF, PRD v3.0, API contract, upgrade plan, all May-06 reports*
```

---