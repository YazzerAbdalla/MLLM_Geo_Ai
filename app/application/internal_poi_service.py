import logging
import pandas as pd
from app.infrastructure import poi_cache as _poi_cache

logger = logging.getLogger(__name__)


def get_all_pois_heatmap() -> dict:
    df = _poi_cache.get_poi_cache()

    if df is None or df.empty:
        logger.info("total_cached=0 valid_rows=0 returned_features=0 (no cache)")
        return {
            "type": "FeatureCollection",
            "metadata": {"total_pois": 0, "source": "project.csv"},
            "features": []
        }

    total_cached = len(df)

    df = df.dropna(subset=["X", "Y"])

    null_mask = df["osm_id"].isna()
    df = pd.concat([
        df[~null_mask].drop_duplicates(subset=["osm_id"], keep="first"),
        df[null_mask]
    ])

    df = df[
        (df["X"] >= -180) &
        (df["X"] <= 180) &
        (df["Y"] >= -90) &
        (df["Y"] <= 90)
    ]

    valid_rows = len(df)

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

    logger.info("total_cached=%d valid_rows=%d returned_features=%d",
                total_cached, valid_rows, len(features))

    return {
        "type": "FeatureCollection",
        "metadata": {"total_pois": valid_rows, "source": "project.csv"},
        "features": features
    }
