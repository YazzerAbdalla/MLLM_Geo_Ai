import pandas as pd
from typing import Optional

_df: Optional[pd.DataFrame] = None


def load_poi_cache(csv_path: str) -> None:
    global _df
    _df = pd.read_csv(csv_path)
    print(f"POI cache loaded: {len(_df)} rows from {csv_path}")


def get_poi_cache() -> Optional[pd.DataFrame]:
    return _df


def clear_poi_cache() -> None:
    global _df
    _df = None


def reload_poi_cache(csv_path: str) -> None:
    global _df
    _df = pd.read_csv(csv_path)
    print(f"POI cache reloaded: {len(_df)} rows from {csv_path}")
