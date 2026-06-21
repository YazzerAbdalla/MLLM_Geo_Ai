# Export Validation Report

**Date:** 2026-06-17  
**Audit scope:** Export endpoints, supported formats, ExportService implementation, runtime behavior

---

## Export Endpoint

| Property | Value |
|---|---|
| Route | `GET /api/v1/export/{job_id}` |
| Query param | `format` — one of `geojson`, `csv`, `shapefile` |
| Source | `app/interfaces/api.py:323` |
| Service | `app/application/export_service.py` — `ExportService` class |

## Supported Formats

| Format | `format` value | Media Type | Implementation |
|---|---|---|---|
| GeoJSON | `geojson` | `application/geo+json` | Reads file directly as bytes |
| CSV | `csv` | `text/csv` | GeoPandas read → drop geometry → to_csv |
| Shapefile (ZIP) | `shapefile` | `application/zip` | GeoPandas to_file → zip → bytes |

## Code Verification

- ✅ Endpoint registered at `GET /api/v1/export/{job_id}`
- ✅ Validates job exists → 404 if not found
- ✅ Validates job is not failed → 400 if `status == "failed"`
- ✅ Validates job is completed → 400 if status != "completed"
- ✅ Falls back to `job.result_data` if result file missing from disk
- ✅ `ExportService.to_geojson()` — reads file as raw bytes
- ✅ `ExportService.to_csv()` — uses GeoPandas to convert GeoJSON → CSV
- ✅ `ExportService.to_shapefile()` — writes to temp dir → zips → returns bytes
- ✅ Proper `Content-Disposition` headers set for all formats

## Runtime Verification

- ✅ **Geojson export:** Tested for a completed job — returned non-empty GeoJSON response
- ✅ **CSV export:** Tested for a completed job — returned non-empty CSV response
- ✅ **Invalid format:** Returns 400 error
- ✅ **Missing job:** Returns 404 error
- ✅ **Failed job:** Returns 400 error
- ⚠️ **Shapefile export:** Code verified but not runtime-tested (requires GDAL drivers)

## Error Handling

| Scenario | Status | Response |
|---|---|---|
| Job not found | `404` | `{"detail": "Job not found"}` |
| Job failed | `400` | `{"detail": "Cannot export: classification job failed"}` |
| Job not completed | `400` | `{"detail": "Cannot export: job status is '...' (must be 'completed')"}` |
| Invalid format | `400` | `{"detail": "Unsupported export format: ..."}` |
| Result file missing + no result_data | `404` | `{"detail": "Result file not found and no result data available"}` |

## Evidence Matrix

| Item | Source | Status |
|---|---|---|
| Export route defined | `app/interfaces/api.py:323` | ✅ |
| Job existence check | `app/interfaces/api.py:326-327` | ✅ |
| Job status validation | `app/interfaces/api.py:328-331` | ✅ |
| `ExportService` class exists | `app/application/export_service.py` | ✅ |
| GeoJSON export | `app/application/export_service.py:28` | ✅ |
| CSV export | `app/application/export_service.py:47` | ✅ |
| Shapefile export | `app/application/export_service.py:67` | ✅ |
| GeoJSON runtime (non-empty) | Session test | ✅ |
| CSV runtime (non-empty) | Session test | ✅ |
| Shapefile runtime | Not tested (GDAL required) | ⚠️ UNVERIFIABLE |
| Invalid format error | Session test | ✅ |
| Missing job error | Session test | ✅ |
| Failed job error | Session test | ✅ |
