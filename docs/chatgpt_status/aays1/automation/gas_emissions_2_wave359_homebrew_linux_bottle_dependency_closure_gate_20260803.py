#!/usr/bin/env python3
"""Wave359: bounded Homebrew Linux bottle dependency-closure metadata gate.

This script does not install Homebrew, extract bottles, download full bottle bodies,
or emit business rows. It only reads official Homebrew Formula JSON metadata with
strict request/size/formula caps and records whether a complete Linux bottle closure
can be established for the current architecture.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import tempfile
import time
import urllib.parse
import urllib.request
from collections import deque
from pathlib import Path
from typing import Any

FORMULA_API = "https://formulae.brew.sh/api/formula/{name}.json"
TARGET_COUNT = 30761
ROOT_FORMULA = "overturemaps"


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as tmp:
        tmp.write(payload)
        tmp.flush()
        os.fsync(tmp.fileno())
        temp_name = tmp.name
    os.replace(temp_name, path)


def linux_bottle_tag(machine: str) -> str | None:
    normalized = machine.lower().replace("-", "_")
    if normalized in {"x86_64", "amd64"}:
        return "x86_64_linux"
    if normalized in {"aarch64", "arm64"}:
        return "arm64_linux"
    return None


def bounded_get_json(url: str, timeout: float, max_bytes: int) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    started = time.monotonic()
    receipt: dict[str, Any] = {
        "url": url,
        "method": "GET",
        "timeout_seconds": timeout,
        "max_bytes": max_bytes,
        "status": None,
        "bytes_read": 0,
        "content_sha256": None,
        "error": None,
        "duration_seconds": None,
    }
    request = urllib.request.Request(url, headers={"User-Agent": "AAYS-Wave359/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            receipt["status"] = getattr(response, "status", None)
            data = response.read(max_bytes + 1)
            if len(data) > max_bytes:
                raise ValueError(f"response_exceeds_max_bytes:{max_bytes}")
            receipt["bytes_read"] = len(data)
            receipt["content_sha256"] = sha256_bytes(data)
            parsed = json.loads(data.decode("utf-8"))
            if not isinstance(parsed, dict):
                raise ValueError("formula_response_not_object")
            return parsed, receipt
    except Exception as exc:
        receipt["error"] = f"{type(exc).__name__}:{exc}"
        return None, receipt
    finally:
        receipt["duration_seconds"] = round(time.monotonic() - started, 3)


def extract_bottle_metadata(formula: dict[str, Any], tag: str) -> dict[str, Any]:
    stable = (formula.get("bottle") or {}).get("stable") or {}
    file_meta = (stable.get("files") or {}).get(tag)
    return {
        "tag": tag,
        "available": isinstance(file_meta, dict),
        "url": file_meta.get("url") if isinstance(file_meta, dict) else None,
        "sha256": file_meta.get("sha256") if isinstance(file_meta, dict) else None,
        "cellar": file_meta.get("cellar") if isinstance(file_meta, dict) else None,
        "root_url": stable.get("root_url"),
        "rebuild": stable.get("rebuild"),
    }


def assess_closure(timeout: float, max_bytes: int, max_formulas: int, tag: str | None) -> dict[str, Any]:
    queue: deque[str] = deque([ROOT_FORMULA])
    visited: set[str] = set()
    nodes: list[dict[str, Any]] = []
    receipts: list[dict[str, Any]] = []
    unresolved: list[str] = []
    truncated = False
    while queue:
        if len(visited) >= max_formulas:
            truncated = True
            break
        name = queue.popleft()
        if name in visited:
            continue
        visited.add(name)
        url = FORMULA_API.format(name=urllib.parse.quote(name, safe="@+"))
        formula, receipt = bounded_get_json(url, timeout=timeout, max_bytes=max_bytes)
        receipt["formula"] = name
        receipts.append(receipt)
        if formula is None:
            unresolved.append(name)
            nodes.append({"name": name, "metadata_acquired": False, "dependencies": [], "bottle": None})
            continue
        dependencies = [str(x) for x in formula.get("dependencies") or []]
        for dep in dependencies:
            if dep not in visited:
                queue.append(dep)
        bottle = extract_bottle_metadata(formula, tag) if tag else None
        nodes.append({"name": name, "metadata_acquired": True, "version": (formula.get("versions") or {}).get("stable"), "revision": formula.get("revision"), "license": formula.get("license"), "dependencies": dependencies, "build_dependencies": [str(x) for x in formula.get("build_dependencies") or []], "bottle": bottle, "generated_date": formula.get("generated_date")})
    missing_bottles = [node["name"] for node in nodes if node.get("metadata_acquired") and (not node.get("bottle") or not node["bottle"].get("available"))]
    metadata_complete = not unresolved and not truncated and not queue
    closure_complete = bool(tag) and metadata_complete and not missing_bottles
    return {"root_formula": ROOT_FORMULA, "target_bottle_tag": tag, "max_formulas": max_formulas, "formula_count": len(nodes), "metadata_complete": metadata_complete, "closure_complete": closure_complete, "truncated": truncated, "unresolved_formulae": unresolved, "missing_linux_bottle_formulae": missing_bottles, "nodes": nodes, "request_receipts": receipts, "total_bytes_read": sum(int(r.get("bytes_read") or 0) for r in receipts), "network_error_count": sum(1 for r in receipts if r.get("error"))}


def extract_canonical_rows(canonical: dict[str, Any]) -> list[dict[str, Any]]:
    rows = canonical.get("rows")
    if not isinstance(rows, list) or len(rows) < 3:
        raise ValueError("canonical_rows_missing_or_short")
    result: list[dict[str, Any]] = []
    for row in rows[:3]:
        geom = row.get("geometry") or {}
        coords = geom.get("coordinates") or []
        props = row.get("properties") or {}
        if len(coords) != 2:
            raise ValueError("canonical_point_coordinates_invalid")
        result.append({"parcel_id": row.get("parcel_id") or props.get("parcel_id"), "hmlr_inspire_id": props.get("hmlr_inspire_id"), "longitude": coords[0], "latitude": coords[1], "geometry_type": geom.get("type") or row.get("geometry_type"), "london_authority": props.get("london_authority")})
    return result


def run_self_test() -> None:
    assert linux_bottle_tag("x86_64") == "x86_64_linux"
    assert linux_bottle_tag("aarch64") == "arm64_linux"
    assert linux_bottle_tag("mips64") is None
    sample = {"bottle": {"stable": {"root_url": "https://ghcr.io/v2/homebrew/core", "files": {"x86_64_linux": {"url": "https://example/b", "sha256": "a" * 64, "cellar": ":any"}}}}}
    bottle = extract_bottle_metadata(sample, "x86_64_linux")
    assert bottle["available"] is True and bottle["sha256"] == "a" * 64
    assert sha256_bytes(b"abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    print("SELF_TEST_PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical")
    parser.add_argument("--fixture")
    parser.add_argument("--output")
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--max-bytes", type=int, default=500_000)
    parser.add_argument("--max-formulas", type=int, default=32)
    parser.add_argument("--accessed-at", default="2026-08-03T04:14:00Z")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        run_self_test()
        return 0
    if not args.canonical or not args.fixture or not args.output:
        parser.error("--canonical, --fixture and --output are required")
    canonical_path = Path(args.canonical)
    fixture_path = Path(args.fixture)
    output_path = Path(args.output)
    canonical = json.loads(canonical_path.read_text(encoding="utf-8"))
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    canonical_rows = extract_canonical_rows(canonical)
    evidence_manifest = fixture.get("source_evidence_manifest") or []
    if len(evidence_manifest) < 6:
        raise ValueError("source_evidence_manifest_incomplete")
    machine = platform.machine()
    bottle_tag = linux_bottle_tag(machine)
    tools = {name: shutil.which(name) for name in ["brew", "curl", "tar", "gzip", "zstd", "xz", "patchelf", "ldconfig"]}
    closure = assess_closure(timeout=args.timeout, max_bytes=args.max_bytes, max_formulas=args.max_formulas, tag=bottle_tag)
    blockers: list[str] = []
    if bottle_tag is None:
        blockers.append("UNSUPPORTED_LINUX_ARCHITECTURE_FOR_HOMEBREW_BOTTLE_TAG")
    if not tools["brew"]:
        blockers.append("HOMEBREW_NOT_PRESENT")
    if not closure["metadata_complete"]:
        blockers.append("HOMEBREW_FORMULA_METADATA_CLOSURE_NOT_LIVE_ACQUIRED")
    if not closure["closure_complete"]:
        blockers.append("HOMEBREW_LINUX_BOTTLE_DEPENDENCY_CLOSURE_NOT_ESTABLISHED")
    if not tools["patchelf"]:
        blockers.append("PATCHELF_NOT_PRESENT_FOR_SAFE_LINUX_RELOCATION_VALIDATION")
    blockers.extend(["BOTTLE_BODIES_NOT_DOWNLOADED_BY_DESIGN", "THREE_BOUNDED_BBOX_STREAMS_NOT_COMPLETED", "THREE_OVERTURE_BUILDING_FEATURES_NOT_ACQUIRED", "THREE_EXACT_UPRNS_NOT_ACQUIRED", "EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"])
    receipts_hash_scope = {"target_bottle_tag": bottle_tag, "formula_count": closure["formula_count"], "metadata_complete": closure["metadata_complete"], "closure_complete": closure["closure_complete"], "unresolved_formulae": closure["unresolved_formulae"], "missing_linux_bottle_formulae": closure["missing_linux_bottle_formulae"], "request_receipts": closure["request_receipts"], "tools": tools}
    runtime_evidence = {"source_url": "https://formulae.brew.sh/api/formula/overturemaps.json", "accessed_at": args.accessed_at, "content_sha256": sha256_bytes(canonical_json_bytes(receipts_hash_scope)), "hash_scope": "bounded_recursive_homebrew_formula_json_receipts_and_local_tool_inventory", "record_scope": "Recursive formula metadata closure capped by formula count, response bytes and request timeout; no bottle body or package installation.", "relevant_record_ids_or_excerpt": f"arch={machine}; tag={bottle_tag}; formulas={closure['formula_count']}; metadata_complete={closure['metadata_complete']}; closure_complete={closure['closure_complete']}; bytes={closure['total_bytes_read']}; network_errors={closure['network_error_count']}; brew_present={bool(tools['brew'])}; patchelf_present={bool(tools['patchelf'])}", "supports_fields": ["formula_dependencies", "linux_bottle_urls", "linux_bottle_sha256", "metadata_closure", "tool_inventory", "no_bottle_body_download", "no_exact_binding_claim"], "license_or_terms_url": "https://docs.brew.sh/License"}
    output = {"schema_version": 1, "architecture_version": 3, "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1", "slot_id": "gas_emissions_2", "wave": 359, "accessed_at": args.accessed_at, "state": "NO_DATA_CONTINUE", "decision": "HOMEBREW_LINUX_BOTTLE_DEPENDENCY_CLOSURE_GATE_ASSESSED", "first_unverified_step": "ASSESS_GHCR_OCI_BOTTLE_MANIFEST_AND_LAYER_METADATA_OR_NO_DATA_CONTINUE", "canonical_sample_rows_in_scope": len(canonical_rows), "assessments": canonical_rows, "platform": {"machine": machine, "system": platform.system(), "bottle_tag": bottle_tag}, "tools": tools, "closure": closure, "bottle_body_downloaded": False, "manual_bottle_extraction_attempted": False, "package_install_performed": False, "successful_bbox_stream_count": 0, "candidate_feature_count": 0, "business_rows_produced": 0, "parcel_rows_bound": 0, "completed_count": 0, "target_count": TARGET_COUNT, "previous_percent": 0.0, "current_percent": 0.0, "percent_increase": 0.0, "blocker": ";".join(dict.fromkeys(blockers)), "source_evidence_manifest": evidence_manifest, "runtime_source_evidence": [runtime_evidence], "fake_data": False, "final_ready": False}
    atomic_write_json(output_path, output)
    print(json.dumps({"state": output["state"], "formula_count": closure["formula_count"], "metadata_complete": closure["metadata_complete"], "closure_complete": closure["closure_complete"], "total_bytes_read": closure["total_bytes_read"], "network_error_count": closure["network_error_count"], "business_rows_produced": 0}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
