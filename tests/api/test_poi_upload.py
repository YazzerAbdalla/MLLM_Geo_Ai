import io
import json
import os
import shutil
import uuid
from pathlib import Path
from unittest.mock import patch, MagicMock, ANY

import pandas as pd
import pytest

from app.application import poi_upload_service as svc
from app.application.poi_upload_service import (
    PREVIEW_DIR,
    PREVIEW_TTL_SECONDS,
    IMPORT_HISTORY_DIR,
)
from app.infrastructure import poi_cache
from app.models.poi_upload import (
    ParsedPOI,
    UploadPreviewResponse,
    ImportResultV2,
    CancelResponse,
    ValidationSummary,
    ValidationWarning,
    ValidationErrorDetail,
)


@pytest.fixture(autouse=True)
def _protect_csv():
    csv_path = "data/raw/project.csv"
    backup_path = csv_path + ".bak"
    if os.path.exists(csv_path):
        shutil.copy2(csv_path, backup_path)
    yield
    if os.path.exists(backup_path):
        shutil.copy2(backup_path, csv_path)
        os.remove(backup_path)
        poi_cache.reload_poi_cache(csv_path)

# ─── Helpers ───────────────────────────────────────────────────────────────────

VALID_CSV = (
    "name,category,place_type,latitude,longitude,address\n"
    "New School X,Education,School,30.50,31.50,123 Main St\n"
    "New Clinic Y,Health,Clinic,30.55,31.55,\n"
)

VALID_CSV_LAT_LNG = (
    "name,category,place_type,lat,lng,address\n"
    "New Library Z,Education,Library,30.60,31.60,Book St\n"
)

VALID_CSV_NO_ADDRESS = (
    "name,category,place_type,latitude,longitude\n"
    "School A,Education,School,30.05,31.23\n"
)

MISSING_COLS_CSV = (
    "name,category,latitude,longitude\n"
    "School A,Education,30.05,31.23\n"
)

INVALID_LAT_CSV = (
    "name,category,place_type,latitude,longitude\n"
    "Bad Place,Health,Clinic,100.0,31.23\n"
)

INVALID_LON_CSV = (
    "name,category,place_type,latitude,longitude\n"
    "Bad Place,Health,Clinic,30.05,200.0\n"
)

DUPLICATE_ROWS_CSV = (
    "name,category,place_type,latitude,longitude,address\n"
    "School A,Education,School,30.05,31.23,Addr1\n"
    "School A,Education,School,30.05,31.23,Addr1\n"
)

MALFORMED_CSV = b"not,a,csv,file\nthis,is,not,proper\n"

MALFORMED_BINARY = b"\x00\x01\x02\xff\xfe\xfd\xfc"

NOT_UTF8 = b"\xff\xfe\x00\x31\x00\x2c\x00\x32\x00\x0a"

CATEGORY_ALIAS_CSV = (
    "name,category,place_type,latitude,longitude\n"
    "Restaurant X,Restaurants,Dining,30.05,31.23\n"
)

UNKNOWN_CATEGORY_CSV = (
    "name,category,place_type,latitude,longitude\n"
    "Mystery Place,Alien,Unknown,30.05,31.23\n"
)

EMPTY_CSV = "name,category,place_type,latitude,longitude,address\n"

NEAR_DUPLICATE_CSV = (
    "name,category,place_type,latitude,longitude,address\n"
    "School A,Education,School,30.05001,31.23001,Addr1\n"
)

NEAR_COORD_DUP_CSV = (
    "name,category,place_type,latitude,longitude,address\n"
    "Different Name,Education,School,30.05001,31.23001,Addr1\n"
)


def _make_sample_df():
    return pd.DataFrame({
        "X": [31.23, 31.25, 31.30],
        "Y": [30.05, 30.10, 30.15],
        "osm_id": [1001, 1002, 1003],
        "name": ["School A", "Hospital B", "Park C"],
        "place_type": ["School", "Hospital", "Park"],
        "category": ["Education", "Health", "Other"],
        "text_des": ["desc1", "desc2", "desc3"],
        "label": [0, 1, 0],
    })


# ─── Template ──────────────────────────────────────────────────────────────────

class TestDownloadTemplate:
    def test_returns_csv(self, client):
        resp = client.get("/api/v1/poi-upload/template")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/csv")
        assert "poi_upload_template.csv" in resp.headers["content-disposition"]
        assert "name,category,place_type,lat,lng,address" in resp.text


# ─── Validation ────────────────────────────────────────────────────────────────

class TestParseAndValidate:
    def test_valid_csv(self):
        parsed, summary = svc.parse_and_validate_csv(VALID_CSV.encode("utf-8"))
        assert summary.valid is True
        assert len(parsed) == 2
        assert parsed[0].name == "New School X"
        assert parsed[0].latitude == 30.50
        assert parsed[0].longitude == 31.50

    def test_valid_csv_lat_lng(self):
        parsed, summary = svc.parse_and_validate_csv(VALID_CSV_LAT_LNG.encode("utf-8"))
        assert summary.valid is True
        assert len(parsed) == 1
        assert parsed[0].latitude == 30.60
        assert parsed[0].longitude == 31.60

    def test_valid_csv_no_address(self):
        parsed, summary = svc.parse_and_validate_csv(VALID_CSV_NO_ADDRESS.encode("utf-8"))
        assert summary.valid is True
        assert len(parsed) == 1
        assert parsed[0].address == ""

    def test_missing_columns(self):
        with pytest.raises(ValueError, match="Missing required columns"):
            svc.parse_and_validate_csv(MISSING_COLS_CSV.encode("utf-8"))

    def test_invalid_latitude(self):
        parsed, summary = svc.parse_and_validate_csv(INVALID_LAT_CSV.encode("utf-8"))
        assert summary.valid is False
        errors = [e for e in summary.errors if e.field == "latitude"]
        assert len(errors) == 1
        assert "outside" in errors[0].message

    def test_invalid_longitude(self):
        parsed, summary = svc.parse_and_validate_csv(INVALID_LON_CSV.encode("utf-8"))
        assert summary.valid is False
        errors = [e for e in summary.errors if e.field == "longitude"]
        assert len(errors) == 1
        assert "outside" in errors[0].message

    def test_duplicate_rows(self):
        parsed, summary = svc.parse_and_validate_csv(DUPLICATE_ROWS_CSV.encode("utf-8"))
        dup_warnings = [w for w in summary.warnings if w.field == "(all)"]
        assert len(dup_warnings) >= 1

    def test_malformed_csv(self):
        with pytest.raises(ValueError):
            svc.parse_and_validate_csv(MALFORMED_BINARY)

    def test_malformed_csv_missing_columns(self):
        with pytest.raises(ValueError, match="Missing required columns"):
            svc.parse_and_validate_csv(MALFORMED_CSV)

    def test_invalid_encoding(self):
        with pytest.raises(ValueError, match="UTF-8"):
            svc.parse_and_validate_csv(NOT_UTF8)

    def test_empty_csv(self):
        with pytest.raises(ValueError, match="empty"):
            svc.parse_and_validate_csv(EMPTY_CSV.encode("utf-8"))

    def test_empty_values_produce_warnings(self):
        csv_data = (
            "name,category,place_type,latitude,longitude\n"
            ",,Hospital,30.05,31.23\n"
        )
        parsed, summary = svc.parse_and_validate_csv(csv_data.encode("utf-8"))
        assert len(summary.warnings) >= 2  # name + category empty


# ─── Category Validation ───────────────────────────────────────────────────────

class TestCategoryValidation:
    def test_auto_maps_alias(self, client):
        parsed, summary = svc.parse_and_validate_csv(CATEGORY_ALIAS_CSV.encode("utf-8"))
        response, _ = svc.build_preview_response(parsed, summary)
        cat_warnings = [w for w in response.validation.warnings if w.field == "category"]
        assert any("mapped" in w.message for w in cat_warnings)

    def test_unknown_category_warning(self, client):
        parsed, summary = svc.parse_and_validate_csv(UNKNOWN_CATEGORY_CSV.encode("utf-8"))
        response, _ = svc.build_preview_response(parsed, summary)
        cat_warnings = [w for w in response.validation.warnings if w.field == "category"]
        assert any("Unknown" in w.message for w in cat_warnings)


# ─── Preview Session (file-based, v2) ─────────────────────────────────────────

class TestPreviewSession:
    def test_create_and_load(self, tmp_path, monkeypatch):
        monkeypatch.setattr(svc, "PREVIEW_DIR", tmp_path / "poi_preview")
        parsed = [ParsedPOI(row=2, name="Test", category="Education", place_type="School", latitude=30.0, longitude=31.0, address="")]
        summary = ValidationSummary(valid=True, total_rows=1, errors=[], warnings=[])
        from app.models.poi_upload import ImportStatistics
        stats = ImportStatistics(bbox=[30, 31, 30, 31], center=[30, 31], unique_categories=["Education"], average_density=1.0, imported_area_deg=0.0)
        sid = svc.create_preview_session(parsed, summary, stats)
        loaded = svc.load_preview_session(sid)
        assert loaded is not None
        assert loaded["session_id"] == sid
        assert len(loaded["parsed_pois"]) == 1

    def test_load_nonexistent(self, tmp_path, monkeypatch):
        monkeypatch.setattr(svc, "PREVIEW_DIR", tmp_path / "poi_preview")
        loaded = svc.load_preview_session("nonexistent")
        assert loaded is None

    def test_delete(self, tmp_path, monkeypatch):
        monkeypatch.setattr(svc, "PREVIEW_DIR", tmp_path / "poi_preview")
        parsed = [ParsedPOI(row=2, name="Test", category="Education", place_type="School", latitude=30.0, longitude=31.0, address="")]
        summary = ValidationSummary(valid=True, total_rows=1, errors=[], warnings=[])
        from app.models.poi_upload import ImportStatistics
        stats = ImportStatistics(bbox=[30, 31, 30, 31], center=[30, 31], unique_categories=["Education"], average_density=1.0, imported_area_deg=0.0)
        sid = svc.create_preview_session(parsed, summary, stats)
        assert svc.delete_preview_session(sid) is True
        assert svc.load_preview_session(sid) is None

    def test_expiration(self, tmp_path, monkeypatch):
        monkeypatch.setattr(svc, "PREVIEW_DIR", tmp_path / "poi_preview")
        monkeypatch.setattr(svc, "PREVIEW_TTL_SECONDS", -1)
        parsed = [ParsedPOI(row=2, name="Test", category="Education", place_type="School", latitude=30.0, longitude=31.0, address="")]
        summary = ValidationSummary(valid=True, total_rows=1, errors=[], warnings=[])
        from app.models.poi_upload import ImportStatistics
        stats = ImportStatistics(bbox=[30, 31, 30, 31], center=[30, 31], unique_categories=["Education"], average_density=1.0, imported_area_deg=0.0)
        sid = svc.create_preview_session(parsed, summary, stats)
        loaded = svc.load_preview_session(sid)
        assert loaded is None

    def test_cleanup_expired(self, tmp_path, monkeypatch):
        monkeypatch.setattr(svc, "PREVIEW_DIR", tmp_path / "poi_preview")
        monkeypatch.setattr(svc, "PREVIEW_TTL_SECONDS", -1)
        parsed = [ParsedPOI(row=2, name="Test", category="Education", place_type="School", latitude=30.0, longitude=31.0, address="")]
        summary = ValidationSummary(valid=True, total_rows=1, errors=[], warnings=[])
        from app.models.poi_upload import ImportStatistics
        stats = ImportStatistics(bbox=[30, 31, 30, 31], center=[30, 31], unique_categories=["Education"], average_density=1.0, imported_area_deg=0.0)
        svc.create_preview_session(parsed, summary, stats)
        removed = svc.cleanup_expired_previews()
        assert removed >= 1


# ─── Upload Endpoint ──────────────────────────────────────────────────────────

class TestUploadEndpoint:
    def test_upload_valid_csv(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr(svc, "PREVIEW_DIR", tmp_path / "poi_preview")
        resp = client.post("/api/v1/poi-upload/preview", files={"file": ("test.csv", VALID_CSV.encode("utf-8"), "text/csv")})
        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" in data
        assert data["total_uploaded"] == 2
        assert data["validation"]["valid"] is True

    def test_upload_missing_columns(self, client):
        resp = client.post("/api/v1/poi-upload/preview", files={"file": ("test.csv", MISSING_COLS_CSV.encode("utf-8"), "text/csv")})
        assert resp.status_code == 422

    def test_upload_invalid_coords(self, client):
        resp = client.post("/api/v1/poi-upload/preview", files={"file": ("test.csv", INVALID_LAT_CSV.encode("utf-8"), "text/csv")})
        assert resp.status_code == 200
        data = resp.json()
        assert data["validation"]["valid"] is False
        assert len(data["validation"]["errors"]) > 0

    def test_upload_malformed(self, client):
        resp = client.post("/api/v1/poi-upload/preview", files={"file": ("test.csv", MALFORMED_CSV, "text/csv")})
        assert resp.status_code == 422

    def test_upload_empty_file(self, client):
        resp = client.post("/api/v1/poi-upload/preview", files={"file": ("empty.csv", b"", "text/csv")})
        assert resp.status_code == 400

    def test_upload_no_filename(self, client):
        resp = client.post("/api/v1/poi-upload/preview", files={"file": ("", b"data", "text/csv")})
        assert resp.status_code in (400, 422)


# ─── Import (atomic, duplicate detection, audit) ──────────────────────────────

class TestImport:
    def test_import_success(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr(svc, "PREVIEW_DIR", tmp_path / "poi_preview")
        monkeypatch.setattr(svc, "IMPORT_HISTORY_DIR", tmp_path / "import_history")
        monkeypatch.setattr("os.path.exists", lambda p: True)

        sample_df = _make_sample_df()
        monkeypatch.setattr(poi_cache, "_df", sample_df.copy())

        parsed = [
            ParsedPOI(row=2, name="New School", category="Education", place_type="School", latitude=30.20, longitude=31.35, address="Addr1"),
            ParsedPOI(row=3, name="New Hospital", category="Health", place_type="Hospital", latitude=30.25, longitude=31.40, address="Addr2"),
        ]
        summary = ValidationSummary(valid=True, total_rows=2, errors=[], warnings=[])
        from app.models.poi_upload import ImportStatistics
        stats = ImportStatistics(bbox=[30.2, 31.35, 30.25, 31.4], center=[30.225, 31.375], unique_categories=["Education", "Health"], average_density=1.0, imported_area_deg=0.0025)
        sid = svc.create_preview_session(parsed, summary, stats)

        tmp_csv = tmp_path / "project.csv"
        sample_df.to_csv(str(tmp_csv), index=False)

        def _fake_import(sid2):
            new_rows_df = pd.DataFrame([
                {"X": 31.35, "Y": 30.20, "osm_id": None, "name": "New School",
                 "place_type": "School", "category": "Education", "text_des": "Addr1",
                 "label": 0, "source": "user_upload", "import_batch_id": "batch_X",
                 "created_at": "now", "validated": True},
                {"X": 31.40, "Y": 30.25, "osm_id": None, "name": "New Hospital",
                 "place_type": "Hospital", "category": "Health", "text_des": "Addr2",
                 "label": 0, "source": "user_upload", "import_batch_id": "batch_X",
                 "created_at": "now", "validated": True},
            ])
            final_df = pd.concat([sample_df, new_rows_df], ignore_index=True)
            final_df.to_csv(str(tmp_csv), index=False)
            poi_cache._df = final_df
            return ImportResultV2(
                imported_count=2,
                skipped_count=0,
                duplicate_coordinates=0,
                duplicate_pois=0,
                message="2 POIs imported successfully.",
                statistics=stats,
            )

        monkeypatch.setattr("app.application.poi_upload_service.import_preview", _fake_import)

        resp = client.post(f"/api/v1/poi-upload/import/{sid}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["imported_count"] == 2
        assert data["duplicate_coordinates"] == 0
        assert data["duplicate_pois"] == 0

    def test_import_session_not_found(self, client):
        resp = client.post("/api/v1/poi-upload/import/nonexistent-sid")
        assert resp.status_code == 404

    def test_import_skips_duplicate_coords(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr(svc, "PREVIEW_DIR", tmp_path / "poi_preview")
        monkeypatch.setattr(svc, "IMPORT_HISTORY_DIR", tmp_path / "import_history")
        monkeypatch.setattr("app.application.poi_upload_service.refresh_aux_caches", lambda p: None)

        sample_df = _make_sample_df()
        monkeypatch.setattr(poi_cache, "_df", sample_df.copy())

        parsed = [
            ParsedPOI(row=2, name="Different Name", category="Health", place_type="Hospital", latitude=30.05, longitude=31.23, address=""),
        ]
        summary = ValidationSummary(valid=True, total_rows=1, errors=[], warnings=[])
        from app.models.poi_upload import ImportStatistics
        stats = ImportStatistics(bbox=[30.05, 31.23, 30.05, 31.23], center=[30.05, 31.23], unique_categories=["Health"], average_density=1.0, imported_area_deg=0.0)
        sid = svc.create_preview_session(parsed, summary, stats)

        with patch("app.application.poi_upload_service.poi_cache.reload_poi_cache"):
            resp = client.post(f"/api/v1/poi-upload/import/{sid}")
            assert resp.status_code == 200
            data = resp.json()
            assert data["imported_count"] == 0
            assert data["duplicate_coordinates"] == 1

    def test_import_skips_near_duplicate_poi(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr(svc, "PREVIEW_DIR", tmp_path / "poi_preview")
        monkeypatch.setattr(svc, "IMPORT_HISTORY_DIR", tmp_path / "import_history")
        monkeypatch.setattr("app.application.poi_upload_service.refresh_aux_caches", lambda p: None)

        sample_df = _make_sample_df()
        monkeypatch.setattr(poi_cache, "_df", sample_df.copy())

        parsed, summary = svc.parse_and_validate_csv(NEAR_DUPLICATE_CSV.encode("utf-8"))
        from app.models.poi_upload import ImportStatistics
        stats = ImportStatistics(bbox=[30.05, 31.23, 30.05, 31.23], center=[30.05, 31.23], unique_categories=["Education"], average_density=1.0, imported_area_deg=0.0)
        sid = svc.create_preview_session(parsed, summary, stats)

        with patch("app.application.poi_upload_service.poi_cache.reload_poi_cache"):
            resp = client.post(f"/api/v1/poi-upload/import/{sid}")
            assert resp.status_code == 200
            data = resp.json()
            assert data["duplicate_pois"] >= 1

    def test_import_skips_near_coord_with_diff_name(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr(svc, "PREVIEW_DIR", tmp_path / "poi_preview")
        monkeypatch.setattr(svc, "IMPORT_HISTORY_DIR", tmp_path / "import_history")
        monkeypatch.setattr("app.application.poi_upload_service.refresh_aux_caches", lambda p: None)

        sample_df = _make_sample_df()
        monkeypatch.setattr(poi_cache, "_df", sample_df.copy())

        parsed, summary = svc.parse_and_validate_csv(NEAR_COORD_DUP_CSV.encode("utf-8"))
        from app.models.poi_upload import ImportStatistics
        stats = ImportStatistics(bbox=[30.05, 31.23, 30.05, 31.23], center=[30.05, 31.23], unique_categories=["Education"], average_density=1.0, imported_area_deg=0.0)
        sid = svc.create_preview_session(parsed, summary, stats)

        with patch("app.application.poi_upload_service.poi_cache.reload_poi_cache"):
            resp = client.post(f"/api/v1/poi-upload/import/{sid}")
            assert resp.status_code == 200
            data = resp.json()
            assert data["duplicate_coordinates"] >= 1

    def test_import_creates_audit_log(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr(svc, "PREVIEW_DIR", tmp_path / "poi_preview")
        monkeypatch.setattr(svc, "IMPORT_HISTORY_DIR", tmp_path / "import_history")
        monkeypatch.setattr("app.application.poi_upload_service.refresh_aux_caches", lambda p: None)

        sample_df = _make_sample_df()
        monkeypatch.setattr(poi_cache, "_df", sample_df.copy())

        parsed = [ParsedPOI(row=2, name="New", category="Education", place_type="School", latitude=30.50, longitude=31.50, address="")]
        summary = ValidationSummary(valid=True, total_rows=1, errors=[], warnings=[])
        from app.models.poi_upload import ImportStatistics
        stats = ImportStatistics(bbox=[30.5, 31.5, 30.5, 31.5], center=[30.5, 31.5], unique_categories=["Education"], average_density=1.0, imported_area_deg=0.0)
        sid = svc.create_preview_session(parsed, summary, stats)

        with patch("app.application.poi_upload_service.poi_cache.reload_poi_cache"):
            client.post(f"/api/v1/poi-upload/import/{sid}")

        log_files = list((tmp_path / "import_history").glob("*.json"))
        assert len(log_files) >= 1


# ─── Cancel ───────────────────────────────────────────────────────────────────

class TestCancel:
    def test_cancel_existing_session(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr(svc, "PREVIEW_DIR", tmp_path / "poi_preview")
        parsed = [ParsedPOI(row=2, name="Test", category="Education", place_type="School", latitude=30.0, longitude=31.0, address="")]
        summary = ValidationSummary(valid=True, total_rows=1, errors=[], warnings=[])
        from app.models.poi_upload import ImportStatistics
        stats = ImportStatistics(bbox=[30, 31, 30, 31], center=[30, 31], unique_categories=["Education"], average_density=1.0, imported_area_deg=0.0)
        sid = svc.create_preview_session(parsed, summary, stats)

        resp = client.delete(f"/api/v1/poi-upload/preview/{sid}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "cancelled"

    def test_cancel_nonexistent(self, client):
        resp = client.delete("/api/v1/poi-upload/preview/nonexistent")
        assert resp.status_code == 404

    def test_cancel_removes_preview(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr(svc, "PREVIEW_DIR", tmp_path / "poi_preview")
        parsed = [ParsedPOI(row=2, name="Test", category="Education", place_type="School", latitude=30.0, longitude=31.0, address="")]
        summary = ValidationSummary(valid=True, total_rows=1, errors=[], warnings=[])
        from app.models.poi_upload import ImportStatistics
        stats = ImportStatistics(bbox=[30, 31, 30, 31], center=[30, 31], unique_categories=["Education"], average_density=1.0, imported_area_deg=0.0)
        sid = svc.create_preview_session(parsed, summary, stats)

        client.delete(f"/api/v1/poi-upload/preview/{sid}")
        loaded = svc.load_preview_session(sid)
        assert loaded is None


# ─── Statistics ───────────────────────────────────────────────────────────────

class TestStatistics:
    def test_compute_statistics(self):
        from app.application.poi_upload_service import _compute_statistics
        pois = [
            ParsedPOI(row=2, name="A", category="Education", place_type="School", latitude=30.0, longitude=31.0, address=""),
            ParsedPOI(row=3, name="B", category="Health", place_type="Hospital", latitude=30.1, longitude=31.1, address=""),
        ]
        stats = _compute_statistics(pois)
        assert stats.bbox == [30.0, 31.0, 30.1, 31.1]
        assert stats.center == [30.05, 31.05]
        assert "Education" in stats.unique_categories
        assert "Health" in stats.unique_categories

    def test_statistics_empty(self):
        from app.application.poi_upload_service import _compute_statistics
        stats = _compute_statistics([])
        assert stats.bbox == [0, 0, 0, 0]


# ─── AI-Ready Metadata ────────────────────────────────────────────────────────

class TestAIMetadata:
    def test_apply_metadata_columns(self):
        from app.application.poi_upload_service import _apply_metadata, _ensure_ai_metadata_columns
        import pandas as pd
        parsed = [ParsedPOI(row=2, name="Test", category="Education", place_type="School", latitude=30.0, longitude=31.0, address="")]
        existing = pd.DataFrame({"X": [31.0], "Y": [30.0]})
        existing = _ensure_ai_metadata_columns(existing)
        df = _apply_metadata(parsed, existing)
        assert "source" in df.columns
        assert "import_batch_id" in df.columns
        assert "created_at" in df.columns
        assert "validated" in df.columns
        assert df.iloc[0]["source"] == "user_upload"
        assert df.iloc[0]["validated"] == True


# ─── Spatial Index ────────────────────────────────────────────────────────────

class TestSpatialIndex:
    def test_kdtree_query(self):
        from app.infrastructure.spatial_index import PoiSpatialIndex
        import pandas as pd
        df = pd.DataFrame({
            "X": [31.23, 31.25, 31.30],
            "Y": [30.05, 30.10, 30.15],
            "name": ["A", "B", "C"],
        })
        idx = PoiSpatialIndex(df)
        near = idx.query_near(30.05, 31.23, 100)
        assert 0 in near

    def test_exact_coord(self):
        from app.infrastructure.spatial_index import PoiSpatialIndex
        import pandas as pd
        df = pd.DataFrame({"X": [31.23], "Y": [30.05], "name": ["A"]})
        idx = PoiSpatialIndex(df)
        found, match = idx.find_exact_coord_match(30.05, 31.23)
        assert found is True

    def test_normalize_name(self):
        from app.infrastructure.spatial_index import normalize_name
        assert normalize_name("  Pharmacy  ") == normalize_name("pharmacy")
        assert normalize_name("Restaurant!") == normalize_name("Restaurant")
        assert normalize_name("  SCHOOL  ") == normalize_name("School")


# ─── Full Integration Flow ────────────────────────────────────────────────────

class TestFullFlow:
    def test_upload_preview_import_flow(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr(svc, "PREVIEW_DIR", tmp_path / "poi_preview")
        monkeypatch.setattr(svc, "IMPORT_HISTORY_DIR", tmp_path / "import_history")

        sample_df = _make_sample_df()
        monkeypatch.setattr(poi_cache, "_df", sample_df.copy())

        resp = client.post("/api/v1/poi-upload/preview", files={"file": ("test.csv", VALID_CSV.encode("utf-8"), "text/csv")})
        assert resp.status_code == 200
        preview = resp.json()
        sid = preview["session_id"]
        assert len(sid) > 0
        assert preview["total_uploaded"] == 2
        assert preview["validation"]["valid"] is True

        monkeypatch.setattr("app.application.poi_upload_service.refresh_aux_caches", lambda p: None)

        with patch("app.application.poi_upload_service.poi_cache.reload_poi_cache"):
            resp2 = client.post(f"/api/v1/poi-upload/import/{sid}")
            assert resp2.status_code == 200
            result = resp2.json()
            assert result["imported_count"] >= 1

    def test_upload_cancel_flow(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr(svc, "PREVIEW_DIR", tmp_path / "poi_preview")

        resp = client.post("/api/v1/poi-upload/preview", files={"file": ("test.csv", VALID_CSV.encode("utf-8"), "text/csv")})
        assert resp.status_code == 200
        sid = resp.json()["session_id"]

        resp2 = client.delete(f"/api/v1/poi-upload/preview/{sid}")
        assert resp2.status_code == 200
        assert resp2.json()["status"] == "cancelled"

        resp3 = client.post(f"/api/v1/poi-upload/import/{sid}")
        assert resp3.status_code == 404


# ─── Health check (confirm existing endpoints not broken) ─────────────────────

class TestExistingEndpoints:
    def test_health_check(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200


# ─── GeoJSON Features ─────────────────────────────────────────────────────────

class TestPreviewGeoJSON:
    def test_preview_contains_features(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr(svc, "PREVIEW_DIR", tmp_path / "poi_preview")
        resp = client.post("/api/v1/poi-upload/preview", files={"file": ("test.csv", VALID_CSV.encode("utf-8"), "text/csv")})
        assert resp.status_code == 200
        data = resp.json()
        assert "features" in data
        assert data["features"]["type"] == "FeatureCollection"
        assert isinstance(data["features"]["features"], list)

    def test_one_feature_per_valid_poi(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr(svc, "PREVIEW_DIR", tmp_path / "poi_preview")
        resp = client.post("/api/v1/poi-upload/preview", files={"file": ("test.csv", VALID_CSV.encode("utf-8"), "text/csv")})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["features"]["features"]) == data["total_uploaded"]

    def test_coordinates_are_lng_lat(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr(svc, "PREVIEW_DIR", tmp_path / "poi_preview")
        resp = client.post("/api/v1/poi-upload/preview", files={"file": ("test.csv", VALID_CSV.encode("utf-8"), "text/csv")})
        assert resp.status_code == 200
        data = resp.json()
        for feat in data["features"]["features"]:
            coords = feat["geometry"]["coordinates"]
            assert len(coords) == 2
            assert isinstance(coords[0], float)
            assert isinstance(coords[1], float)

    def test_feature_properties(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr(svc, "PREVIEW_DIR", tmp_path / "poi_preview")
        resp = client.post("/api/v1/poi-upload/preview", files={"file": ("test.csv", VALID_CSV.encode("utf-8"), "text/csv")})
        assert resp.status_code == 200
        data = resp.json()
        feat = data["features"]["features"][0]
        props = feat["properties"]
        assert "name" in props
        assert "category" in props
        assert "place_type" in props
        assert "status" in props
        assert "validation" in props
        assert props["name"] == "New School X"
        assert props["category"] == "Education"
        assert props["place_type"] == "School"
        assert props["status"] == "new"
        assert props["validation"] == "valid"

    def test_feature_status_valid(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr(svc, "PREVIEW_DIR", tmp_path / "poi_preview")
        resp = client.post("/api/v1/poi-upload/preview", files={"file": ("test.csv", VALID_CSV.encode("utf-8"), "text/csv")})
        assert resp.status_code == 200
        data = resp.json()
        for feat in data["features"]["features"]:
            assert feat["properties"]["validation"] == "valid"

    def test_feature_status_warning_on_empty_name(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr(svc, "PREVIEW_DIR", tmp_path / "poi_preview")
        csv_data = (
            "name,category,place_type,latitude,longitude\n"
            ",Education,School,30.05,31.23\n"
        )
        resp = client.post("/api/v1/poi-upload/preview", files={"file": ("test.csv", csv_data.encode("utf-8"), "text/csv")})
        assert resp.status_code == 200
        data = resp.json()
        for feat in data["features"]["features"]:
            assert feat["properties"]["validation"] == "warning"

    def test_empty_features_on_validation_failure(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr(svc, "PREVIEW_DIR", tmp_path / "poi_preview")
        resp = client.post("/api/v1/poi-upload/preview", files={"file": ("test.csv", INVALID_LAT_CSV.encode("utf-8"), "text/csv")})
        assert resp.status_code == 200
        data = resp.json()
        assert "features" in data
        assert data["features"]["type"] == "FeatureCollection"
        assert data["features"]["features"] == []

    def test_statistics_bbox_and_center(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr(svc, "PREVIEW_DIR", tmp_path / "poi_preview")
        resp = client.post("/api/v1/poi-upload/preview", files={"file": ("test.csv", VALID_CSV.encode("utf-8"), "text/csv")})
        assert resp.status_code == 200
        data = resp.json()
        stats = data.get("statistics")
        assert stats is not None
        assert "bbox" in stats
        assert "center" in stats
        assert "unique_categories" in stats
        assert "average_density" in stats
        assert len(stats["bbox"]) == 4
        assert len(stats["center"]) == 2

    def test_session_json_contains_features(self, tmp_path, monkeypatch):
        monkeypatch.setattr(svc, "PREVIEW_DIR", tmp_path / "poi_preview")
        parsed = [ParsedPOI(row=2, name="Test", category="Education", place_type="School", latitude=30.0, longitude=31.0, address="")]
        summary = ValidationSummary(valid=True, total_rows=1, errors=[], warnings=[])
        from app.models.poi_upload import ImportStatistics
        stats = ImportStatistics(bbox=[30, 31, 30, 31], center=[30, 31], unique_categories=["Education"], average_density=1.0, imported_area_deg=0.0)
        sid = svc.create_preview_session(parsed, summary, stats)
        session = svc.load_preview_session(sid)
        assert session is not None
        assert "features" in session
        assert session["features"]["type"] == "FeatureCollection"

    def test_features_on_preview_import_flow(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr(svc, "PREVIEW_DIR", tmp_path / "poi_preview")
        monkeypatch.setattr(svc, "IMPORT_HISTORY_DIR", tmp_path / "import_history")
        sample_df = _make_sample_df()
        monkeypatch.setattr(poi_cache, "_df", sample_df.copy())
        resp = client.post("/api/v1/poi-upload/preview", files={"file": ("test.csv", VALID_CSV.encode("utf-8"), "text/csv")})
        assert resp.status_code == 200
        data = resp.json()
        assert "features" in data
        assert len(data["features"]["features"]) == 2

    def test_internal_poi_preview_alias_returns_features(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr(svc, "PREVIEW_DIR", tmp_path / "poi_preview")
        resp = client.post("/api/v1/internal/poi-preview", files={"file": ("test.csv", VALID_CSV.encode("utf-8"), "text/csv")})
        assert resp.status_code == 200
        data = resp.json()
        assert "features" in data
        assert data["features"]["type"] == "FeatureCollection"

    def test_upload_with_lat_lng_aliases_returns_features(self, client, tmp_path, monkeypatch):
        monkeypatch.setattr(svc, "PREVIEW_DIR", tmp_path / "poi_preview")
        resp = client.post("/api/v1/poi-upload/preview", files={"file": ("test.csv", VALID_CSV_LAT_LNG.encode("utf-8"), "text/csv")})
        assert resp.status_code == 200
        data = resp.json()
        assert "features" in data
        assert len(data["features"]["features"]) == 1
        feat = data["features"]["features"][0]
        assert feat["properties"]["name"] == "New Library Z"
        assert feat["geometry"]["coordinates"] == [31.60, 30.60]
