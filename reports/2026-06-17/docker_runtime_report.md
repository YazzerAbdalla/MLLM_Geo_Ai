# Docker Runtime Report — 2026-06-17

## Badge: ⚠️ CONFIGURED but NOT VERIFIED at runtime

## Docker Configuration Files

| File | Path | Status |
|------|------|--------|
| docker-compose.yml | `D:\Projects\MLLM_Geo_Ai\docker-compose.yml` | ✅ EXISTS |
| Dockerfile | `D:\Projects\MLLM_Geo_Ai\Dockerfile` | ✅ EXISTS |
| nginx.conf | `D:\Projects\MLLM_Geo_Ai\nginx.conf` | ✅ EXISTS |
| .dockerignore | `D:\Projects\MLLM_Geo_Ai\.dockerignore` | ✅ EXISTS |

## docker-compose.yml Structure

**Services defined**:
| Service | Image/Build | Ports | Notes |
|---------|------------|-------|-------|
| `redis` | `redis:7-alpine` | `6379:6379` | Healthcheck enabled, volume `redis_data` |
| `nginx` | `nginx:latest` | `80:80` | Reverse proxy, depends on fastapi (healthy) |
| `fastapi` | Build from `Dockerfile` | `8000:8000` | Healthcheck, depends on redis (healthy) |
| `celery-cpu-worker` | Build from `Dockerfile` | — | `celery -A celery_app worker -Q cpu -c 4` |
| `celery-gpu-worker` | Build from `Dockerfile` | — | GPU resource reservation, `celery -A celery_app worker -Q gpu -c 1` |

**Volumes**:
- `redis_data` — Redis persistence
- `./data:/app/data` — Shared data directory
- `./models:/app/models` — Model files
- `./mllm_goe_ai.db:/app/mllm_geo_ai.db` — SQLite database (note: typo "goe" vs "geo")
- `${HOME}/.config/earthengine:/root/.config/earthengine:ro` — GEE credentials (mount issue: `$HOME` not set)

## Dockerfile (`Dockerfile`)
- Base: `python:3.11-slim`
- System deps: gcc, g++, curl, libgl1, libglib2.0-0, sqlite3
- Installs `requirements.txt`
- Copies entire project
- CMD: `python -m app.main`

## nginx.conf
- Upstream `fastapi` on `fastapi:8000`
- Proxies `/` and `/ws/` (WebSocket support with Upgrade headers)

## .dockerignore
- Excludes: .venv, .git, __pycache__, .env, data/sat_images/, data/raw/, models/*.pt, reports/, docs/, *.db, tests/, *.md, nginx.conf

## Runtime Status

| Component | Running Mode | Status |
|-----------|-------------|--------|
| Redis | Docker container (`mllm-geo-redis`) | ✅ Up (17 hours, healthy on port 6379) |
| FastAPI | Native (python -m app.main) | ✅ Running on port 8000 |
| Celery worker | Native | ✅ Running (processing tasks) |
| Nginx | Docker (planned) | ❌ NOT running — only redis container active |
| fastapi container | Docker (planned) | ❌ NOT running — running natively |
| celery containers | Docker (planned) | ❌ NOT running — running natively |

**Docker compose status output**:
```
NAME             IMAGE            COMMAND                  SERVICE   CREATED       STATUS                  PORTS
mllm-geo-redis   redis:7-alpine   "docker-entrypoint.s…"   redis     4 weeks ago   Up 17 hours (healthy)   0.0.0.0:6379->6379/tcp
```

Only the Redis container is running via Docker. The app, celery workers, and nginx are running natively on the host.

## Issues Found

1. **HOME variable not set**: Docker compose warning: `The "HOME" variable is not set. Defaulting to a blank string.` — This affects the GEE credentials mount in the fastapi and celery services.
2. **Database path typo**: In `docker-compose.yml`, the volume mapping uses `./mllm_goe_ai.db:/app/mllm_geo_ai.db` (note: "goe" vs "geo"). This means the SQLite file won't match.
3. **Full docker stack not tested**: The complete containerized setup (fastapi + celery + nginx) was not verified at runtime in this session.

## Docker Readiness Assessment

| Aspect | Status | Notes |
|--------|--------|-------|
| docker-compose.yml | ✅ Complete | All 5 services defined with healthchecks |
| Dockerfile | ✅ Complete | Python 3.11-slim, installs deps |
| nginx.conf | ✅ Complete | Reverse proxy + WebSocket passthrough |
| .dockerignore | ✅ Complete | Excludes dev/test artifacts |
| Redis container | ✅ Running | Verified healthy on port 6379 |
| FastAPI container | ❌ Not running | Running natively instead |
| Celery containers | ❌ Not running | Running natively instead |
| Nginx container | ❌ Not running | Not started |
| Full stack verification | ❌ Not performed | Not executed this session |

## Evidence Matrix

| Check | Status | Source |
|-------|--------|--------|
| docker-compose.yml exists | ✅ | `D:\Projects\MLLM_Geo_Ai\docker-compose.yml` |
| Dockerfile exists | ✅ | `D:\Projects\MLLM_Geo_Ai\Dockerfile` |
| nginx.conf exists | ✅ | `D:\Projects\MLLM_Geo_Ai\nginx.conf` |
| .dockerignore exists | ✅ | `D:\Projects\MLLM_Geo_Ai\.dockerignore` |
| Redis container running | ✅ | `docker compose ps` → Up (healthy) |
| FastAPI container running | ❌ | `docker compose ps` → not listed |
| Celery container running | ❌ | `docker compose ps` → not listed |
| Nginx container running | ❌ | `docker compose ps` → not listed |
| Full stack docker test | ❌ | Not executed this session |

## Conclusion

⚠️ **CONFIGURED but NOT VERIFIED** — All four Docker configuration files are present and properly structured. Redis is running in Docker (healthy, 17 hours uptime). However, the FastAPI application, Celery workers, and Nginx are running natively rather than in Docker containers. The full containerized stack was not tested end-to-end in this session. Two configuration issues were noted: `$HOME` variable not set (affecting GEE credential mount) and a database path typo (`mllm_goe_ai.db` vs `mllm_geo_ai.db`).
