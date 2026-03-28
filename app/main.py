"""
 * Main entry point for the MLLM-Geo-AI-App.
 * Sets up the FastAPI application and includes the API routes.
 """
from fastapi import FastAPI
from app.interfaces.api import router as api_router

app = FastAPI(title="MLLM-Geo-AI-App", description="Spatial Grid Classification with MLLM Embeddings")

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
