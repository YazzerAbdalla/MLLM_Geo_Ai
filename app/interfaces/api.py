"""
 * API interface for the MLLM-Geo-AI application.
 * Defines the HTTP endpoints for interacting with the classification pipeline.
 """
from fastapi import APIRouter, HTTPException
from app.application.use_cases import run_classification_pipeline
import os

router = APIRouter()

@router.post("/classify")
async def classify_geo_data():
    """
    * Triggers the MLLM-Geo-AI pipeline using project.csv data.
    * Returns binned classification results by 500m grid cells.
    *
    * @returns {dict} Success status and classification results
    """
    csv_path = os.path.join(os.getcwd(), 'assets', 'project.csv')
    
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail=f"project.csv not found at {csv_path}")
    
    try:
        # Run the full pipeline
        results = run_classification_pipeline(csv_path)
        return {"status": "success", "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
