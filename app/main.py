"""
 * Main entry point for the MLLM-Geo-AI-App.
 * Sets up the FastAPI application and includes the API routes.
 """
from fastapi import FastAPI
from contextlib import asynccontextmanager
import ee
import os
from dotenv import load_dotenv
from app.interfaces.api import router as api_router
from app.infrastructure.db import engine, Base
from app.infrastructure.redis_store import RedisJobStore
from app.models.grid import Grid
from app.models.job import Job

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
     * Lifespan context manager for FastAPI.
     * Initializes Google Earth Engine and creates DB tables on startup.
     """
    Base.metadata.create_all(bind=engine)

    try:
        redis_store = RedisJobStore()
        redis_store.r.ping()
        print("Redis connected OK")
    except Exception as e:
        print(f"WARNING: Redis connection failed: {e}")
        print("NOTE: Redis is required for async job tracking.")
        print("      Some features may be limited without Redis.")
        print("      See docs/project_status.md for details.")

    project_id = os.getenv('EARTH_ENGINE_PROJECT')
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

# Include the routes
app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
def health_check():
    """
    * Health check endpoint to verify the application status.
    *
    * @returns {dict} Status and app name
    """
    return {"status": "ok", "app": "MLLM-Geo-AI-App"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
