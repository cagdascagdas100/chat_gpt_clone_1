from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.routes import contractor as contractor_routes
from app.api.routes import estate_agents as estate_agent_routes
from app.main import app


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _prepare_dataset(root: Path) -> None:
    _write(
        root / "estate_agent_verified_final.csv",
        "\n".join(
            [
                "agent_id,candidate_id,company_name,agent_or_branch_name,phone,email,website_url,office_address,postcode,region,trust_score_10,overall_data_truth_score_4,contact_status",
                "A1,C1,Alpha Estates,Alpha Branch,111,a@alpha.example,https://alpha.example,Addr1,PC1,North,9,3.6,READY",
                "A2,C2,Beta Estates,Beta Branch,222,b@beta.example,https://beta.example,Addr2,PC2,North,6,3.9,READY",
                "A3,C3,Gamma Estates,Gamma Branch,333,c@gamma.example,https://gamma.example,Addr3,PC3,South,4,2.7,READY",
            ]
        ),
    )
    _write(
        root / "estate_agent_evidence_sources_final.csv",
        "\n".join(
            [
                "agent_id,candidate_id,source_file,source_type,source_url,truth_score_source_4,candidate_text_excerpt",
                "A1,C1,ev1.csv,csv,https://evidence-1.example,4,text-1",
                "A2,C2,ev2.csv,csv,https://evidence-2.example,4,text-2",
                "A3,C3,ev3.csv,csv,https://evidence-3.example,3,text-3",
            ]
        ),
    )
    _write(
        root / "estate_agent_coverage_groups_final.csv",
        "\n".join(
            [
                "agent_id,candidate_id,parcel_group_id,coverage_method,coverage_truth_score_4,source_url,source_file,notes",
                "A1,C1,G1,authority_match,4,https://coverage-1.example,cov1.csv,n1",
                "A2,C2,G1,authority_match,3,https://coverage-2.example,cov2.csv,n2",
                "A3,C3,G2,authority_match,4,https://coverage-3.example,cov3.csv,n3",
            ]
        ),
    )
    _write(
        root / "terrayield_parcel_group_join_final.csv",
        "\n".join(
            [
                "program_parcel_id,parcel_group_id,match_method,match_confidence,source_file,geometry_field,notes",
                "101,G1,exact,3,join.csv,geo,n1",
                "102,G2,exact,3,join.csv,geo,n2",
            ]
        ),
    )
    _write(
        root / "estate023_final_acceptance_audit.csv",
        "\n".join(
            [
                "check,value,status",
                "DB_WRITE,false,pass",
                "PRODUCTION_DEPLOY,false,pass",
                "FAKE_DATA,false,pass",
                "FINAL_ACCEPTANCE,true,pass",
            ]
        ),
    )
    (root / "TerraYield_Emlakci_Parsel_Eslesme_FINAL.xlsx").write_bytes(b"x" * 1201)


def _fake_settings(tmp_path: Path) -> SimpleNamespace:
    root = tmp_path / "estate_agents"
    _prepare_dataset(root)
    contractor_root = tmp_path / "contractor"
    return SimpleNamespace(
        estate_agent_final_root=root,
        estate_agent_fallback_roots="",
        estate_agent_strict_mode=True,
        contractor_storage_root=contractor_root,
        contractor_export_root=contractor_root / "exports",
        contractor_manifest_root=contractor_root / "manifests",
        contractor_preflight_audit_path=tmp_path / "bridge" / "audit.json",
    )


def test_estate_agents_by_parcel_returns_only_matching_and_sorted(monkeypatch, tmp_path: Path) -> None:
    settings = _fake_settings(tmp_path)
    monkeypatch.setattr(estate_agent_routes, "get_settings", lambda: settings)
    response = TestClient(app).get("/api/estate-agents/by-parcel/101?limit=10")
    assert response.status_code == 200
    payload = response.json()
    assert payload["dataset_available"] is True
    assert payload["parcel_group_ids"] == ["G1"]
    assert payload["total_agents"] == 2
    assert [row["agent_id"] for row in payload["agents"]] == ["A1", "A2"]
    assert payload["agents"][0]["trust_score_10"] >= payload["agents"][1]["trust_score_10"]


def test_estate_agents_by_unknown_parcel_returns_empty(monkeypatch, tmp_path: Path) -> None:
    settings = _fake_settings(tmp_path)
    monkeypatch.setattr(estate_agent_routes, "get_settings", lambda: settings)
    response = TestClient(app).get("/api/estate-agents/by-parcel/999999?limit=10")
    assert response.status_code == 200
    payload = response.json()
    assert payload["dataset_available"] is True
    assert payload["parcel_group_ids"] == []
    assert payload["agents"] == []


def test_estate_agents_dry_run_validate_exposes_no_write_flags(monkeypatch, tmp_path: Path) -> None:
    settings = _fake_settings(tmp_path)
    monkeypatch.setattr(estate_agent_routes, "get_settings", lambda: settings)
    response = TestClient(app).get("/api/estate-agents/dry-run/validate")
    assert response.status_code == 200
    payload = response.json()
    assert payload["dataset_available"] is True
    assert payload["FINAL_ACCEPTANCE"] is True
    assert payload["audit"]["DB_WRITE"] is False
    assert payload["audit"]["PRODUCTION_DEPLOY"] is False
    assert payload["audit"]["FAKE_DATA"] is False


def test_contractor_contacts_uses_estate_agent_dataset(monkeypatch, tmp_path: Path) -> None:
    settings = _fake_settings(tmp_path)
    monkeypatch.setattr(estate_agent_routes, "get_settings", lambda: settings)
    monkeypatch.setattr(contractor_routes, "get_settings", lambda: settings)
    response = TestClient(app).get("/api/contractor/parcel/101/contacts?limit=10")
    assert response.status_code == 200
    payload = response.json()
    assert payload["integration_mode"] == "estate_agent_read_only"
    assert payload["parcel_group_ids"] == ["G1"]
    assert payload["total_rows"] == 2
    assert [row["contractor_id"] for row in payload["rows"]] == ["A1", "A2"]
    assert payload["final_audit"]["DB_WRITE"] is False


def test_contractor_contacts_unknown_parcel_returns_empty_no_fallback(monkeypatch, tmp_path: Path) -> None:
    settings = _fake_settings(tmp_path)
    monkeypatch.setattr(estate_agent_routes, "get_settings", lambda: settings)
    monkeypatch.setattr(contractor_routes, "get_settings", lambda: settings)
    response = TestClient(app).get("/api/contractor/parcel/999999/contacts?limit=10")
    assert response.status_code == 200
    payload = response.json()
    assert payload["integration_mode"] == "estate_agent_read_only"
    assert payload["total_rows"] == 0
    assert payload["rows"] == []
