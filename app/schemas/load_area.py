"""
 * Load Area Request Schema with validation.
"""
from pydantic import BaseModel, field_validator
from typing import Optional, List


class LoadAreaRequest(BaseModel):
    bbox: Optional[List[float]] = None
    place_name: Optional[str] = None
    grid_size: int = 500
    modalities: List[str] = ["poi", "image", "graph"]

    @field_validator("grid_size")
    @classmethod
    def validate_grid_size(cls, v):
        if v not in [200, 500, 1000]:
            raise ValueError("grid_size must be 200, 500, or 1000")
        return v

    @field_validator("bbox")
    @classmethod
    def validate_bbox(cls, v):
        if v is not None and len(v) != 4:
            raise ValueError("bbox must have exactly 4 values: [min_lon, min_lat, max_lon, max_lat]")
        return v