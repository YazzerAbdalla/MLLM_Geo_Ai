"""
 * API interface for the MLLM-Geo-AI application.
 * Defines the HTTP endpoints for interacting with the multi-modal classification pipeline.
 """
from fastapi import APIRouter, HTTPException, Response, UploadFile, File, Form
from fastapi.responses import JSONResponse , StreamingResponse , FileResponse
from pydantic import BaseModel
from typing import List, Optional, Literal
from celery_app import celery_app
import os
import io
import uuid
import geopandas as gpd
import json

from app.infrastructure.job_store import job_store
from app.application.fusion_service import MultiModalClassificationUseCase
from app.application.export_service import ExportService
from app.infrastructure.satellite_loader import SatelliteImageLoader
from app.infrastructure.road_network import RoadNetworkLoader
from app.domain.spatial_service import generate_grid
from app.interfaces.helpers import _extract_graph_from_grid_data, _graph_to_geojson
from app.application.evaluation_service import evaluate_job, export_evaluation_csv

router = APIRouter()

# Async task import guard - prevents startup crash
try:
    from tasks.load_area import load_area_task
    from tasks.classify import classify_task
    TASKS_AVAILABLE = True
except ImportError:
    TASKS_AVAILABLE = False

# --- Pydantic Models ---
class LoadAreaRequest(BaseModel):
    bbox: Optional[List[float]] = None
    place_name: Optional[str] = None
    grid_size: int = 500
    modalities: List[str] = ["poi", "image", "graph"]

class ClassifyRequest(BaseModel):
    grid_id: str
    modalities: List[str] = ["poi", "image", "graph"]
    fusion_method: str = "concat"
    model_version: Optional[str] = "v1.0"


class QueryRequest(BaseModel):
    question: str
    grid_id: str

class MLLMTrainRequest(BaseModel):
    model_name: str = "tiny-llm"
    dataset_path: str
    epochs: int = 3
    batch_size: int = 8

# --- Endpoints ---

@router.post("/load-area", status_code=202)
async def load_area(request: LoadAreaRequest):
    if not TASKS_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail={
                "error": "Async task pipeline not yet implemented",
                "message": "This feature is planned for future implementation",
                "docs": "See docs/project_status.md for system status",
                "workaround": "Use a smaller synchronous workflow or wait for future release"
            }
        )

    job_id = job_store.create_job("load")

    bbox = request.bbox
    if not bbox:
        bbox = [31.10, 29.90, 31.30, 30.10]

    min_x, min_y, max_x, max_y = bbox
    from app.domain.spatial_service import generate_grid
    grid_gdf = generate_grid((min_x, min_y, max_x, max_y), cell_size_m=request.grid_size)
    num_cells = len(grid_gdf)

    if num_cells > 500:
        raise HTTPException(
            status_code=413,
            detail=f"Area too large: {num_cells} cells exceed the 500-cell limit. Zoom in or increase grid_size."
        )

    from tasks.load_area import load_area_task
    result = load_area_task.apply_async(
       args=[job_id, bbox, request.grid_size, request.modalities]
    )

    job_store.update_job(
    job_id,
    celery_task_id=result.id,
    status="queued"
    )

    return {
        "job_id": job_id,
        "status_url": f"/api/v1/area-status/{job_id}",
        "websocket_url": f"ws://localhost:8000/api/v1/ws/progress/{job_id}"
    }

@router.get("/area-status/{job_id}")
async def get_area_status(job_id: str):
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    response = {
        "job_id": job["id"],
        "status": job["status"],
        "step": job["step"],
        "progress": job["progress"],
        "error": job["error"]
    }
    if job["status"] == "completed":
        response["grid_id"] = job.get("grid_id")
        response["num_cells"] = job.get("num_cells", 0)
        response["geojson_preview_url"] = f"/api/v1/grid/{job.get('grid_id')}/preview"
        
    return response

@router.get("/grid/{grid_id}/preview")
async def get_grid_preview(grid_id: str):
    grid_data = job_store.get_grid(grid_id)
    if not grid_data:
        raise HTTPException(status_code=404, detail="Grid not found")

    geojson_str = grid_data["gdf"].to_json()
    return Response(content=geojson_str, media_type="application/geo+json")

@router.post("/classify", status_code=202)
async def classify_grid(request: ClassifyRequest):
    if not TASKS_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail={
                "error": "Async task pipeline not yet implemented",
                "message": "This feature is planned for future implementation",
                "docs": "See docs/project_status.md for system status",
                "workaround": "Use a smaller synchronous workflow or wait for future release"
            }
        )

    job_id = job_store.create_job("classify")
    from tasks.classify import classify_task
    result = classify_task.apply_async(
        args=[job_id, request.grid_id, request.modalities, request.fusion_method]
    )

    job_store.update_job(
    job_id,
    celery_task_id=result.id,
    status="queued"
    )

    return {
        "job_id": job_id,
        "status_url": f"/api/v1/classify-status/{job_id}",
        "websocket_url": f"ws://localhost:8000/api/v1/ws/progress/{job_id}"
    }

@router.get("/classify-status/{job_id}")
async def get_classify_status(job_id: str):
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    response = {
        "job_id": job["id"],
        "status": job["status"],
        "step": job["step"],
        "progress": job["progress"],
        "error": job["error"]
    }
    if job["status"] == "completed":
        response["result_url"] = f"/api/v1/classification-result/{job_id}"
        
    return response

@router.get("/classification-result/{job_id}")
async def get_classification_result(job_id: str):
    job = job_store.get_job(job_id)
    if not job or job["status"] != "completed":
        raise HTTPException(status_code=404, detail="Job not found or not completed")

    result_path = f"data/results/{job_id}.geojson"
    if not os.path.exists(result_path):
        results = job.get("result_data", [])
        return {"type": "FeatureCollection", "features": results}

    with open(result_path) as f:
        content = f.read()
    return Response(content=content, media_type="application/geo+json")

@router.get("/export/{job_id}")
async def export_results(job_id: str, format: str = "geojson"):
    job = job_store.get_job(job_id)
    if not job or job["status"] != "completed":
        raise HTTPException(status_code=404, detail="Job not found or not completed")

    result_path = f"data/results/{job_id}.geojson"
    if not os.path.exists(result_path):
        raise HTTPException(status_code=404, detail="Result file not found")

    svc = ExportService()
    if format == "geojson":
        data = svc.to_geojson(result_path)
        media_type = "application/geo+json"
        filename = f"{job_id}.geojson"
    elif format == "csv":
        data = svc.to_csv(result_path)
        media_type = "text/csv"
        filename = f"{job_id}.csv"
    elif format == "shapefile":
        data = svc.to_shapefile(result_path)
        media_type = "application/zip"
        filename = f"{job_id}_shapefile.zip"
    else:
        raise HTTPException(status_code=400, detail="format must be geojson, csv, or shapefile")

    return Response(
        content=data,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.get("/thumbnails/{grid_id}/{cell_id}.jpg")
async def get_thumbnail(grid_id: str, cell_id: str):
    png_path = f"data/sat_images/cell_{cell_id}.png"
    if not os.path.exists(png_path):
        raise HTTPException(status_code=404, detail="Thumbnail not found")

    from PIL import Image
    import io
    img = Image.open(png_path).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return Response(content=buf.getvalue(), media_type="image/jpeg")


# End Point -1 DELETE /api/v1/jobs/{job_id}
@router.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    job = job_store.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    task_id = job.get("celery_task_id")

    if task_id:
        celery_app.control.revoke(
            task_id,
            terminate=True,
            signal="SIGTERM"
        )

    job_store.update_job(
        job_id,
        status="cancelled",
        step="cancelled",
        progress=0,
        error=None
    )

    return {
        "job_id": job_id,
        "status": "cancelled",
        "message": "Job cancelled successfully"
    }

# End Point -2 GET /api/v1/grid/{grid_id}/graph-topology
@router.get("/grid/{grid_id}/graph-topology")
async def get_graph_topology(grid_id: str):
    try:
        grid_data = job_store.get_grid(grid_id)
    except NotImplementedError:
        raise HTTPException(
            status_code=501,
            detail="Grid storage is not implemented yet."
        )

    if not grid_data:
        raise HTTPException(status_code=404, detail="Grid not found")

    graph = _extract_graph_from_grid_data(grid_data)

    if graph is None:
        raise HTTPException(
            status_code=404,
            detail="Road network graph not available for this grid"
        )

    geojson = _graph_to_geojson(graph)

    if not geojson:
        raise HTTPException(
            status_code=404,
            detail="Could not build graph topology GeoJSON"
        )

    return JSONResponse(content=geojson)

# End Point -3 POST /api/v1/evaluate
@router.post("/evaluate")
async def evaluate(job_id: str = Form(...), ground_truth_file: UploadFile = File(...)):
    result = await evaluate_job(job_id, ground_truth_file)
    return JSONResponse(content=result)

# End Point -4 GET /api/v1/evaluate/{job_id}/export
@router.get("/evaluate/{job_id}/export")
async def export_evaluation(job_id: str):
    csv_bytes = export_evaluation_csv(job_id)
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="evaluation_{job_id}.csv"'}
    )

### helper for End-Point-5
@router.get("/mllm/train-status/{job_id}")
async def get_train_status(job_id: str):

    job = job_store.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    return {
        "job_id": job["id"],
        "status": job["status"],
        "step": job["step"],
        "progress": job["progress"],
        "error": job["error"]
    }
# End Point -5 POST /api/v1/mllm/train
@router.post("/mllm/train", status_code=202)
async def train_mllm(request: MLLMTrainRequest):

    job_id = job_store.create_job("mllm_train")

    from tasks.train_mllm import train_mllm_task

    result = train_mllm_task.apply_async(
        args=[
            job_id,
            request.model_name,
            request.dataset_path,
            request.epochs,
            request.batch_size
        ]
    )

    job_store.update_job(
        job_id,
        celery_task_id=result.id,
        status="queued"
    )

    return {
        "job_id": job_id,
        "status": "queued",
        "status_url": f"/api/v1/mllm/train-status/{job_id}",
        "websocket_url": f"ws://localhost:8000/api/v1/ws/progress/{job_id}"
    }

# End Point -6 POST /api/v1/query (Digital Twin NL)
@router.post("/query")
async def natural_language_query(body: QueryRequest):
    raise HTTPException(
        status_code=501,
        detail="Natural language query is planned for v2 and not yet implemented."
    )
