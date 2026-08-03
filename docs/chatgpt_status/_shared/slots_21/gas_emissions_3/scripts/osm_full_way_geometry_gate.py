#!/usr/bin/env python3
"""Fetch two official OSM full-way XML documents and validate site polygons fail-closed."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--prior", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--fixture-dir", type=Path)
    return parser.parse_args()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def point_on_segment(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> bool:
    cross = (px - ax) * (by - ay) - (py - ay) * (bx - ax)
    if not math.isclose(cross, 0.0, abs_tol=1e-12):
        return False
    return min(ax, bx) - 1e-12 <= px <= max(ax, bx) + 1e-12 and min(ay, by) - 1e-12 <= py <= max(ay, by) + 1e-12


def point_in_polygon(lon: float, lat: float, coords: list[list[float]]) -> tuple[bool, bool]:
    inside = False
    boundary = False
    for i in range(len(coords) - 1):
        ax, ay = coords[i]
        bx, by = coords[i + 1]
        if point_on_segment(lon, lat, ax, ay, bx, by):
            boundary = True
            inside = True
            break
        if (ay > lat) != (by > lat):
            x_intersection = (bx - ax) * (lat - ay) / (by - ay) + ax
            if lon < x_intersection:
                inside = not inside
    return inside, boundary


def parse_way_xml(raw: bytes, target: dict[str, Any]) -> dict[str, Any]:
    root = ET.fromstring(raw)
    way_id = str(target["way_id"])
    way = next((item for item in root.findall("way") if item.get("id") == way_id), None)
    require(way is not None, f"way {way_id} missing")
    nodes: dict[str, list[float]] = {}
    for node in root.findall("node"):
        node_id = node.get("id")
        lat = node.get("lat")
        lon = node.get("lon")
        if node_id and lat is not None and lon is not None:
            nodes[node_id] = [float(lon), float(lat)]
    refs = [item.get("ref") for item in way.findall("nd")]
    require(all(ref for ref in refs), "empty node reference")
    require(len(refs) <= int(target.get("maximum_nodes", 5000)), "way exceeds node limit")
    unresolved = [ref for ref in refs if ref not in nodes]
    require(not unresolved, f"unresolved node references: {len(unresolved)}")
    coords = [nodes[str(ref)] for ref in refs]
    closed = len(coords) >= 4 and refs[0] == refs[-1] and coords[0] == coords[-1]
    locator = target["locator"]
    inside, boundary = point_in_polygon(float(locator["longitude"]), float(locator["latitude"]), coords) if closed else (False, False)
    tags = {item.get("k", ""): item.get("v", "") for item in way.findall("tag") if item.get("k")}
    validated = closed and inside
    return {"way_id": int(way_id), "node_reference_count": len(refs), "unique_node_count": len(set(refs)), "unresolved_node_count": 0, "closed_polygon": closed, "locator_inside_or_boundary": inside, "locator_on_boundary": boundary, "geometry_validated": validated, "tags": tags, "geometry_coordinates_lon_lat": coords}


def fetch_target(target: dict[str, Any], policy: dict[str, Any], fixture_dir: Path | None) -> dict[str, Any]:
    way_id = int(target["way_id"])
    url = str(target["source_url"])
    base: dict[str, Any] = {"target_id": target["target_id"], "site_name": target["site_name"], "way_id": way_id, "source_url": url, "attempt_completed": True, "http_status": None, "response_sha256": None, "response_bytes": 0, "geometry_validated": False, "decision": "NO_DATA_CONTINUE", "error": None}
    try:
        if fixture_dir:
            raw = (fixture_dir / f"way_{way_id}.osm").read_bytes()
            status = 200
        else:
            request = urllib.request.Request(url, headers={"User-Agent": "AAYS-OSM-Way-Geometry-Gate/1.0", "Accept": "application/xml,text/xml"}, method="GET")
            with urllib.request.urlopen(request, timeout=int(policy["per_target_timeout_seconds"])) as response:
                status = int(getattr(response, "status", response.getcode()))
                raw = response.read(int(policy["maximum_response_bytes"]) + 1)
        require(status == 200, f"unexpected HTTP status {status}")
        require(len(raw) <= int(policy["maximum_response_bytes"]), "response exceeds byte limit")
        parsed = parse_way_xml(raw, target)
        base.update({"http_status": status, "response_sha256": sha256_bytes(raw), "response_bytes": len(raw), **parsed, "decision": "GEOMETRY_VALIDATED" if parsed["geometry_validated"] else "NO_DATA_CONTINUE"})
    except urllib.error.HTTPError as exc:
        base["http_status"] = int(exc.code)
        base["error"] = f"HTTPError: {exc.code} {exc.reason}"[:500]
    except Exception as exc:
        base["error"] = f"{type(exc).__name__}: {exc}"[:500]
    return base


def main() -> int:
    args = parse_args()
    contract_bytes = args.contract.read_bytes()
    prior_bytes = args.prior.read_bytes()
    contract = json.loads(contract_bytes)
    prior = json.loads(prior_bytes)
    require(contract.get("schema_version") == 3, "contract schema mismatch")
    require(contract.get("slot_id") == "gas_emissions_3", "slot mismatch")
    require(contract.get("state") == "READY", "contract must be READY")
    require(contract.get("claimable") is True and contract.get("ready_for_claim") is True, "contract not claimable")
    precondition = contract.get("precondition") or {}
    require(sha256_bytes(prior_bytes) == precondition.get("prior_output_sha256"), "prior SHA mismatch")
    require(prior.get("task_batch") == 257, "unexpected prior batch")
    require(prior.get("state") == "NO_DATA_CONTINUE", "unexpected prior state")
    require(prior.get("next_unverified_step") == "ACQUIRE_RAW_CADASTRAL_GEOMETRY_OR_VERIFIED_INSPIRE_IDS", "unexpected prior next step")
    manifest = contract.get("source_evidence_manifest") or {}
    for field in ("source_url", "accessed_at", "content_sha256", "supports_fields", "relevant_record_ids_or_excerpt", "license_or_terms_url"):
        require(manifest.get(field), f"missing source manifest field {field}")
    targets = contract.get("runtime_targets")
    require(isinstance(targets, list) and len(targets) == 2, "exactly two targets required")
    policy = contract.get("network_policy") or {}
    results = [fetch_target(target, policy, args.fixture_dir) for target in targets]
    completed = sum(bool(item["attempt_completed"]) for item in results)
    validated = sum(bool(item.get("geometry_validated")) for item in results)
    target_count = len(targets)
    state = "GEOMETRIES_VALIDATED" if validated == target_count else "NO_DATA_CONTINUE"
    next_step = "USE_VALIDATED_OPEN_SITE_POLYGONS_AS_NON_CADASTRAL_SPATIAL_CARRIERS_FOR_NEXT_EMISSIONS_SOURCE_MATCHING" if state == "GEOMETRIES_VALIDATED" else "ADVANCE_TO_NEXT_UNVERIFIED_GAS_EMISSIONS_SOURCE_AFTER_OSM_GEOMETRY_NO_DATA"
    output = {"schema_version": 3, "architecture_version": 3, "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1", "slot_id": "gas_emissions_3", "task_id": contract["task_id"], "continuation_key": contract["continuation_key"], "state": state, "panel_status": "PUBLISHED" if state == "GEOMETRIES_VALIDATED" else "BİLGİ TOPLANIYOR", "execution_mode": "SYNTHETIC_FIXTURE" if args.fixture_dir else "LIVE_NETWORK", "first_unverified_step_completed": contract["first_unverified_step"], "next_unverified_step": next_step, "input": {"contract_path": args.contract.as_posix(), "contract_sha256": sha256_bytes(contract_bytes), "prior_output_path": args.prior.as_posix(), "prior_output_sha256": sha256_bytes(prior_bytes)}, "counts": {"completed_count": completed, "target_count": target_count, "geometry_fetch_attempts": completed, "raw_way_xml_documents": sum(bool(item.get("response_sha256")) for item in results), "closed_site_polygons": sum(bool(item.get("closed_polygon")) for item in results), "locator_containment_validations": sum(bool(item.get("locator_inside_or_boundary")) for item in results), "validated_open_site_geometries": validated, "verified_inspire_ids": 0, "parcel_bindings": 0}, "progress_percent": round(completed / target_count * 100, 6), "targets": results, "decision": {"open_site_geometry_is_not_cadastral_parcel_geometry": True, "inferred_values": 0, "fake_data": False}}
    require(completed == target_count, "not all attempts completed")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temp = args.output.with_suffix(args.output.suffix + ".tmp")
    temp.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    temp.replace(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
