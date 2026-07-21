#!/usr/bin/env python3
from __future__ import annotations
import argparse
import importlib.util
import io
import json
import zipfile
from pathlib import Path


def load_module(script: Path):
    spec = importlib.util.spec_from_file_location("hmlr_downloader", script)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load HMLR downloader")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def zip_bytes(entries: list[tuple[str, bytes]]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries:
            archive.writestr(name, data)
    return buffer.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--downloader", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    module = load_module(args.downloader.resolve())
    checks: list[dict[str, object]] = []

    def run(name: str, fn) -> None:
        try:
            fn()
            checks.append({"check": name, "passed": True, "detail": ""})
        except Exception as exc:
            checks.append({"check": name, "passed": False, "detail": f"{type(exc).__name__}: {exc}"})

    def reject(name: str, fn, needle: str) -> None:
        try:
            fn()
            checks.append({"check": name, "passed": False, "detail": "no exception"})
        except Exception as exc:
            detail = f"{type(exc).__name__}: {exc}"
            checks.append({"check": name, "passed": needle in str(exc), "detail": detail})

    gml = b'<?xml version="1.0"?><FeatureCollection xmlns:gml="http://www.opengis.net/gml">' + b"x" * 100 + b"</FeatureCollection>"
    html = '''<table><tr><td>Royal Borough of Greenwich</td><td><a href="/datasets/inspire/download/Royal_Borough_of_Greenwich.zip">Download .gml</a></td></tr><tr><td>London Borough of Redbridge</td><td><a href="/datasets/inspire/download/London_Borough_of_Redbridge.gml">Download .gml</a></td></tr><tr><td>Evil</td><td><a href="https://evil.example/a.zip">Download .gml</a></td></tr></table>'''
    links = module.parse_authority_links(html)
    run("parse_zip_link", lambda: None if links[module.norm("Royal Borough of Greenwich")].endswith(".zip") else (_ for _ in ()).throw(AssertionError()))
    run("parse_raw_gml_link", lambda: None if links[module.norm("London Borough of Redbridge")].endswith(".gml") else (_ for _ in ()).throw(AssertionError()))
    run("reject_official_host_mismatch_by_omission", lambda: None if module.norm("Evil") not in links else (_ for _ in ()).throw(AssertionError()))
    run("extract_single_gml_zip", lambda: module.extract_gml_payload(zip_bytes([("Greenwich.gml", gml)]), "https://use-land-property-data.service.gov.uk/a.zip"))
    run("extract_single_xml_zip", lambda: module.extract_gml_payload(zip_bytes([("Greenwich.xml", gml)]), "https://use-land-property-data.service.gov.uk/a.zip"))
    run("accept_raw_gml", lambda: module.extract_gml_payload(gml, "https://use-land-property-data.service.gov.uk/a.gml"))
    reject("reject_no_gml_member", lambda: module.extract_gml_payload(zip_bytes([("readme.txt", b"x")]), "https://use-land-property-data.service.gov.uk/a.zip"), "exactly one")
    reject("reject_multiple_gml_members", lambda: module.extract_gml_payload(zip_bytes([("a.gml", gml), ("b.gml", gml)]), "https://use-land-property-data.service.gov.uk/a.zip"), "exactly one")
    reject("reject_zip_slip_parent", lambda: module.extract_gml_payload(zip_bytes([("../a.gml", gml)]), "https://use-land-property-data.service.gov.uk/a.zip"), "unsafe ZIP")
    reject("reject_zip_slip_absolute", lambda: module.extract_gml_payload(zip_bytes([("/a.gml", gml)]), "https://use-land-property-data.service.gov.uk/a.zip"), "unsafe ZIP")
    reject("reject_fake_zip", lambda: module.extract_gml_payload(b"notzip", "https://use-land-property-data.service.gov.uk/a.zip"), "valid ZIP")
    reject("reject_tiny_gml", lambda: module.extract_gml_payload(b"<?xml?><x/>", "https://use-land-property-data.service.gov.uk/a.gml"), "too small")
    reject("reject_non_xml_raw", lambda: module.extract_gml_payload(b"x" * 200, "https://use-land-property-data.service.gov.uk/a.gml"), "does not look")
    payload = {"slot_id": "future_growth_2", "candidates": [{"local_authority": "Royal Borough of Greenwich"}, {"local_authority": "Royal Borough of Greenwich"}, {"local_authority": "Other"}]}
    run("candidate_authorities_deduplicated", lambda: None if module.candidate_authorities(payload) == ["Royal Borough of Greenwich"] else (_ for _ in ()).throw(AssertionError()))

    result = {
        "schema_version": 1,
        "slot_id": "future_growth_2",
        "executed": True,
        "test_type": "actual_hmlr_zip_transport_and_secure_extraction_regression",
        "checks_passed": sum(bool(c["passed"]) for c in checks),
        "checks_total": len(checks),
        "all_passed": all(bool(c["passed"]) for c in checks),
        "checks": checks,
        "actual_hmlr_downloads": 0,
        "actual_exact_intersections": 0,
        "canonical_parcel_matches": 0,
        "future_growth_scores_produced": 0,
        "actual_business_data_rows_written": 0,
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
    return 0 if result["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
