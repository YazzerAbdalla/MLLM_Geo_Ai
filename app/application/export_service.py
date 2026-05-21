"""
 * Export Service for converting classification results to different formats.
 * 
 * Provides functionality to export classification results in multiple geospatial
 * formats including GeoJSON, CSV, and Shapefile (as ZIP archive).
 * Supports both web download and file system operations.
 """
import geopandas as gpd
import zipfile
import io
import tempfile
import os


class ExportService:
    """
     * Service class for exporting classification results to various formats.
     * 
     * Handles the conversion of GeoJSON classification results into different
     * output formats suitable for different downstream applications:
     * - GeoJSON: Web mapping and API responses
     * - CSV: Tabular analysis and spreadsheet software
     * - Shapefile: Desktop GIS software (ArcGIS, QGIS)
     * 
     * All methods return bytes ready for HTTP response or file writing.
     """
    
    def to_geojson(self, result_path: str) -> bytes:
        """
         * Exports classification results to GeoJSON format.
         * 
         * GeoJSON is the native format for web mapping applications and
         * maintains the full geospatial structure including geometry.
         * Returns raw bytes of the GeoJSON file content.
         * 
         * @param result_path: str - File path to the source GeoJSON result file
         * @returns bytes - Raw GeoJSON file content as bytes for download
         * 
         * @example
         * service = ExportService()
         * geojson_bytes = service.to_geojson("data/results/job_123.geojson")
         * response = send_file(io.BytesIO(geojson_bytes), mimetype='application/json')
         """
        with open(result_path, "rb") as f:
            return f.read()

    def to_csv(self, result_path: str) -> bytes:
        """
         * Exports classification results to CSV format.
         * 
         * Converts GeoJSON to tabular CSV format by dropping geometry column.
         * Useful for statistical analysis, reporting, or import into
         * spreadsheet applications like Excel or Google Sheets.
         * 
         * @param result_path: str - File path to the source GeoJSON result file
         * @returns bytes - CSV file content as bytes with classification data
         * 
         * @example
         * service = ExportService()
         * csv_bytes = service.to_csv("data/results/job_123.geojson")
         * # CSV columns: cell_id, dominant_class, confidence_Residential, etc.
         """
        gdf = gpd.read_file(result_path)
        df = gdf.drop(columns="geometry")
        return df.to_csv(index=False).encode()

    def to_shapefile(self, result_path: str) -> bytes:
        """
         * Exports classification results to Shapefile format (ZIP compressed).
         * 
         * Converts GeoJSON to ESRI Shapefile format, which requires multiple
         * files (.shp, .shx, .dbf, .prj). Returns a ZIP archive containing
         * all required shapefile components.
         * 
         * Shapefile is the standard format for desktop GIS software including:
         * - ArcGIS Pro/ArcMap
         * - QGIS
         * - GRASS GIS
         * 
         * Uses temporary directory to create intermediate files which are
         * automatically cleaned up after ZIP creation.
         * 
         * @param result_path: str - File path to the source GeoJSON result file
         * @returns bytes - ZIP archive containing complete shapefile as bytes
         * 
         * @example
         * service = ExportService()
         * shapefile_zip_bytes = service.to_shapefile("data/results/job_123.geojson")
         * # Download as result.zip containing result.shp, result.shx, result.dbf, result.prj
         * 
         * @note The returned ZIP archive maintains proper shapefile structure
         *       and can be directly unzipped and opened in any GIS software.
         """
        gdf = gpd.read_file(result_path)
        with tempfile.TemporaryDirectory() as tmpdir:
            shp_path = os.path.join(tmpdir, "result.shp")
            gdf.to_file(shp_path)
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w") as z:
                for f in os.listdir(tmpdir):
                    z.write(os.path.join(tmpdir, f), arcname=f)
            return buf.getvalue()