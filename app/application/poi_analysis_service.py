import logging
import math
import pandas as pd
from shapely.geometry import shape, Point
from app.infrastructure import poi_cache as _poi_cache

logger = logging.getLogger(__name__)

MAX_RETURNED_POIS = 1000

NOMINIMUM_USER_AGENT = "mllm_geo_ai_poi_analysis/1.0"


def analyze_poi_area(geometry: dict, include_location: bool = False) -> dict:
    polygon = _validate_polygon(geometry)

    centroid = polygon.centroid
    area_m2, perimeter_m = _compute_utm_metrics(polygon)
    area_km2 = round(area_m2 / 1_000_000, 4) if area_m2 > 0 else 0.0

    df = _poi_cache.get_poi_cache()

    if df is None or df.empty:
        return _build_empty_result(
            polygon, centroid, area_m2, area_km2, perimeter_m
        )

    df = df.dropna(subset=["X", "Y"])
    df = df[
        (df["X"] >= -180) & (df["X"] <= 180) &
        (df["Y"] >= -90) & (df["Y"] <= 90)
    ]

    if df.empty:
        return _build_empty_result(
            polygon, centroid, area_m2, area_km2, perimeter_m
        )

    points = df.apply(lambda row: Point(row["X"], row["Y"]), axis=1)
    mask = points.apply(lambda p: polygon.covers(p))
    filtered_df = df[mask].copy()

    total_pois = len(filtered_df)
    if total_pois == 0:
        return _build_empty_result(
            polygon, centroid, area_m2, area_km2, perimeter_m
        )

    poi_density = round(total_pois / area_km2, 2) if area_km2 > 0 else 0.0

    category_counts = filtered_df["category"].value_counts().to_dict()
    top_categories = sorted(category_counts.items(), key=lambda x: -x[1])[:10]

    poi_list = _build_poi_list(filtered_df)

    truncated = False
    if len(poi_list) > MAX_RETURNED_POIS:
        truncated = True
        poi_list = poi_list[:MAX_RETURNED_POIS]

    reverse_geo = None
    if include_location:
        reverse_geo = _reverse_geocode(centroid)

    return {
        "type": "FeatureCollection",
        "features": poi_list,
        "analysis": {
            "total_pois": total_pois,
            "area_m2": round(area_m2, 2),
            "area_km2": area_km2,
            "perimeter_m": round(perimeter_m, 2),
            "poi_density": poi_density,
            "centroid": {
                "type": "Point",
                "coordinates": [round(centroid.x, 6), round(centroid.y, 6)]
            },
            "category_counts": {str(k): int(v) for k, v in category_counts.items()},
            "top_categories": [
                {"category": str(k), "count": int(v)}
                for k, v in top_categories
            ],
            "reverse_geocoding": reverse_geo,
            "returned_pois": len(poi_list),
            "truncated": truncated
        }
    }


def _validate_polygon(geometry: dict):
    if not isinstance(geometry, dict):
        raise ValueError("Geometry must be a GeoJSON object")

    geom_type = geometry.get("type")
    if geom_type != "Polygon":
        raise ValueError(
            f"Unsupported geometry type: '{geom_type}'. Only 'Polygon' is supported."
        )

    coords = geometry.get("coordinates")
    if not coords or not isinstance(coords, list) or len(coords) == 0:
        raise ValueError("Empty coordinates")

    try:
        polygon = shape(geometry)
    except Exception as e:
        raise ValueError(f"Invalid polygon: {str(e)}")

    if polygon.is_empty:
        raise ValueError("Empty polygon")
    if not polygon.is_valid:
        raise ValueError("Invalid polygon geometry")

    return polygon


def _compute_utm_metrics(polygon):
    try:
        import pyproj
        from shapely.ops import transform

        lon, lat = polygon.centroid.x, polygon.centroid.y
        utm_zone = int((lon + 180) / 6) + 1
        epsg_code = 32600 + utm_zone if lat >= 0 else 32700 + utm_zone

        crs_geo = pyproj.CRS.from_epsg(4326)
        crs_utm = pyproj.CRS.from_epsg(epsg_code)
        project = pyproj.Transformer.from_crs(
            crs_geo, crs_utm, always_xy=True
        ).transform
        polygon_utm = transform(project, polygon)
        return polygon_utm.area, polygon_utm.length
    except Exception:
        lat_m = 111_320
        lon_m = 111_320 * math.cos(math.radians(polygon.centroid.y))
        area_m2 = polygon.area * lat_m * lon_m
        return area_m2, 0.0


def _reverse_geocode(centroid):
    try:
        import requests
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "lat": centroid.y,
            "lon": centroid.x,
            "format": "json",
            "addressdetails": 1,
        }
        headers = {"User-Agent": NOMINIMUM_USER_AGENT}
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data and "address" in data:
            address = data["address"]
            return {
                "area_name": data.get("display_name"),
                "city": (
                    address.get("city")
                    or address.get("town")
                    or address.get("village")
                ),
                "country": address.get("country"),
            }
    except Exception as e:
        logger.warning("Reverse geocoding failed: %s", e)

    return {"area_name": None, "city": None, "country": None}


def _build_poi_list(df: pd.DataFrame) -> list:
    poi_list = []
    for _, row in df.iterrows():
        poi_list.append({
            "name": str(row.get("name", "Unknown")),
            "category": str(row.get("category", "Unknown")),
            "place_type": str(row.get("place_type", "Unknown")),
            "coordinates": [float(row["X"]), float(row["Y"])],
        })
    return poi_list


def _build_empty_result(polygon, centroid, area_m2, area_km2, perimeter_m):
    return {
        "type": "FeatureCollection",
        "features": [],
        "analysis": {
            "total_pois": 0,
            "area_m2": round(area_m2, 2),
            "area_km2": area_km2,
            "perimeter_m": round(perimeter_m, 2),
            "poi_density": 0.0,
            "centroid": {
                "type": "Point",
                "coordinates": [round(centroid.x, 6), round(centroid.y, 6)]
            },
            "category_counts": {},
            "top_categories": [],
            "reverse_geocoding": None,
            "returned_pois": 0,
            "truncated": False,
        }
    }
