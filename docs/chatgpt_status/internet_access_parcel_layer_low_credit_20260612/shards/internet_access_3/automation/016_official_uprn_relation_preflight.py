#!/usr/bin/env python3
"""Preflight official UPRN, postcode-relation, licence and HMLR endpoints.

This worker validates source accessibility and signatures only. It does not
hydrate full releases, create parcel relations, or raise confidence.
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile
import urllib.request
from pathlib import Path
from typing import Any

SLOT_ID = "internet_access_3"

PROBES = [
    {
        "id": "os_open_uprn_product",
        "url": "https://www.ordnancesurvey.co.uk/products/os-open-uprn",
        "required": True,
        "signatures": ["OS Open UPRN", "every six weeks", "CSV", "GeoPackage"],
    },
    {
        "id": "os_open_uprn_documentation",
        "url": "https://docs.os.uk/os-downloads/products/addresses-and-names-portfolio/os-open-uprn",
        "required": True,
        "signatures": ["authoritative identifier", "OS Data Hub", "approximately 40 million"],
    },
    {
        "id": "ons_uprn_products",
        "url": "https://www.ons.gov.uk/methodology/geography/geographicalproducts/nationalstatisticsaddressproducts",
        "required": True,
        "signatures": ["National Statistics UPRN Lookup", "ONS UPRN Directory", "every six weeks", "CSV"],
    },
    {
        "id": "ons_uprn_licence",
        "url": "https://www.ons.gov.uk/methodology/geography/licences",
        "required": True,
        "signatures": ["UPRN products", "Open Government Licence", "GeoPlace"],
    },
    {
        "id": "ons_open_geography_portal",
        "url": "https://geoportal.statistics.gov.uk/",
        "required": False,
        "signatures": [],
    },
    {
        "id": "hmlr_inspire_july_2026",
        "url": "https://use-land-property-data.service.gov.uk/datasets/inspire/download",
        "required": True,
        "signatures": ["Download Index polygons", "5 July 2026", "local authority"],
    },
]


def args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--repo-root", type=Path)
    p.add_argument("--timeout", type=int, default=45)
    p.add_argument("--output-root", default="england_map_web/data/aays_21_slots/internet_access_3")
    p.add_argument("--runner-output", default="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/012_official_uprn_relation_preflight_latest.json")
    return p.parse_args()


def root(explicit: Path | None) -> Path:
    if explicit:
        return explicit.expanduser().resolve()
    for item in [Path.cwd(), *Path(__file__).resolve().parents]:
        if (item / "england_map_web").exists() and (item / "docs").exists():
            return item
    raise FileNotFoundError("repository root not found")


def atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
            handle.write("\n")
        os.replace(name, path)
    except Exception:
        try:
            os.unlink(name)
        except FileNotFoundError:
            pass
        raise


def probe(item: dict[str, Any], timeout: int) -> dict[str, Any]:
    request = urllib.request.Request(item["url"], headers={"User-Agent": "TerraYield-AAYS-internet-access-3/1.0", "Accept": "text/html,application/json;q=0.9,*/*;q=0.8"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(512000).decode("utf-8", errors="replace")
            content_type = response.headers.get("Content-Type")
            status = int(getattr(response, "status", 200))
            final_url = response.geturl()
        missing = [signature for signature in item["signatures"] if signature.lower() not in body.lower()]
        passed = status < 400 and not missing
        return {"id": item["id"], "required": item["required"], "url": item["url"], "final_url": final_url, "status": status, "content_type": content_type, "bytes_read": len(body.encode("utf-8")), "missing_signatures": missing, "passed": passed}
    except Exception as exc:
        return {"id": item["id"], "required": item["required"], "url": item["url"], "status": None, "missing_signatures": list(item["signatures"]), "passed": False, "error_type": type(exc).__name__, "error": str(exc)}


def main() -> int:
    parsed = args()
    repo = root(parsed.repo_root)
    results = [probe(item, parsed.timeout) for item in PROBES]
    required_failures = [item for item in results if item["required"] and not item["passed"]]
    optional_failures = [item for item in results if not item["required"] and not item["passed"]]
    summary = {
        "schema_version": 1,
        "slot_id": SLOT_ID,
        "state": "runtime_validation_passed" if not required_failures else "blocked",
        "result": {
            "probes_expected": len(PROBES),
            "probes_executed": len(results),
            "probes_passed": sum(1 for item in results if item["passed"]),
            "required_failures": len(required_failures),
            "optional_failures": len(optional_failures),
            "full_release_bytes_hydrated": 0,
            "parcel_relations_promoted": 0,
            "confidence_uplifts": 0,
            "actual_business_data_rows_written": 0
        },
        "probes": results,
        "validation": {
            "passed": not required_failures,
            "blockers": [f"REQUIRED_UPRN_SOURCE_PREFLIGHT_FAILED:{item['id']}" for item in required_failures] + ["CURRENT_OS_OPEN_UPRN_AND_ONSUD_RELEASE_BYTES_NOT_HYDRATED"]
        },
        "output_semantics": "OFFICIAL_SOURCE_ACCESS_AND_SIGNATURE_PREFLIGHT_ONLY",
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "first_unverified_step_after_run": "RESOLVE_CURRENT_OS_OPEN_UPRN_AND_ONSUD_OR_NSUL_RELEASE_DOWNLOADS_THEN_HYDRATE_EXACT_UPRN_RELATIONS"
    }
    atomic_json(repo / parsed.output_root / "official_uprn_relation_preflight_latest.json", summary)
    atomic_json(repo / parsed.runner_output, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not required_failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
