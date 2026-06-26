from pydantic import BaseModel, Field
from typing import List, Literal, Optional


class POIHeatmapProperties(BaseModel):
    osm_id: Optional[str] = None
    name: str = "Unknown"
    category: str = "Unknown"
    place_type: str = "Unknown"
    label: int = 0
    weight: int = 1


class POIHeatmapFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    geometry: dict = Field(default={"type": "Point", "coordinates": [0.0, 0.0]})
    properties: POIHeatmapProperties


class POIHeatmapMetadata(BaseModel):
    total_pois: int


class POIHeatmapResponse(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    metadata: POIHeatmapMetadata
    features: List[POIHeatmapFeature]


class InternalPOIHeatmapMetadata(BaseModel):
    total_pois: int
    source: str = "project.csv"


class InternalPOIHeatmapResponse(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    metadata: InternalPOIHeatmapMetadata
    features: List[POIHeatmapFeature]
