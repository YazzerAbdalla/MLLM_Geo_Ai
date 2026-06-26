from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal, Any


class ParsedPOI(BaseModel):
    row: int
    name: str
    category: str
    place_type: str
    latitude: float
    longitude: float
    address: Optional[str] = ""


class ValidationWarning(BaseModel):
    row: int
    field: str
    message: str


class ValidationErrorDetail(BaseModel):
    row: int
    field: str
    value: Any = None
    message: str


class ValidationSummary(BaseModel):
    valid: bool
    total_rows: int
    errors: List[ValidationErrorDetail] = []
    warnings: List[ValidationWarning] = []


class ImportStatistics(BaseModel):
    bbox: List[float]
    center: List[float]
    unique_categories: List[str]
    average_density: float
    imported_area_deg: float


class UploadPreviewResponse(BaseModel):
    session_id: str
    validation: ValidationSummary
    parsed_pois: List[ParsedPOI]
    category_counts: Dict[str, int]
    total_uploaded: int
    duplicates_count: int
    statistics: Optional[ImportStatistics] = None
    features: dict = {"type": "FeatureCollection", "features": []}


class ImportResultV2(BaseModel):
    imported_count: int
    skipped_count: int
    duplicate_coordinates: int
    duplicate_pois: int
    warnings: List[ValidationWarning] = []
    message: str
    statistics: Optional[ImportStatistics] = None


class CancelResponse(BaseModel):
    session_id: str
    status: Literal["cancelled"]
    message: str
