import logging
import pandas as pd
from typing import Optional
from app.infrastructure.job_store import job_store
from app.infrastructure import poi_cache as _poi_cache

logger = logging.getLogger(__name__)


def get_poi_heatmap(grid_id: str) -> Optional[dict]:
    grid_data = job_store.get_grid(grid_id)
    if not grid_data:
        return None

    bbox = grid_data.get("bbox")
    if not bbox or len(bbox) != 4:
        return {
            "type": "FeatureCollection",
            "metadata": {"total_pois": 0},
            "features": []
        }

    df = _poi_cache.get_poi_cache()
    if df is None or df.empty:
        logger.info("grid_id=%s total_before=0 total_after=0 (no cache)", grid_id)
        return {
            "type": "FeatureCollection",
            "metadata": {"total_pois": 0},
            "features": []
        }

    total_before = len(df)

    df = df.dropna(subset=["X", "Y"])

    df = df[
        (df["X"] >= -180) &
        (df["X"] <= 180) &
        (df["Y"] >= -90) &
        (df["Y"] <= 90)
    ]

    null_mask = df["osm_id"].isna()
    df = pd.concat([
        df[~null_mask].drop_duplicates(subset=["osm_id"], keep="first"),
        df[null_mask]
    ])

    min_lon, min_lat, max_lon, max_lat = bbox
    df = df[(df["X"] >= min_lon) & (df["X"] <= max_lon) &
            (df["Y"] >= min_lat) & (df["Y"] <= max_lat)]

    total_after = len(df)

    logger.info("grid_id=%s total_before=%d total_after=%d",
                grid_id, total_before, total_after)

    features = []
    for _, row in df.iterrows():
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(row["X"]), float(row["Y"])]
            },
            "properties": {
                "osm_id": str(row.get("osm_id", "")) if pd.notna(row.get("osm_id")) else None,
                "name": str(row.get("name", "Unknown")),
                "category": str(row.get("category", "Unknown")),
                "place_type": str(row.get("place_type", "Unknown")),
                "label": int(row.get("label", 0)) if pd.notna(row.get("label")) else 0,
                "weight": 1
            }
        })

    return {
        "type": "FeatureCollection",
        "metadata": {"total_pois": total_after},
        "features": features
    }
