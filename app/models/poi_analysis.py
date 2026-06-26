from pydantic import BaseModel, Field
from typing import Optional, List, Literal


class ReverseGeocoding(BaseModel):
    area_name: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None


class TopCategoryItem(BaseModel):
    category: str
    count: int


class CentroidGeometry(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: list


class PoiAnalysisStats(BaseModel):
    total_pois: int
    area_m2: float
    area_km2: float
    perimeter_m: float
    poi_density: float
    centroid: Optional[CentroidGeometry] = None
    category_counts: dict
    top_categories: List[TopCategoryItem]
    reverse_geocoding: Optional[ReverseGeocoding] = None
    returned_pois: int
    truncated: bool


class PoiListItem(BaseModel):
    name: str
    category: str
    place_type: str
    coordinates: list


class PoiAnalysisResponse(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: List[PoiListItem]
    analysis: PoiAnalysisStats
