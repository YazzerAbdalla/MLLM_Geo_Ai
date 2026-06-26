import io
import json
import math
import os
import re
import unicodedata
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from app.infrastructure import poi_cache
from app.infrastructure.poi_caches import refresh_all as refresh_aux_caches
from app.infrastructure.spatial_index import normalize_name, haversine_distance_m
from app.models.poi_upload import (
    CancelResponse,
    ImportResultV2,
    ImportStatistics,
    ParsedPOI,
    UploadPreviewResponse,
    ValidationErrorDetail,
    ValidationSummary,
    ValidationWarning,
)

PREVIEW_DIR = Path("data/temp/poi_preview")
PREVIEW_TTL_SECONDS = 7200
MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_CATEGORIES_PATH = "data/allowed_categories.json"
IMPORT_HISTORY_DIR = Path("logs/import_history")
NEAR_DISTANCE_M = 2.0

LAT_ALIASES = {"latitude", "lat"}
LON_ALIASES = {"longitude", "lng"}
REQUIRED_COLUMNS = {"name", "category", "place_type"}
REQUIRED_LAT = LAT_ALIASES
REQUIRED_LON = LON_ALIASES

TEMPLATE_HEADER = "name,category,place_type,lat,lng,address\n"


def generate_template_csv() -> str:
    return TEMPLATE_HEADER


def _load_allowed_categories() -> dict:
    if not os.path.exists(ALLOWED_CATEGORIES_PATH):
        return {"allowed": [], "aliases": {}}
    with open(ALLOWED_CATEGORIES_PATH, encoding="utf-8") as f:
        return json.load(f)


def parse_and_validate_csv(content: bytes) -> Tuple[List[ParsedPOI], ValidationSummary]:
    try:
        decoded = content.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("File must be UTF-8 encoded")

    try:
        df = pd.read_csv(io.StringIO(decoded))
    except Exception as e:
        raise ValueError(f"Could not parse CSV: {str(e)}")

    if df.empty:
        raise ValueError("Uploaded CSV is empty")

    provided_cols = set(df.columns.str.strip())
    missing_base = [c for c in REQUIRED_COLUMNS if c not in provided_cols]
    if missing_base:
        raise ValueError(f"Missing required columns: {', '.join(missing_base)}")

    lat_col = provided_cols & LAT_ALIASES
    lon_col = provided_cols & LON_ALIASES
    if not lat_col:
        raise ValueError(f"Missing latitude column. Expected one of: {', '.join(sorted(LAT_ALIASES))}")
    if not lon_col:
        raise ValueError(f"Missing longitude column. Expected one of: {', '.join(sorted(LON_ALIASES))}")
    lat_col_name = list(lat_col)[0]
    lon_col_name = list(lon_col)[0]

    errors: List[ValidationErrorDetail] = []
    warnings: List[ValidationWarning] = []
    parsed: List[ParsedPOI] = []

    address_col = "address" if "address" in provided_cols else None

    for idx, row in df.iterrows():
        row_num = idx + 2
        raw_name = row.get("name")
        raw_cat = row.get("category")
        raw_place = row.get("place_type")
        name_val = str(raw_name).strip() if pd.notna(raw_name) else ""
        cat_val = str(raw_cat).strip() if pd.notna(raw_cat) else ""
        place_val = str(raw_place).strip() if pd.notna(raw_place) else ""
        lat_val = row.get(lat_col_name)
        lon_val = row.get(lon_col_name)
        addr_val = str(row.get("address", "")).strip() if address_col and pd.notna(row.get("address")) else ""

        if not name_val:
            warnings.append(ValidationWarning(row=row_num, field="name", message="Empty value"))
        if not cat_val:
            warnings.append(ValidationWarning(row=row_num, field="category", message="Empty value"))
        if not place_val:
            warnings.append(ValidationWarning(row=row_num, field="place_type", message="Empty value"))

        try:
            lat = float(lat_val) if lat_val is not None and str(lat_val).strip() else None
        except (ValueError, TypeError):
            lat = None
        try:
            lon = float(lon_val) if lon_val is not None and str(lon_val).strip() else None
        except (ValueError, TypeError):
            lon = None

        if lat is None:
            errors.append(ValidationErrorDetail(row=row_num, field="latitude", value=str(lat_val), message="Empty or non-numeric latitude"))
        elif lat < -90 or lat > 90:
            errors.append(ValidationErrorDetail(row=row_num, field="latitude", value=lat, message="Latitude outside [-90, 90]"))

        if lon is None:
            errors.append(ValidationErrorDetail(row=row_num, field="longitude", value=str(lon_val), message="Empty or non-numeric longitude"))
        elif lon < -180 or lon > 180:
            errors.append(ValidationErrorDetail(row=row_num, field="longitude", value=lon, message="Longitude outside [-180, 180]"))

        if lat is not None and lon is not None and -90 <= lat <= 90 and -180 <= lon <= 180:
            parsed.append(ParsedPOI(
                row=row_num,
                name=name_val or "Unknown",
                category=cat_val or "Other",
                place_type=place_val or "Other",
                latitude=lat,
                longitude=lon,
                address=addr_val,
            ))

    duplicate_rows = _find_duplicate_rows(parsed)
    for dup_row in duplicate_rows:
        warnings.append(ValidationWarning(row=dup_row, field="(all)", message="Duplicate row in uploaded CSV"))

    total_rows = len(df)
    valid = len(errors) == 0

    return parsed, ValidationSummary(valid=valid, total_rows=total_rows, errors=errors, warnings=warnings)


def _find_duplicate_rows(parsed: List[ParsedPOI]) -> List[int]:
    seen = set()
    dup_rows = []
    for poi in parsed:
        key = (round(poi.latitude, 6), round(poi.longitude, 6), normalize_name(poi.name), normalize_name(poi.category), normalize_name(poi.place_type))
        if key in seen:
            dup_rows.append(poi.row)
        seen.add(key)
    return dup_rows


def _validate_categories(parsed_pois: List[ParsedPOI]) -> List[ValidationWarning]:
    rules = _load_allowed_categories()
    allowed = set(rules.get("allowed", []))
    aliases = rules.get("aliases", {})
    warnings = []
    for poi in parsed_pois:
        raw = poi.category.strip()
        if raw in aliases:
            mapped = aliases[raw]
            if mapped != raw:
                poi.category = mapped
                warnings.append(ValidationWarning(row=poi.row, field="category", message=f"Category '{raw}' auto-mapped to '{mapped}'"))
            continue
        if raw not in allowed:
            warnings.append(ValidationWarning(row=poi.row, field="category", message=f"Unknown category '{raw}'"))
    return warnings


def _compute_statistics(parsed_pois: List[ParsedPOI]) -> ImportStatistics:
    if not parsed_pois:
        return ImportStatistics(
            bbox=[0, 0, 0, 0],
            center=[0, 0],
            unique_categories=[],
            average_density=0.0,
            imported_area_deg=0.0,
        )
    lats = [p.latitude for p in parsed_pois]
    lons = [p.longitude for p in parsed_pois]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)
    area_deg = (max_lat - min_lat) * (max_lon - min_lon)
    lat_m = 111320
    lon_m = 111320 * math.cos(math.radians((min_lat + max_lat) / 2))
    area_m2 = (max_lat - min_lat) * lat_m * (max_lon - min_lon) * lon_m
    area_km2 = area_m2 / 1_000_000 if area_m2 > 0 else 1.0
    density = round(len(parsed_pois) / area_km2, 2) if area_km2 > 0 else 0.0
    cats = sorted(set(p.category for p in parsed_pois))
    return ImportStatistics(
        bbox=[min_lat, min_lon, max_lat, max_lon],
        center=[(min_lat + max_lat) / 2, (min_lon + max_lon) / 2],
        unique_categories=cats,
        average_density=density,
        imported_area_deg=round(area_deg, 6),
    )


def _category_counts(parsed_pois: List[ParsedPOI]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for p in parsed_pois:
        counts[p.category] = counts.get(p.category, 0) + 1
    return counts


def create_preview_session(parsed_pois: List[ParsedPOI], validation: ValidationSummary, statistics: ImportStatistics, features: Optional[dict] = None) -> str:
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    data = {
        "session_id": session_id,
        "created_at": now.isoformat(),
        "expires_at": None,
        "parsed_pois": [p.model_dump() for p in parsed_pois],
        "validation": validation.model_dump(),
        "statistics": statistics.model_dump(),
        "category_counts": _category_counts(parsed_pois),
        "features": features or {"type": "FeatureCollection", "features": []},
    }
    path = PREVIEW_DIR / f"{session_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return session_id


def _session_path(session_id: str) -> Path:
    return PREVIEW_DIR / f"{session_id}.json"


def load_preview_session(session_id: str) -> Optional[dict]:
    _cleanup_expired()
    path = _session_path(session_id)
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        return None
    created = datetime.fromisoformat(data["created_at"])
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    if (datetime.now(timezone.utc) - created).total_seconds() > PREVIEW_TTL_SECONDS:
        path.unlink(missing_ok=True)
        return None
    return data


def delete_preview_session(session_id: str) -> bool:
    path = _session_path(session_id)
    if not path.exists():
        return False
    path.unlink()
    return True


def cleanup_expired_previews() -> int:
    return _cleanup_expired()


def _cleanup_expired() -> int:
    count = 0
    if not PREVIEW_DIR.exists():
        return 0
    now = datetime.now(timezone.utc)
    for f in PREVIEW_DIR.glob("*.json"):
        try:
            with open(f, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            created = datetime.fromisoformat(data["created_at"])
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            if (now - created).total_seconds() > PREVIEW_TTL_SECONDS:
                f.unlink()
                count += 1
        except (json.JSONDecodeError, IOError, KeyError):
            f.unlink(missing_ok=True)
            count += 1
    return count


def _detect_preview_duplicates(parsed_pois: List[ParsedPOI]) -> Dict[int, str]:
    existing_df = poi_cache.get_poi_cache()
    if existing_df is None or existing_df.empty:
        return {}
    duplicates: Dict[int, str] = {}
    existing = existing_df.copy()
    existing["_norm_name"] = existing["name"].apply(lambda n: normalize_name(str(n)))
    for poi in parsed_pois:
        x, y = poi.longitude, poi.latitude
        norm_name = normalize_name(str(poi.name))
        exact_mask = (existing["X"].sub(x).abs() < 1e-6) & (existing["Y"].sub(y).abs() < 1e-6)
        if exact_mask.any():
            duplicates[poi.row] = "duplicate_coordinate"
            continue
        near_mask = existing.apply(
            lambda r: haversine_distance_m(r["Y"], r["X"], y, x) <= NEAR_DISTANCE_M,
            axis=1
        )
        near_matches = existing[near_mask]
        if not near_matches.empty:
            name_match = near_matches[near_matches["_norm_name"] == norm_name]
            if not name_match.empty:
                duplicates[poi.row] = "duplicate_poi"
            else:
                duplicates[poi.row] = "duplicate_coordinate"
    return duplicates


def build_preview_geojson(parsed_pois: List[ParsedPOI], validation: ValidationSummary, duplicates: Dict[int, str]) -> dict:
    features = []
    error_rows = {e.row for e in validation.errors}
    for poi in parsed_pois:
        row = poi.row
        status = duplicates.get(row, "new")
        if row in error_rows:
            validation_status = "invalid"
        elif any(w.row == row for w in validation.warnings):
            validation_status = "warning"
        else:
            validation_status = "valid"
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [poi.longitude, poi.latitude]},
            "properties": {
                "row": row,
                "name": poi.name,
                "category": poi.category,
                "place_type": poi.place_type,
                "address": poi.address or "",
                "status": status,
                "validation": validation_status,
            },
        })
    return {"type": "FeatureCollection", "features": features}


def build_preview_response(parsed_pois: List[ParsedPOI], validation: ValidationSummary) -> Tuple[UploadPreviewResponse, str]:
    cat_warnings = _validate_categories(parsed_pois)
    validation.warnings.extend(cat_warnings)
    stats = _compute_statistics(parsed_pois)
    counts = _category_counts(parsed_pois)
    dup_count = sum(1 for w in validation.warnings if w.field == "(all)")
    duplicates = _detect_preview_duplicates(parsed_pois)
    features = build_preview_geojson(parsed_pois, validation, duplicates)
    session_id = create_preview_session(parsed_pois, validation, stats, features)
    response = UploadPreviewResponse(
        session_id=session_id,
        validation=validation,
        parsed_pois=parsed_pois,
        category_counts=counts,
        total_uploaded=len(parsed_pois),
        duplicates_count=dup_count,
        statistics=stats,
        features=features,
    )
    return response, session_id


def _ensure_ai_metadata_columns(df: pd.DataFrame) -> pd.DataFrame:
    ai_cols = ["source", "import_batch_id", "created_at", "validated"]
    for col in ai_cols:
        if col not in df.columns:
            df[col] = None
    return df


def _apply_metadata(parsed: List[ParsedPOI], existing_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    batch_id = f"batch_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    now = datetime.now(timezone.utc).isoformat()
    for p in parsed:
        rows.append({
            "X": p.longitude,
            "Y": p.latitude,
            "osm_id": None,
            "name": p.name,
            "place_type": p.place_type,
            "category": p.category,
            "text_des": p.address or "",
            "label": 0,
            "source": "user_upload",
            "import_batch_id": batch_id,
            "created_at": now,
            "validated": True,
        })
    return pd.DataFrame(rows)


def _detect_duplicates(new_rows: pd.DataFrame, existing_df: pd.DataFrame) -> Tuple[pd.DataFrame, int, int]:
    from app.infrastructure.spatial_index import normalize_name, haversine_distance_m

    if existing_df.empty:
        return new_rows, 0, 0

    existing = existing_df.copy()
    existing["_norm_name"] = existing["name"].apply(lambda n: normalize_name(str(n)))

    imported_indices = []
    skipped_coord = 0
    skipped_poi = 0

    for idx, row in new_rows.iterrows():
        x, y = row["X"], row["Y"]
        norm_name = normalize_name(str(row.get("name", "")))

        exact_mask = (existing["X"].sub(x).abs() < 1e-6) & (existing["Y"].sub(y).abs() < 1e-6)
        if exact_mask.any():
            skipped_coord += 1
            continue

        near_mask = existing.apply(
            lambda r: haversine_distance_m(r["Y"], r["X"], y, x) <= NEAR_DISTANCE_M,
            axis=1
        )
        near_matches = existing[near_mask]

        if not near_matches.empty:
            name_match = near_matches[near_matches["_norm_name"] == norm_name]
            if name_match.empty:
                skipped_coord += 1
            else:
                skipped_poi += 1
            continue

        imported_indices.append(idx)

    return new_rows.loc[imported_indices].reset_index(drop=True) if imported_indices else pd.DataFrame(columns=new_rows.columns), skipped_coord, skipped_poi


def import_preview(session_id: str) -> ImportResultV2:
    session = load_preview_session(session_id)
    if session is None:
        raise ValueError("Preview session not found or expired")

    parsed_pois_data = session["parsed_pois"]
    statistics_data = session.get("statistics")
    statistics = ImportStatistics(**statistics_data) if statistics_data else None

    parsed_pois = [ParsedPOI(**p) for p in parsed_pois_data]
    existing_df = poi_cache.get_poi_cache()
    if existing_df is None:
        raise ValueError("POI cache is not loaded")

    existing_df = _ensure_ai_metadata_columns(existing_df.copy())

    new_df = _apply_metadata(parsed_pois, existing_df)

    imported_df, skipped_coord, skipped_poi = _detect_duplicates(new_df, existing_df)

    imported_count = len(imported_df)
    skipped_count = skipped_coord + skipped_poi

    if imported_count > 0:
        final_df = pd.concat([existing_df, imported_df], ignore_index=True)
        tmp_path = "data/raw/project.csv.tmp"
        final_df.to_csv(tmp_path, index=False)
        os.replace(tmp_path, "data/raw/project.csv")
        poi_cache.reload_poi_cache("data/raw/project.csv")
        refresh_aux_caches("data/raw/project.csv")

    delete_preview_session(session_id)

    _write_audit_log({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "total_submitted": len(parsed_pois),
        "imported_count": imported_count,
        "skipped_count": skipped_count,
        "skipped_coordinates": skipped_coord,
        "skipped_pois": skipped_poi,
        "category_counts": _category_counts(parsed_pois),
        "statistics": statistics.model_dump() if statistics else None,
    })

    msg = f"{imported_count} POIs imported successfully."
    if skipped_count > 0:
        parts = []
        if skipped_coord > 0:
            parts.append(f"{skipped_coord} duplicate coordinates")
        if skipped_poi > 0:
            parts.append(f"{skipped_poi} duplicate POIs")
        msg += f" {skipped_count} skipped ({', '.join(parts)})."

    return ImportResultV2(
        imported_count=imported_count,
        skipped_count=skipped_count,
        duplicate_coordinates=skipped_coord,
        duplicate_pois=skipped_poi,
        message=msg,
        statistics=statistics,
    )


def cancel_preview(session_id: str) -> CancelResponse:
    if not delete_preview_session(session_id):
        raise ValueError("Preview session not found")
    return CancelResponse(
        session_id=session_id,
        status="cancelled",
        message="Preview session deleted. No data was imported.",
    )


def _write_audit_log(data: dict) -> str:
    os.makedirs(IMPORT_HISTORY_DIR, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    filename = IMPORT_HISTORY_DIR / f"{timestamp}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return str(filename)
