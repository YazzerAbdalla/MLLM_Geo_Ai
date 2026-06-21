# Performance Report

**Date:** 2026-06-17
**Project:** MLLM-Geo-AI

## Methodology

API latency measured from request submission to response receipt on local development machine (Windows, CPU-only). All measurements include a ~2s baseline overhead attributed to CPU-bound imports and framework initialization.

## API Latency Measurements

| Endpoint                                  | Latency   | Notes                                   |
|-------------------------------------------|-----------|-----------------------------------------|
| `GET /health`                             | ~2.0s     | Baseline overhead only                  |
| `POST /api/v1/load-area` (submit)         | ~2.5s     | Submit to Celery queue                  |
| Load-area async execution                 | ~8-10s    | Celery worker processing time           |
| `GET /api/v1/area-status/{job_id}`        | ~2.0s     | Each poll                               |
| `GET /api/v1/grid/{id}/preview`           | ~2.5s     |                                         |
| `GET /api/v1/grid/{id}/details`           | ~2.0s     |                                         |
| `GET /api/v1/grid/{id}/graph-topology`    | ~13.5s    | **Returns 500 error after timeout**     |
| `POST /api/v1/classify` (submit)          | ~2.1s     | Submit to Celery queue                  |
| `GET /api/v1/classify-status/{job_id}`    | ~2.0s     | Each poll                               |

## Bottlenecks

1. **Graph-topology endpoint** — Takes 13.5 seconds before returning HTTP 500. Likely caused by reading the full 584MB `roads.graphml` file and constructing the topology object in memory without streaming or pagination.

2. **Baseline overhead (~2s)** — Every endpoint incurs ~2 seconds of fixed overhead. Root cause is suspected to be:
   - Heavy imports at module level (torch, sentence-transformers, geopandas, OSMnx)
   - CPU contention from other processes on the development machine
   - FastAPI process startup and middleware chain

3. **Classify endpoint** — Fails with a memory error due to insufficient paging file size when loading the sentence transformer model (~470MB) alongside torch and other ML components.

## Celery Performance

| Metric                  | Value      |
|-------------------------|------------|
| Queue delay             | <1s        |
| Load-area execution     | ~10s total |
| Classification execution| ~2.1s submit, then memory failure |

## Recommendations

| Issue                          | Recommendation                               |
|--------------------------------|----------------------------------------------|
| 2s baseline overhead           | Lazy-load heavy models; use async where possible |
| Graph-topology 13.5s + 500    | Stream road network data; add pagination; set realistic timeout |
| Classify memory error          | Increase paging file; use smaller batch; lazy-load model |

## Evidence Matrix

| Evidence File                                              | Content                                         |
|------------------------------------------------------------|-------------------------------------------------|
| `audit/api_responses/`                                     | Collected API response snapshots with timestamps|
| `data/raw/roads.graphml`                                   | 584,632,898 bytes — large file causes graph-topology failure |
| `evals/task_execution.log` (if present)                    | Celery task execution durations                 |
