"""
 * Export Service for converting classification results to different formats.
 """
import geopandas as gpd
import zipfile
import io
import tempfile
import os


class ExportService:
    def to_geojson(self, result_path: str) -> bytes:
        with open(result_path, "rb") as f:
            return f.read()

    def to_csv(self, result_path: str) -> bytes:
        gdf = gpd.read_file(result_path)
        df = gdf.drop(columns="geometry")
        return df.to_csv(index=False).encode()

    def to_shapefile(self, result_path: str) -> bytes:
        gdf = gpd.read_file(result_path)
        with tempfile.TemporaryDirectory() as tmpdir:
            shp_path = os.path.join(tmpdir, "result.shp")
            gdf.to_file(shp_path)
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w") as z:
                for f in os.listdir(tmpdir):
                    z.write(os.path.join(tmpdir, f), arcname=f)
            return buf.getvalue()