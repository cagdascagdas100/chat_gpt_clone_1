from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.routes import contractor as contractor_routes
from app.main import app


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _fake_settings(tmp_path: Path) -> SimpleNamespace:
    storage_root = tmp_path / "contractor"
    export_root = storage_root / "exports"
    manifest_root = storage_root / "manifests"
    preflight_path = tmp_path / "bridge" / "ai-results" / "terrayield-079-contractor-db-env-loader-preflight.audit.json"
    return SimpleNamespace(
        contractor_storage_root=storage_root,
        contractor_export_root=export_root,
        contractor_manifest_root=manifest_root,
        contractor_preflight_audit_path=preflight_path,
    )


def test_contractor_status_completed(monkeypatch, tmp_path: Path) -> None:
    settings = _fake_settings(tmp_path)
    _write_json(
        settings.contractor_preflight_audit_path,
        {
            "status": "completed",
            "db_credentials_present": True,
            "connection_ok": True,
            "db_query_ok": True,
            "project_root": "C:/should/not/be/exposed",
            "next_action": "Proceed without exposing path details.",
        },
    )
    _write_json(settings.contractor_manifest_root / "postgres_load_manifest.json", {"loaded_companies": 160})
    _write_json(settings.contractor_manifest_root / "parcel_match_manifest.json", {"match_count": 29})
    _write_json(settings.contractor_export_root / "export_manifest.json", {"parcel_match_count": 29})

    monkeypatch.setattr(contractor_routes, "get_settings", lambda: settings)
    response = TestClient(app).get("/api/contractor/status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["manifests"]["postgres_load"]["loaded_companies"] == 160
    assert payload["manifests"]["parcel_match"]["match_count"] == 29
    assert payload["postgres_load_manifest"]["loaded_companies"] == 160
    assert payload["parcel_match_manifest"]["match_count"] == 29
    assert payload["preflight_audit"]["db_query_ok"] is True
    assert "project_root" not in payload["preflight_audit"]
    assert "next_action" not in payload["preflight_audit"]
    assert payload["warnings"] == []


def test_contractor_export_contractors_pagination(monkeypatch, tmp_path: Path) -> None:
    settings = _fake_settings(tmp_path)
    settings.contractor_export_root.mkdir(parents=True, exist_ok=True)
    (settings.contractor_export_root / "contractors_for_app.csv").write_text(
        "\n".join(
            [
                "contractor_id,company_name,do_not_contact",
                "c1,Alpha,false",
                "c2,Beta,true",
                "c3,Gamma,false",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(contractor_routes, "get_settings", lambda: settings)
    response = TestClient(app).get("/api/contractor/exports/contractors?offset=1&limit=1")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_rows"] == 3
    assert len(payload["rows"]) == 1
    assert payload["rows"][0]["contractor_id"] == "c2"


def test_contractor_export_parcel_match_filter(monkeypatch, tmp_path: Path) -> None:
    settings = _fake_settings(tmp_path)
    settings.contractor_export_root.mkdir(parents=True, exist_ok=True)
    (settings.contractor_export_root / "contractor_parcel_matches_for_app.csv").write_text(
        "\n".join(
            [
                "parcel_id,contractor_id,match_method",
                "101,c1,geometry_intersection",
                "102,c2,authority_postcode_proxy",
                "101,c3,region_fallback_review",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(contractor_routes, "get_settings", lambda: settings)
    response = TestClient(app).get("/api/contractor/exports/parcel-matches?parcel_id=101")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_rows"] == 2
    assert len(payload["rows"]) == 2
    assert all(row["parcel_id"] == "101" for row in payload["rows"])


def test_contractor_parcel_match_preview(monkeypatch, tmp_path: Path) -> None:
    settings = _fake_settings(tmp_path)
    settings.contractor_export_root.mkdir(parents=True, exist_ok=True)
    (settings.contractor_export_root / "contractor_parcel_matches_for_app.csv").write_text(
        "\n".join(
            [
                "parcel_id,contractor_id,match_method",
                "101,c1,geometry_intersection",
                "102,c2,authority_postcode_proxy",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(contractor_routes, "get_settings", lambda: settings)
    response = TestClient(app).get("/api/contractor/exports/parcel-matches/preview?limit=1")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_rows"] == 2
    assert payload["offset"] == 0
    assert payload["limit"] == 1
    assert len(payload["rows"]) == 1
    assert payload["rows"][0]["parcel_id"] == "101"


def test_contractor_parcel_contacts_filters_do_not_contact(monkeypatch, tmp_path: Path) -> None:
    settings = _fake_settings(tmp_path)
    settings.contractor_export_root.mkdir(parents=True, exist_ok=True)
    (settings.contractor_export_root / "contractors_for_app.csv").write_text(
        "\n".join(
            [
                "contractor_id,company_name,reliability_score,data_confidence_score,legal_contact_score,do_not_contact,contact_status",
                "c1,Alpha Build,90,88,77,false,READY",
                "c2,Beta Build,95,91,35,true,DO_NOT_CONTACT",
            ]
        ),
        encoding="utf-8",
    )
    (settings.contractor_export_root / "contractor_parcel_matches_for_app.csv").write_text(
        "\n".join(
            [
                "parcel_id,contractor_id,match_method,match_score,contact_readiness",
                "101,c1,geometry_intersection,84,READY",
                "101,c2,authority_postcode_proxy,88,DO_NOT_CONTACT",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(contractor_routes, "get_settings", lambda: settings)
    response = TestClient(app).get("/api/contractor/parcel/101/contacts?limit=10")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_rows"] == 2
    assert payload["ready_rows"] == 1
    assert payload["blocked_rows"] == 1
    assert len(payload["rows"]) == 1
    assert payload["rows"][0]["contractor_id"] == "c1"
    assert payload["rows"][0]["contact_allowed"] is True


def test_contractor_parcel_contacts_include_blocked(monkeypatch, tmp_path: Path) -> None:
    settings = _fake_settings(tmp_path)
    settings.contractor_export_root.mkdir(parents=True, exist_ok=True)
    (settings.contractor_export_root / "contractors_for_app.csv").write_text(
        "\n".join(
            [
                "contractor_id,company_name,reliability_score,data_confidence_score,legal_contact_score,do_not_contact,contact_status",
                "c1,Alpha Build,90,88,77,false,READY",
                "c2,Beta Build,95,91,35,true,DO_NOT_CONTACT",
            ]
        ),
        encoding="utf-8",
    )
    (settings.contractor_export_root / "contractor_parcel_matches_for_app.csv").write_text(
        "\n".join(
            [
                "parcel_id,contractor_id,match_method,match_score,contact_readiness",
                "101,c1,geometry_intersection,84,READY",
                "101,c2,authority_postcode_proxy,88,DO_NOT_CONTACT",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(contractor_routes, "get_settings", lambda: settings)
    response = TestClient(app).get("/api/contractor/parcel/101/contacts?limit=10&include_blocked=true")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["rows"]) == 2
    assert payload["rows"][0]["contractor_id"] == "c1"
    assert payload["rows"][1]["contractor_id"] == "c2"
    assert payload["rows"][1]["contact_allowed"] is False


def test_contractor_parcel_contacts_filters_by_structure_type(monkeypatch, tmp_path: Path) -> None:
    settings = _fake_settings(tmp_path)
    settings.contractor_export_root.mkdir(parents=True, exist_ok=True)
    (settings.contractor_export_root / "contractors_for_app.csv").write_text(
        "\n".join(
            [
                "contractor_id,company_name,reliability_score,data_confidence_score,legal_contact_score,do_not_contact,contact_status,structure_types",
                "c1,Alpha Build,90,88,77,false,READY,residential;detached",
                "c2,Office Build,93,92,80,false,READY,office;commercial",
            ]
        ),
        encoding="utf-8",
    )
    (settings.contractor_export_root / "contractor_parcel_matches_for_app.csv").write_text(
        "\n".join(
            [
                "parcel_id,contractor_id,match_method,match_score,contact_readiness",
                "101,c1,geometry_intersection,84,READY",
                "101,c2,authority_postcode_proxy,88,READY",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(contractor_routes, "get_settings", lambda: settings)
    response = TestClient(app).get("/api/contractor/parcel/101/contacts?limit=10&structure_type=ofis")
    assert response.status_code == 200
    payload = response.json()
    assert payload["structure_type"] == "ofis"
    assert payload["total_rows"] == 1
    assert len(payload["rows"]) == 1
    assert payload["rows"][0]["contractor_id"] == "c2"
