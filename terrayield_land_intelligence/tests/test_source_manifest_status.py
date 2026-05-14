from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from app.services.admin_service import _build_listing_manifest_gaps
from app.services.source_manifest_status import (
    derive_manifest_availability,
    summarize_facilities_manifest_entries,
    summarize_listing_manifest_entries,
)
from app.services.source_service import _build_source_status_notes
from app.etl.validate_live_listing_manifests import main as validate_live_listing_manifests_main


def test_summarize_listing_manifest_entries_counts_live_ready_and_demo() -> None:
    manifest_path = Path(__file__)
    status = summarize_listing_manifest_entries(
        [
            {
                "provider_name": "licensed_vendor",
                "provider_kind": "vendor_export",
                "license_scope": "licensed_export",
                "input_format": "csv",
                "truth_tier": "licensed",
                "active": True,
                "file_drop_path": Path(__file__).name,
            },
            {
                "provider_name": "sample_csv",
                "provider_kind": "demo",
                "license_scope": "internal_sample",
                "truth_tier": "demo",
                "is_demo": True,
                "active": True,
                "file_drop_path": Path(__file__).name,
            },
        ],
        manifest_path=manifest_path,
        container_key="providers",
        source_name="market_listing_adapter",
    )

    assert status["manifest_entries"] == 2
    assert status["active_entries"] == 2
    assert status["demo_entries"] == 1
    assert status["live_ready_entries"] == 1
    assert status["has_live_ready_manifest"] is True
    assert derive_manifest_availability(status) == "live_ready"


def test_derive_manifest_availability_prefers_missing_files_over_demo_only() -> None:
    status = {
        "manifest_exists": True,
        "parse_error": None,
        "has_live_ready_manifest": False,
        "missing_active_files": ["missing.csv"],
        "has_demo_only_manifest": True,
        "active_entries": 1,
        "manifest_entries": 1,
    }

    assert derive_manifest_availability(status) == "missing_files"


def test_build_source_status_notes_attaches_manifest_status(monkeypatch) -> None:
    def fake_inspect(source_name: str, settings: object) -> dict[str, object]:
        assert source_name == "market_listing_adapter"
        return {
            "availability": "demo_only",
            "manifest_exists": True,
            "active_entries": 1,
            "demo_entries": 1,
            "live_ready_entries": 0,
            "missing_active_files": [],
            "active_provider_names": ["sample_csv"],
        }

    monkeypatch.setattr("app.services.source_service.inspect_configured_manifest_status", fake_inspect)

    notes = _build_source_status_notes(
        "market_listing_adapter",
        {"snapshot_key": "market-1"},
        SimpleNamespace(),
    )

    assert notes["snapshot_key"] == "market-1"
    assert notes["manifest_status"]["availability"] == "demo_only"
    assert notes["manifest_status"]["active_provider_names"] == ["sample_csv"]
    assert notes["source_confidence"]["needs_review"] is True
    assert notes["source_confidence"]["review_route"] == "source_confidence_review"
    assert notes["source_confidence"]["origin"] == "source_status"
    assert "missing_source_url" in notes["source_confidence"]["reasons"]


def test_summarize_facilities_manifest_entries_counts_download_mode_as_live_ready() -> None:
    status = summarize_facilities_manifest_entries(
        [
            {
                "name": "gias_live",
                "mode": "download",
                "download_url": "https://example.com/gias.csv",
                "input_format": "csv",
                "source_priority": "authoritative",
                "active": True,
            }
        ],
        manifest_path=Path(__file__),
        container_key="sources",
        source_name="gias_facilities",
    )

    assert status["manifest_entries"] == 1
    assert status["active_entries"] == 1
    assert status["live_ready_entries"] == 1
    assert status["missing_active_files"] == []
    assert status["manifest_rows"][0]["mode"] == "download"
    assert status["manifest_rows"][0]["download_ready"] is True
    assert derive_manifest_availability(status) == "live_ready"


def test_build_listing_manifest_gaps_reports_demo_only_market_feed() -> None:
    gaps = _build_listing_manifest_gaps(
        "market_listing_adapter",
        manifest_status={
            "manifest_exists": True,
            "parse_error": None,
            "missing_active_files": [],
            "has_demo_only_manifest": True,
            "has_live_ready_manifest": False,
        },
        row_count=0,
    )

    assert [gap.code for gap in gaps] == ["market_listing_adapter_demo_only"]


def test_build_listing_manifest_gaps_reports_inactive_manifest() -> None:
    gaps = _build_listing_manifest_gaps(
        "government_property_finder",
        manifest_status={
            "manifest_exists": True,
            "parse_error": None,
            "missing_active_files": [],
            "has_demo_only_manifest": False,
            "has_live_ready_manifest": False,
            "availability": "inactive_only",
        },
        row_count=0,
    )

    assert [gap.code for gap in gaps] == ["government_property_finder_manifest_inactive"]


def test_validate_live_listing_manifests_require_live(monkeypatch, capsys) -> None:
    monkeypatch.setattr("app.etl.validate_live_listing_manifests.get_settings", lambda: SimpleNamespace())

    def fake_inspect(source_name: str, settings: object) -> dict[str, object]:
        return {
            "manifest_path": f"C:/fake/{source_name}.json",
            "availability": "inactive_only",
            "active_entries": 0,
            "live_ready_entries": 0,
            "demo_entries": 0,
            "has_live_ready_manifest": False,
            "active_provider_names": [],
            "missing_active_files": [],
        }

    monkeypatch.setattr("app.etl.validate_live_listing_manifests.inspect_configured_listing_manifest_status", fake_inspect)

    exit_code = validate_live_listing_manifests_main(["--require-live"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "live_ready_sources: none" in output


def test_validate_live_listing_manifests_passes_when_live_feed_exists(monkeypatch, capsys) -> None:
    monkeypatch.setattr("app.etl.validate_live_listing_manifests.get_settings", lambda: SimpleNamespace())

    def fake_inspect(source_name: str, settings: object) -> dict[str, object]:
        is_market = source_name == "market_listing_adapter"
        return {
            "manifest_path": f"C:/fake/{source_name}.json",
            "availability": "live_ready" if is_market else "inactive_only",
            "active_entries": 1 if is_market else 0,
            "live_ready_entries": 1 if is_market else 0,
            "demo_entries": 0,
            "has_live_ready_manifest": is_market,
            "active_provider_names": ["licensed_vendor"] if is_market else [],
            "missing_active_files": [],
        }

    monkeypatch.setattr("app.etl.validate_live_listing_manifests.inspect_configured_listing_manifest_status", fake_inspect)

    exit_code = validate_live_listing_manifests_main(["--require-live"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "live_ready_sources: market_listing_adapter" in output
