# Docker Runtime Report | Date: 2026-06-17 | MLLM-Geo-AI Project

## 1. Docker Configuration

**docker-compose.yml** defines 5 services:

| Service | Image | Ports | Healthcheck | Status |
|---------|-------|-------|-------------|--------|
| redis | redis:7-alpine | 6379 | redis-cli ping | ⚠️ NOT RUNNING IN DOCKER |
| nginx | nginx:latest | 80 | depends on fastapi | ⚠️ NOT RUNNING IN DOCKER |
| fastapi | custom | 8000 | curl /health | ⚠️ NOT RUNNING IN DOCKER |
| celery-cpu-worker | custom | - | none | ⚠️ NOT RUNNING IN DOCKER |
| celery-gpu-worker | custom | - | GPU support | ⚠️ NOT RUNNING IN DOCKER |

## 2. Dockerfile Analysis

**Dockerfile** (`Dockerfile`):
- Base: python:3.11-slim
- Installs: gcc, g++, curl, libgl1, libglib2.0-0, sqlite3
- Copies requirements.txt, installs dependencies
- Copies entire project
- Exposes port 8000
- CMD: `python -m app.main`

**Potential issues in Dockerfile**:
- `libgl1` and `libglib2.0-0` are for OpenCV — good for satellite image processing
- No GPU-enabled PyTorch installation (uses CPU version from requirements.txt)
- No `.env` file copied (must be mounted or passed via environment)

## 3. Docker Runtime Status

**Docker containers are NOT currently running.** The application runs natively:
- FastAPI: Running natively on port 8000
- Redis: Running natively on port 6379
- Celery worker: Running natively

## 4. Recommendations

1. Start Docker services for reproducible demo environment
2. Add `.dockerignore` to exclude large files (roads.graphml, .venv, etc.)
3. Consider GPU-enabled PyTorch for celery-gpu-worker

## 5. Evidence Matrix

| Item | Code Verified | Runtime Verified | Evidence Attached |
|------|:-------------:|:----------------:|:-----------------:|
| Dockerfile | YES | NO | NO |
| docker-compose.yml | YES | NO | NO |
| Container Health | YES | NO | NO |
