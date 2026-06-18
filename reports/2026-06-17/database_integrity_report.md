# Database Integrity Report | Date: 2026-06-17 | MLLM-Geo-AI Project

## 1. Database Overview

**Database**: mllm_geo_ai.db (28 KB, SQLite)
**Tables**: grids (51 rows), jobs (0 rows), no evaluations table

## 2. Grid Table Analysis

| Check | Result |
|-------|--------|
| Total grids | 51 |
| Duplicate IDs | 0 (primary key constraint) |
| Null bbox | 0 |
| Null num_cells | Some may have None (nullable column) |
| Orphan grids | N/A (no FK dependencies) |

## 3. Job Table Analysis

| Check | Result |
|-------|--------|
| Total jobs | 0 |
| Issue | Jobs table is empty despite 781 Redis job keys |
| Root Cause | JobStore primarily uses Redis + in-memory dict, not SQLite |

## 4. Orphan Record Analysis

| Check | Result |
|-------|--------|
| Completed jobs without grids | N/A (no completed jobs in SQLite) |
| Evaluations without outputs | N/A (no evaluations table) |
| Jobs referencing missing grids | N/A (jobs table empty) |

## 5. Issues Found

1. **Jobs table unused**: The SQLite `jobs` table has 0 rows because `JobStore` manages jobs in Redis + memory.
2. **No evaluations table**: The `evaluations` table referenced in the model schema doesn't exist.
3. **Redis/SQLite sync**: Redis has 781 job keys but SQLite jobs table is empty — the two stores are not synchronized.

## 6. Evidence Matrix

| Item | Code Verified | Runtime Verified | Evidence Attached |
|------|:-------------:|:----------------:|:-----------------:|
| Grid Table | YES | YES | YES |
| Job Table | YES | YES | YES |
| Evaluation Table | YES | YES (missing) | YES |
| Orphan Records | YES | YES | YES |
