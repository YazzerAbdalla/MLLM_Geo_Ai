import logging
from typing import Optional
import pandas as pd
import numpy as np

from app.infrastructure.spatial_index import PoiSpatialIndex

logger = logging.getLogger(__name__)

_df: Optional[pd.DataFrame] = None
_spatial_index: Optional[PoiSpatialIndex] = None
_heatmap_cache: Optional[dict] = None
_category_stats: Optional[dict] = None


def build_all(df: pd.DataFrame):
    global _df, _spatial_index, _heatmap_cache, _category_stats
    _df = df.copy()
    _spatial_index = PoiSpatialIndex(_df)
    _build_heatmap_cache()
    _build_category_stats()
    logger.info("Auxiliary caches built: %d rows, %d categories", len(_df), len(_category_stats or {}))


def _build_heatmap_cache():
    global _heatmap_cache
    if _df is None or _df.empty:
        _heatmap_cache = {"type": "FeatureCollection", "features": []}
        return
    df = _df.dropna(subset=["X", "Y"])
    null_mask = df["osm_id"].isna() if "osm_id" in df.columns else pd.Series([False] * len(df))
    df = pd.concat([
        df[~null_mask].drop_duplicates(subset=["osm_id"], keep="first"),
        df[null_mask]
    ])
    features = []
    for _, row in df.iterrows():
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [float(row["X"]), float(row["Y"])]},
            "properties": {
                "osm_id": str(row.get("osm_id", "")) if pd.notna(row.get("osm_id")) else None,
                "name": str(row.get("name", "Unknown")),
                "category": str(row.get("category", "Unknown")),
                "place_type": str(row.get("place_type", "Unknown")),
                "label": int(row.get("label", 0)) if pd.notna(row.get("label")) else 0,
                "weight": 1
            }
        })
    _heatmap_cache = {
        "type": "FeatureCollection",
        "metadata": {"total_pois": len(features), "source": "project.csv"},
        "features": features
    }


def _build_category_stats():
    global _category_stats
    if _df is None or _df.empty:
        _category_stats = {}
        return
    _category_stats = _df["category"].value_counts().to_dict()


def get_spatial_index() -> Optional[PoiSpatialIndex]:
    return _spatial_index


def get_heatmap_cache() -> Optional[dict]:
    return _heatmap_cache


def get_category_stats() -> Optional[dict]:
    return _category_stats


def refresh_all(csv_path: str) -> None:
    global _df
    _df = pd.read_csv(csv_path)
    build_all(_df)
    logger.info("All caches refreshed from %s: %d rows", csv_path, len(_df))
