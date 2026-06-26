import math
import numpy as np
from typing import Optional, List, Tuple
from scipy.spatial import KDTree


def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def normalize_name(name: str) -> str:
    import re
    import unicodedata
    name = unicodedata.normalize("NFKC", name)
    name = name.strip()
    name = re.sub(r"[\u200b\u200c\s]+", " ", name)
    name = name.lower()
    name = name.strip(".,;:'\"!?¡¿·()[]{}<>«»")
    return name


class PoiSpatialIndex:
    def __init__(self, df):
        self._df = df
        self._tree: Optional[KDTree] = None
        self._coords_rad: Optional[np.ndarray] = None
        self._build()

    def _build(self):
        coords = self._df[["Y", "X"]].dropna().values.astype(float)
        if len(coords) == 0:
            self._coords_rad = np.empty((0, 2))
            self._tree = KDTree(self._coords_rad)
            return
        self._coords_rad = np.radians(coords)
        self._tree = KDTree(self._coords_rad)

    def query_near(self, lat: float, lon: float, radius_m: float) -> List[int]:
        if self._tree is None or len(self._coords_rad) == 0:
            return []
        center = np.radians([[lat, lon]])
        radius_rad = radius_m / 6371000
        return self._tree.query_ball_point(center[0], radius_rad)

    def has_exact_coord(self, lat: float, lon: float) -> bool:
        if self._df is None or self._df.empty:
            return False
        eps = 1e-6
        mask = (self._df["X"].sub(lon).abs() < eps) & (self._df["Y"].sub(lat).abs() < eps)
        return mask.any()

    def find_near_poi(self, lat: float, lon: float, name: str, radius_m: float = 2.0) -> Tuple[bool, Optional[dict]]:
        indices = self.query_near(lat, lon, radius_m)
        if not indices:
            return False, None
        norm_name = normalize_name(name)
        for idx in indices:
            row = self._df.iloc[idx]
            if normalize_name(str(row.get("name", ""))) == norm_name:
                return True, {"name": row.get("name"), "lat": row["Y"], "lon": row["X"]}
        return False, None

    def find_exact_coord_match(self, lat: float, lon: float) -> Tuple[bool, Optional[dict]]:
        eps = 1e-6
        mask = (self._df["X"].sub(lon).abs() < eps) & (self._df["Y"].sub(lat).abs() < eps)
        matches = self._df[mask]
        if matches.empty:
            return False, None
        row = matches.iloc[0]
        return True, {"name": row.get("name"), "lat": row["Y"], "lon": row["X"]}
