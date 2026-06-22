"""
 * Main entry point for the MLLM-Geo-AI-App.
 *
 * Sets up the FastAPI application and includes the API routes.
"""


from contextlib import asynccontextmanager
from pathlib import Path

import ee,os
from dotenv import load_dotenv
from fastapi import FastAPI

from app.interfaces.api import router as api_router
from app.infrastructure.db import engine, Base
from app.infrastructure.redis_store import RedisJobStore
from app.infrastructure.job_store import _redis_store
from app.models.grid import Grid
from app.models.job import Job
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

# --------------------------------------------------
# Startup resources
# --------------------------------------------------
REQUIRED_ROAD_GRAPH = Path("data/raw/roads.graphml")


def check_startup_resources():
    """
    Fail fast if critical startup resources are missing.
    """
    # Redis
    redis_store = RedisJobStore(optional=False)
    redis_store.r.ping()
    print("Redis connected OK")

    # Road graph
    if not REQUIRED_ROAD_GRAPH.exists():
        raise RuntimeError(
            f"Missing required road graph file: {REQUIRED_ROAD_GRAPH}"
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI.
    Initializes resources on startup and disposes DB engine on shutdown.
    """
    Base.metadata.create_all(bind=engine)

    # Startup checks
    try:
        check_startup_resources()
        print("Startup checks passed")
    except Exception as e:
        print(f"Startup check failed: {e}")
        raise

    # Earth Engine
    project_id = os.getenv("EARTH_ENGINE_PROJECT")
    if project_id:
        try:
            ee.Initialize(project=project_id)
            print(f"Initialized Earth Engine with project: {project_id}")
        except Exception as e:
            print(f"Failed to initialize Earth Engine: {e}")
    else:
        print("WARNING: EARTH_ENGINE_PROJECT not set in .env. GEE features will fail.")

    yield
    engine.dispose()


app = FastAPI(
    title="MLLM-Geo-AI-App",
    description="Spatial Grid Classification with Multi-Modal Fusion",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite
        "http://127.0.0.1:5173",
        "http://localhost:8080",  # Vite
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health_check():
    redis_ok = _redis_store.is_available()

    return {
        "status": "ok" if redis_ok else "degraded",
        "app": "MLLM-Geo-AI-App",
        "redis": "ok" if redis_ok else "down",
        "job_store_mode": "redis" if redis_ok else "memory_fallback",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)