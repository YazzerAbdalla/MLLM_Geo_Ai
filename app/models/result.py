from pydantic import BaseModel, Field
from typing import List, Dict, Tuple, Optional, Any, Literal

class Confidences(BaseModel):
    residential: float
    commercial: float
    industrial: float

class CellResult(BaseModel):
    cell_id: str
    dominant_class: Literal["Residential", "Commercial", "Industrial"]
    confidence: float
    confidences: Confidences
    poi_top_categories: List[str] = Field(default_factory=list)
    road_density: float = 0.0
    node_count: int = 0
    degree_centrality: float = 0.0
    clustering_coeff: float = 0.0
    total_road_length_m: float = 0.0
    graph_embedding_norm: float = 0.0
    text_embedding_norm: float = 0.0
    geometry: Dict[str, Any]
    centroid: Tuple[float, float]
    satellite_thumbnail_url: Optional[str] = None
