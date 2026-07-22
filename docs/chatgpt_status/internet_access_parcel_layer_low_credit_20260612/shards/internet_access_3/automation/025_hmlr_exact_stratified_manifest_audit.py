#!/usr/bin/env python3
"""Audit the exact stratified manifest against ONSPD and HMLR INSPIRE polygons.

Every selected row identity comes from stratified_candidate_manifest_latest.json.
The worker uses streaming GML parsing and selects the largest exterior ring for each
matched INSPIRE identifier. Evidence remains indicative and is never promoted.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

SLOT_ID = "internet_access_3"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--repo-root", type=Path, required=True)
    p.add_argument("--rows", default="england_map_web/data/aays_21_slots/internet_access_3/internet_rows_latest.json")
    p.add_argument("--manifest", default="england_map_web/data/aays_21_slots/internet_access_3/stratified_candidate_manifest_latest.json")
    p.add_argument("--onspd-registry", default="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/source_snapshots/003_onspd_may_2026_registry_latest.json")
    p.add_argument("--hmlr-registry", default="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/source_snapshots/004_hmlr_inspire_july_2026_registry_latest.json")
    p.add_argument("--output-root", default="england_map_web/data/aays_21_slots/internet_access_3")
    p.add_argument("--runner-output", default="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/019_hmlr_exact_stratified_manifest_audit_latest.json")
    p.add_argument("--sample-size", type=int, default=384)
    p.add_argument("--minimum-match-ratio", type=float, default=0.90)
    p.add_argument("--timeout", type=int, default=180)
    return p.parse_args()


def load(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
            handle.write("\n")
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def import_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def ring_area(ring: list[tuple[float, float]]) -> float:
    if len(ring) < 4:
        return 0.0
    return abs(sum(ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1] for i in range(len(ring) - 1))) / 2.0


def find_largest_rings(legacy: Any, gml_files: list[Path], target_ids: set[str]) -> tuple[dict[str, list[tuple[float, float]]], dict[str, Any]]:
    found: dict[str, list[tuple[float, float]]] = {}
    scanned_elements = 0
    matched_elements = 0
    multiple_ring_elements = 0
    for path in gml_files:
        for _event, element in ET.iterparse(path, events=("end",)):
            if local(element.tag) != "cadastralparcel":
                continue
            scanned_elements += 1
            texts = {text.strip() for text in element.itertext() if text and text.strip()}
            matches = target_ids & texts
            if not matches:
                element.clear()
                continue
            matched_elements += 1
            rings = []
            for child in element.iter():
                if local(child.tag) in {"poslist", "coordinates"} and child.text:
                    ring = legacy.parse_ring(child.text)
                    if ring:
                        rings.append(ring)
            if len(rings) > 1:
                multiple_ring_elements += 1
            if rings:
                largest = max(rings, key=ring_area)
                for inspire_id in matches:
                    prior = found.get(inspire_id)
                    if prior is None or ring_area(largest) > ring_area(prior):
                        found[inspire_id] = largest
            element.clear()
    return found, {
        "gml_files_scanned": len(gml_files),
        "cadastral_elements_scanned": scanned_elements,
        "matched_elements": matched_elements,
        "multiple_ring_elements": multiple_ring_elements,
        "largest_exterior_ring_policy": True,
        "streaming_iterparse": True,
    }


def update_feed(output_root: Path, summary: dict[str, Any]) -> None:
    path = output_root / "operation_feed_revision8_runtime_latest.json"
    feed = load(path) if path.exists() else {"schema_version": 1, "slot_id": SLOT_ID, "operations": []}
    operations = list(feed.get("operations") or [])
    sequence = max([int(item.get("sequence", 0)) for item in operations] or [0]) + 1
    operations.append({
        "sequence": sequence,
        "status": "PASS" if summary["validation"]["passed"] else "BLOCKED",
        "operation": "HMLR_EXACT_STRATIFIED_MANIFEST_AUDIT",
        "detail": f"selected={summary['result']['sample_rows_selected']}; polygons={summary['result']['inspire_polygons_found']}; onspd={summary['result']['onspd_exact_postcodes_found']}; minimum={summary['guard']['minimum_matches_required']}; exact_manifest_identity=true; confidence_not_raised",
    })
    feed.update({"updated_at": summary["updated_at"], "display_mode": "line_by_line", "final_ready": False, "operations": operations, "safety": {"fake_data": False, "db_write": False, "migration": False, "production_deploy": False}})
    write(path, feed)


def main() -> int:
    options = parse_args()
    if not 0 < options.minimum_match_ratio <= 1:
        raise ValueError("minimum-match-ratio must be within (0,1]")
    repo = options.repo_root.expanduser().resolve()
    automation = Path(__file__).resolve().parent
    legacy = import_module(automation / "008_hmlr_inspire_postcode_centroid_polygon_audit.py", "hmlr_legacy_helpers")
    guard = import_module(automation / "010_hmlr_revision6_guarded_entry.py", "hmlr_guard_helpers")
    rows = load(repo / options.rows)
    manifest = load(repo / options.manifest)
    onspd_registry = load(repo / options.onspd_registry)
    hmlr_registry = load(repo / options.hmlr_registry)
    if not isinstance(rows, list) or len(rows) != 30761:
        raise ValueError("full migrated rows missing or wrong count")
    if not isinstance(manifest, list) or len(manifest) != options.sample_size:
        raise ValueError("stratified manifest missing or wrong count")
    row_lookup = {int(row["row_no"]): row for row in rows}
    manifest_ids = [int(item["row_no"]) for item in manifest]
    if len(set(manifest_ids)) != len(manifest_ids):
        raise ValueError("duplicate manifest row identities")
    missing_rows = [row_no for row_no in manifest_ids if row_no not in row_lookup]
    if missing_rows:
        raise ValueError(f"manifest rows missing from migrated rows: {missing_rows[:20]}")
    selected = [row_lookup[row_no] for row_no in manifest_ids]
    invalid_rows = [int(row["row_no"]) for row in selected if not row.get("hmlr_inspire_id") or not legacy.postcode(row.get("postcode")) or not str(row.get("london_authority") or "").strip()]
    if invalid_rows:
        raise ValueError(f"manifest rows lack HMLR/postcode/authority evidence: {invalid_rows[:20]}")
    authorities = sorted({str(row["london_authority"]).strip() for row in selected})
    authority_manifest = guard.authority_manifest(authorities, hmlr_registry["download_page"], options.timeout)
    date_key = "".join(ch for ch in str(hmlr_registry["publication_date"]) if ch.isdigit())
    manifest_hash = hashlib.sha256(json.dumps({"authority_manifest": authority_manifest, "row_ids": manifest_ids}, sort_keys=True).encode()).hexdigest()[:16]
    cache = Path(tempfile.gettempdir()) / "aays_internet_access_3_hmlr_exact_stratified" / f"{date_key}_{manifest_hash}"
    hydrations: list[dict[str, Any]] = []
    authority_gml: dict[str, list[Path]] = {}
    blocked_before_download = bool(authority_manifest["missing"] or authority_manifest["ambiguous"])
    if not blocked_before_download:
        for authority in authorities:
            item = authority_manifest["chosen"][authority]
            hydrated = legacy.hydrate(authority, item, cache, options.timeout)
            hydrations.append(hydrated)
            authority_gml[authority] = [Path(value) for value in hydrated["gml_files"]]
    targets_by_authority: dict[str, set[str]] = defaultdict(set)
    for row in selected:
        targets_by_authority[str(row["london_authority"]).strip()].add(str(row["hmlr_inspire_id"]))
    rings: dict[str, list[tuple[float, float]]] = {}
    parser_audits: list[dict[str, Any]] = []
    for authority, target_ids in targets_by_authority.items():
        found, audit = find_largest_rings(legacy, authority_gml.get(authority, []), target_ids)
        rings.update(found)
        parser_audits.append({"authority": authority, "target_ids": len(target_ids), "rings_found": len(found), **audit})
    official = legacy.fetch_onspd(onspd_registry["query_url"], sorted({legacy.postcode(row.get("postcode")) for row in selected} - {None}), options.timeout) if not blocked_before_download else {}
    candidates: list[dict[str, Any]] = []
    inside_count = 0
    polygon_found = 0
    for row in selected:
        pc = legacy.postcode(row.get("postcode"))
        inspire_id = str(row.get("hmlr_inspire_id"))
        record = official.get(pc or "")
        ring = rings.get(inspire_id)
        east = float(record["east1m"]) if record and record.get("east1m") not in {None, ""} else None
        north = float(record["north1m"]) if record and record.get("north1m") not in {None, ""} else None
        inside = bool(ring and east is not None and north is not None and legacy.point_in_ring(east, north, ring))
        distance = round(legacy.distance_to_ring(east, north, ring), 2) if ring and east is not None and north is not None else None
        polygon_found += int(ring is not None)
        inside_count += int(inside)
        candidates.append({
            "row_no": int(row["row_no"]),
            "parcel_id": row.get("canonical_program_parcel_id"),
            "hmlr_inspire_id": inspire_id,
            "london_authority": row.get("london_authority"),
            "postcode": pc,
            "manifest_identity_matched": True,
            "hmlr_polygon_found": ring is not None,
            "onspd_postcode_found": record is not None,
            "postcode_centroid_inside_indicative_polygon": inside,
            "postcode_centroid_to_polygon_distance_m": distance,
            "status": "PREPARED_EVIDENCE_NOT_PROMOTED",
            "parcel_relation_promoted": False,
            "confidence_raised": False,
        })
    minimum = math.ceil(options.sample_size * options.minimum_match_ratio)
    blockers = ["PARCEL_TO_POSTCODE_RELATION_REMAINS_PROXY", "EXACT_UPRN_OR_ADDRESS_RELATION_NOT_ESTABLISHED"]
    if authority_manifest["missing"]:
        blockers.append("HMLR_AUTHORITY_DOWNLOAD_LINKS_MISSING")
    if authority_manifest["ambiguous"]:
        blockers.append("HMLR_AUTHORITY_DOWNLOAD_LINKS_AMBIGUOUS")
    if polygon_found < minimum:
        blockers.append(f"HMLR_INSPIRE_MATCH_RATIO_BELOW_GATE:{polygon_found}<{minimum}")
    if len(official) < minimum:
        blockers.append(f"ONSPD_EXACT_POSTCODE_MATCH_RATIO_BELOW_GATE:{len(official)}<{minimum}")
    hard_blockers = [value for value in blockers if value not in {"PARCEL_TO_POSTCODE_RELATION_REMAINS_PROXY", "EXACT_UPRN_OR_ADDRESS_RELATION_NOT_ESTABLISHED"}]
    passed = not hard_blockers
    now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
    summary = {
        "schema_version": 1,
        "task_id": "aays1-internet-access-3-hmlr-exact-stratified-manifest-20260722",
        "slot_id": SLOT_ID,
        "state": "runtime_validation_passed" if passed else "blocked",
        "updated_at": now,
        "guard": {
            "sample_size_required": options.sample_size,
            "minimum_match_ratio": options.minimum_match_ratio,
            "minimum_matches_required": minimum,
            "exact_manifest_row_identity_required": True,
            "authority_manifest": authority_manifest,
            "cache_identity_includes_publication_date_authority_manifest_and_row_ids": True,
        },
        "source_validation": {"hmlr_publication_date": hmlr_registry["publication_date"], "hydrations": hydrations, "parser_audits": parser_audits},
        "result": {
            "sample_rows_selected": len(selected),
            "manifest_rows_matched": len(selected),
            "authorities_selected": len(authorities),
            "inspire_polygons_found": polygon_found,
            "onspd_exact_postcodes_found": len(official),
            "postcode_centroids_inside_indicative_polygon": inside_count,
            "parcel_relations_promoted": 0,
            "confidence_uplifts": 0,
            "actual_business_data_rows_written": 0,
        },
        "validation": {"passed": passed, "blockers": blockers, "hard_blockers": hard_blockers},
        "output_semantics": "EXACT_STRATIFIED_POSTCODE_CENTROID_VS_INDICATIVE_HMLR_POLYGON_ONLY",
        "final_ready": False,
        "fake_data": False,
        "db_write": False,
        "migration": False,
        "production_deploy": False,
        "first_unverified_step_after_run": "HYDRATE_CURRENT_OS_OPEN_UPRN_AND_NSUL_OR_ONSUD_THEN_REQUIRE_EXACT_UPRN_POSTCODE_RELATION",
    }
    output_root = repo / options.output_root
    write(output_root / "hmlr_exact_stratified_candidates_latest.json", candidates)
    write(output_root / "hmlr_exact_stratified_validation_latest.json", summary)
    write(repo / options.runner_output, summary)
    update_feed(output_root, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if passed else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"slot_id": SLOT_ID, "state": "exception", "error_type": type(exc).__name__, "error": str(exc), "final_ready": False, "fake_data": False, "db_write": False, "migration": False, "production_deploy": False}, ensure_ascii=False, indent=2), file=__import__("sys").stderr)
        raise
