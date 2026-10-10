import os
import pytest
from unittest.mock import patch
from app.core.config import (
    Settings,
    is_vercel_environment,
    resolve_storage_dir,
    ensure_storage_directories
)
from app.services.storage_service import StorageService
from app.services.report_service import report_service

def test_default_local_storage_dir():
    """Verifies that local development preserves the standard data/storage directory."""
    with patch.dict(os.environ, {}, clear=True):
        # Ensure no Vercel env flags
        os.environ.pop("VERCEL", None)
        os.environ.pop("VERCEL_ENV", None)
        os.environ.pop("AWS_LAMBDA_FUNCTION_NAME", None)
        os.environ.pop("NOW_REGION", None)

        storage_dir = resolve_storage_dir()
        assert not is_vercel_environment()
        assert "data" in storage_dir
        assert "storage" in storage_dir

def test_vercel_storage_dir_detection():
    """Verifies that VERCEL=1 activates the /tmp/resq-vision writable storage path."""
    with patch.dict(os.environ, {"VERCEL": "1"}):
        assert is_vercel_environment() is True
        storage_dir = resolve_storage_dir()
        assert storage_dir == "/tmp/resq-vision"

def test_vercel_overrides_readonly_var_data_path():
    """
    Verifies that when running on Vercel, a configured path like '/var/data'
    is safely overridden with '/tmp/resq-vision' to avoid read-only filesystem crashes.
    """
    with patch.dict(os.environ, {"VERCEL": "1", "VERCEL_ENV": "production"}):
        storage_dir = resolve_storage_dir("/var/data")
        assert storage_dir == "/tmp/resq-vision"

def test_vercel_allows_custom_tmp_subdir():
    """Verifies that an explicitly configured /tmp subpath on Vercel is permitted."""
    with patch.dict(os.environ, {"VERCEL": "1"}):
        storage_dir = resolve_storage_dir("/tmp/custom-app-storage")
        assert storage_dir == "/tmp/custom-app-storage"

def test_ensure_storage_directories_handles_readonly_error():
    """
    Simulates an OSError (Errno 30 Read-only file system) during os.makedirs
    and verifies that ensure_storage_directories handles it cleanly without crashing.
    """
    with patch("os.makedirs", side_effect=OSError(30, "Read-only file system: '/var/data'")):
        result = ensure_storage_directories("/var/data")
        # Function handles the error gracefully and returns False (or fallback status) without raising
        assert result is False

def test_storage_service_works_with_configured_directory(tmp_path):
    """Verifies that StorageService correctly creates files and persists records in configured storage directory."""
    test_storage_dir = str(tmp_path / "resq_test_storage")
    with patch("app.core.config.settings.LOCAL_STORAGE_DIR", test_storage_dir), \
         patch("app.core.config.settings.MONGODB_URI", ""):
        # Initialize an isolated StorageService instance pointing to tmp_path
        storage = StorageService()

        assert os.path.exists(test_storage_dir)
        assert os.path.exists(storage.local_file)

        # Save an incident in local file
        sample = {
            "incident_id": "TEST-VERCEL-01",
            "incident_type": "road_accident",
            "incident_summary": "Test collision for Vercel storage test."
        }
        saved_id = storage.save_incident(sample)
        assert saved_id == "TEST-VERCEL-01"

        # Read back from local JSON file
        incidents = storage._read_local_incidents()
        assert len(incidents) >= 1
        assert any(inc["incident_id"] == "TEST-VERCEL-01" for inc in incidents)

def test_report_service_pdf_generation_in_temp_dir(tmp_path):
    """Verifies that report_service generates PDFs inside configured storage directory."""
    test_storage_dir = str(tmp_path / "resq_pdf_storage")
    sample_report = {
        "incident_id": "TEST-PDF-01",
        "incident_type": "road_accident",
        "incident_summary": "Two vehicles damaged at crossing.",
        "observations": [{"description": "Crush bumper", "confidence": "high", "evidence": "Debris"}],
        "potential_concerns": [{"concern": "Fluid spill", "confidence": "medium", "reason": "Slippery", "evidence": "Dark pool"}],
        "safety_disclaimer": "AI decision support aid."
    }
    with patch("app.core.config.settings.LOCAL_STORAGE_DIR", test_storage_dir):
        pdf_path = report_service.generate_pdf(sample_report)
        assert os.path.exists(pdf_path)
        assert pdf_path.endswith(".pdf")
        assert test_storage_dir in pdf_path
