"""
 * API interface for the MLLM-Geo-AI application.
 * Defines the HTTP endpoints for interacting with the multi-modal classification pipeline.
 """
from fastapi import APIRouter, HTTPException, Response, UploadFile, File, Form, Query, status, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse , StreamingResponse , FileResponse
from pydantic import BaseModel
from typing import List, Optional, Literal
from celery_app import celery_app

from app.infrastructure.job_store import job_store
from app.application.fusion_service import MultiModalClassificationUseCase
from app.application.export_service import ExportService
from app.infrastructure.satellite_loader import SatelliteImageLoader
from app.infrastructure.road_network import RoadNetworkLoader
from app.domain.spatial_service import generate_grid
from app.interfaces.helpers import _extract_graph_from_grid_data, _graph_to_geojson, validate_ground_truth_file
from app.application.evaluation_service import evaluate_job, export_evaluation_csv
from app.application.poi_service import get_poi_heatmap
from app.application.internal_poi_service import get_all_pois_heatmap
from app.application.poi_analysis_service import analyze_poi_area
from app.models.poi import POIHeatmapResponse, InternalPOIHeatmapResponse
from app.models.poi_analysis import PoiAnalysisResponse

import os,io,uuid,json
import geopandas as gpd
from app.interfaces.websocket_manager import manager

router = APIRouter()

# Async task import guard - prevents startup crash
try:
    from tasks.load_area import load_area_task
    from tasks.classify import classify_task
    from tasks.train_mllm import train_mllm_task
    TASKS_AVAILABLE = True
except ImportError:
    TASKS_AVAILABLE = False

# --- Pydantic Models ---
class LoadAreaRequest(BaseModel):
    bbox: Optional[List[float]] = None
    place_name: Optional[str] = None
    area_geometry: Optional[dict] = None
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
    learning_rate: float = 1e-3

class PoiAnalysisRequest(BaseModel):
    geometry: dict
    include_location: bool = False

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

    from app.domain.spatial_service import generate_grid

    # Calculate cell count BEFORE expensive grid generation (DEF-007)
    if request.area_geometry:
        from shapely.geometry import shape
        try:
            poly = shape(request.area_geometry)
            min_x, min_y, max_x, max_y = poly.bounds
            bbox = [min_x, min_y, max_x, max_y]
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid area_geometry: {str(e)}")
    else:
        bbox = request.bbox
        if not bbox:
            bbox = [31.10, 29.90, 31.30, 30.10]
        min_x, min_y, max_x, max_y = bbox

    # Estimate cell count before generating grid
    import math
    cell_deg = request.grid_size / 111000.0
    est_cols = int(math.ceil((max_x - min_x) / cell_deg))
    est_rows = int(math.ceil((max_y - min_y) / cell_deg))
    est_cells = est_cols * est_rows
    if est_cells > 500:
        raise HTTPException(
            status_code=413,
            detail=f"Area too large: estimated {est_cells} cells exceed the 500-cell limit. Zoom in or increase grid_size."
        )

    if request.area_geometry:
        grid_gdf = generate_grid((min_x, min_y, max_x, max_y), cell_size_m=request.grid_size)
        grid_gdf = grid_gdf[grid_gdf.geometry.intersects(poly)]
    else:
        grid_gdf = generate_grid((min_x, min_y, max_x, max_y), cell_size_m=request.grid_size)

    num_cells = len(grid_gdf)

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
        grid_id = job.get("grid_id")
        response["grid_id"] = grid_id

        # Query Grid SQLite table for authoritative num_cells (DEF-013)
        from app.infrastructure.db import SessionLocal
        from app.models.grid import Grid
        try:
            db = SessionLocal()
            db_grid = db.query(Grid).filter(Grid.id == grid_id).first()
            if db_grid and db_grid.num_cells is not None:
                response["num_cells"] = db_grid.num_cells
            else:
                response["num_cells"] = job.get("num_cells", 0)
            db.close()
        except Exception:
            response["num_cells"] = job.get("num_cells", 0)

        response["geojson_preview_url"] = f"/api/v1/grid/{grid_id}/preview"
        
    return response

@router.websocket("/ws/progress/{job_id}")
async def websocket_progress_endpoint(websocket: WebSocket, job_id: str):
    job = job_store.get_job(job_id)
    if not job:
        await websocket.close(code=4004, reason="Job not found")
        return

    await manager.connect(websocket, job_id)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, job_id)

@router.get("/grid/{grid_id}/preview")
async def get_grid_preview(grid_id: str):
    grid_data = job_store.get_grid(grid_id)
    if not grid_data:
        raise HTTPException(status_code=404, detail="Grid not found")

    geojson_str = grid_data["gdf"].to_json()
    return Response(content=geojson_str, media_type="application/geo+json")

@router.get("/grid/{grid_id}/details")
async def get_grid_details(grid_id: str):
    grid_data = job_store.get_grid(grid_id)
    if not grid_data:
        raise HTTPException(status_code=404, detail="Grid not found")

    gdf = grid_data["gdf"]
    bbox = grid_data.get("bbox", [])

    cell_count = len(gdf)
    road_density = gdf["total_length"].mean() if "total_length" in gdf.columns else 0.0

    poi_count = 0
    if "poi_count" in gdf.columns:
        poi_count = int(gdf["poi_count"].sum())

    nodes = 0
    if "node_count" in gdf.columns:
        nodes = int(gdf["node_count"].sum())

    return {
        "grid_id": grid_id,
        "bbox": bbox,
        "cell_count": cell_count,
        "road_density": float(road_density),
        "poi_count": poi_count,
        "graph_stats": {
            "nodes": nodes,
            "edges": 0
        }
    }

@router.get("/grid/{grid_id}/pois")
async def get_grid_pois(grid_id: str):
    import os
    grid_data = job_store.get_grid(grid_id)
    if not grid_data:
        raise HTTPException(status_code=404, detail="Grid not found")

    pois_path = f"data/raw/pois_{grid_id}.geojson"
    if os.path.exists(pois_path):
        import geopandas as gpd
        pois_gdf = gpd.read_file(pois_path)
        pois = []
        for i, row in pois_gdf.iterrows():
            pois.append({
                "id": str(i),
                "name": row.get("name", "Unknown"),
                "category": row.get("amenity", "Unknown"),
                "lat": row.geometry.y,
                "lng": row.geometry.x
            })
        return pois
    return []


@router.get(
    "/grid/{grid_id}/poi-heatmap",
    response_model=POIHeatmapResponse,
    summary="Get POI heatmap as GeoJSON",
    description="Returns POI data filtered by grid bounding box, optimized for MapLibre HeatmapLayer.",
    responses={
        200: {"content": {"application/geo+json": {}}, "description": "POI heatmap GeoJSON"},
        404: {"description": "Grid not found"}
    }
)
async def get_grid_poi_heatmap(grid_id: str):
    result = get_poi_heatmap(grid_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Grid not found")
    return JSONResponse(content=result, media_type="application/geo+json")


@router.get(
    "/internal/poi-heatmap",
    response_model=InternalPOIHeatmapResponse,
    summary="Get all POIs as GeoJSON (internal)",
    description="Returns every POI from project.csv without grid filtering. For internal visualization.",
    responses={
        200: {"content": {"application/geo+json": {}}, "description": "Full POI heatmap GeoJSON"},
    }
)
async def get_internal_poi_heatmap():
    result = get_all_pois_heatmap()
    return JSONResponse(content=result, media_type="application/geo+json")


@router.post(
    "/internal/poi-analysis",
    response_model=PoiAnalysisResponse,
    summary="Analyze POIs within a drawn polygon",
    description="Returns spatial statistics for POIs inside a GeoJSON Polygon using the cached project.csv dataset.",
    responses={
        200: {"model": PoiAnalysisResponse, "description": "POI analysis results"},
        400: {"description": "Invalid polygon or geometry"}
    }
)
async def poi_analysis(request: PoiAnalysisRequest):
    try:
        result = analyze_poi_area(
            geometry=request.geometry,
            include_location=request.include_location
        )
        return JSONResponse(content=result, media_type="application/json")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

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

    if not request.modalities:
        raise HTTPException(
            status_code=400,
            detail="At least one modality required. Use ['poi'], ['image'], ['graph'], or a combination."
        )

    # Validate grid exists before queueing (DEF-008)
    grid_data = job_store.get_grid(request.grid_id)
    if not grid_data:
        raise HTTPException(
            status_code=404,
            detail=f"Grid not found: {request.grid_id}"
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
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] == "failed":
        raise HTTPException(status_code=400, detail="Cannot export: classification job failed")
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Cannot export: job status is '{job['status']}' (must be 'completed')")

    result_path = f"data/results/{job_id}.geojson"
    if not os.path.exists(result_path):
        # Try fallback: check result_data in job
        result_data = job.get("result_data")
        if result_data:
            os.makedirs("data/results", exist_ok=True)
            with open(result_path, "w") as f:
                json.dump({"type": "FeatureCollection", "features": result_data}, f)
        else:
            raise HTTPException(status_code=404, detail="Result file not found and no result data available")

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
async def get_graph_topology(
    grid_id: str,
    max_nodes: int = Query(500, ge=1, le=5000),
    simplify: bool = Query(True),
):
    try:
        grid_data = job_store.get_grid(grid_id)
    except NotImplementedError:
        raise HTTPException(
            status_code=501,
            detail="Grid storage is not implemented yet."
        )

    if not grid_data:
        raise HTTPException(status_code=404, detail="Grid not found")

    graph = _extract_graph_from_grid_data(
        grid_data,
        max_nodes=max_nodes,
        simplify=simplify,
    )

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
    try:
        await validate_ground_truth_file(ground_truth_file)

        result = await evaluate_job(job_id, ground_truth_file)
        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}"
        )

# End Point -4 GET /api/v1/evaluate/{job_id}/export FOR  End Point -3
@router.get("/evaluate/{job_id}/export")
async def export_evaluation(job_id: str):
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.get("status") != "completed":
        raise HTTPException(
            status_code=400,
            detail="Evaluation is not completed yet."
        )

    csv_bytes = export_evaluation_csv(job_id)

    if not csv_bytes:
        raise HTTPException(
            status_code=404,
            detail="No evaluation data available for export."
        )

    if isinstance(csv_bytes, str):
        csv_bytes = csv_bytes.encode("utf-8")

    return StreamingResponse(
        iter([csv_bytes]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename=\"evaluation_{job_id}.csv\"'
        }
    )

### GET for End-Point-5
@router.get("/mllm/train-status/{job_id}")
async def get_train_status(job_id: str):
    job = job_store.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    response = {
        "job_id": job["id"],
        "status": job["status"],
        "step": job["step"],
        "progress": job["progress"],
        "error": job["error"]
    }

    if job["status"] == "completed":
        response["result_url"] = job.get("result_url")

    return response
# End Point -5 POST /api/v1/mllm/train
@router.post("/mllm/train", status_code=202)
async def train_mllm(request: MLLMTrainRequest):
    if not TASKS_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Async task pipeline is not available."
        )

    # Validate dataset BEFORE queueing
    if not request.dataset_path:
        raise HTTPException(status_code=400, detail="dataset_path is required")
    if not os.path.exists(request.dataset_path):
        raise HTTPException(
            status_code=400,
            detail=f"Dataset not found: {request.dataset_path}"
        )
    valid_extensions = (".csv", ".json", ".geojson")
    if not request.dataset_path.lower().endswith(valid_extensions):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported dataset format. Supported: {valid_extensions}"
        )
    if request.epochs < 1 or request.epochs > 100:
        raise HTTPException(status_code=400, detail="epochs must be between 1 and 100")
    if request.batch_size < 1 or request.batch_size > 1024:
        raise HTTPException(status_code=400, detail="batch_size must be between 1 and 1024")

    job_id = job_store.create_job("mllm_train")

    from tasks.train_mllm import train_mllm_task

    result = train_mllm_task.apply_async(
        args=[
            job_id,
            request.model_name,
            request.dataset_path,
            request.epochs,
            request.batch_size,
            request.learning_rate,
        ]
    )

    job_store.update_job(
        job_id,
        celery_task_id=result.id,
        status="queued",
        step="queued",
        progress=0.0
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
    if not body.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    grid_data = job_store.get_grid(body.grid_id)
    if not grid_data:
        raise HTTPException(status_code=404, detail="Grid not found")

    return {
        "answer": f"This is a stub answer for your query: '{body.question}' regarding grid {body.grid_id}.",
        "query_type": "general",
        "confidence": 0.85
    }
