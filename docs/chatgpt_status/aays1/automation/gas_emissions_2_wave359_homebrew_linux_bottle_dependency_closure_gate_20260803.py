#!/usr/bin/env python3
"""Bounded Homebrew Linux bottle dependency-closure gate; no installs or bottle bodies."""
from __future__ import annotations
import argparse, hashlib, json, os, platform, shutil, tempfile, time, urllib.parse, urllib.request
from collections import deque
from pathlib import Path

API = "https://formulae.brew.sh/api/formula/{name}.json"
TARGET = 30761


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as f:
        f.write(text); f.flush(); os.fsync(f.fileno()); tmp = f.name
    os.replace(tmp, path)


def tag_for(machine: str) -> str | None:
    m = machine.lower().replace("-", "_")
    return "x86_64_linux" if m in {"x86_64", "amd64"} else "arm64_linux" if m in {"aarch64", "arm64"} else None


def get_json(url: str, timeout: float, limit: int) -> tuple[dict | None, dict]:
    started = time.monotonic()
    r = {"url": url, "method": "GET", "timeout_seconds": timeout, "max_bytes": limit,
         "status": None, "bytes_read": 0, "content_sha256": None, "error": None}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AAYS-Wave359/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            r["status"] = getattr(response, "status", None)
            data = response.read(limit + 1)
            if len(data) > limit: raise ValueError(f"response_exceeds_max_bytes:{limit}")
            r["bytes_read"] = len(data); r["content_sha256"] = digest(data)
            obj = json.loads(data.decode("utf-8"))
            if not isinstance(obj, dict): raise ValueError("formula_response_not_object")
            return obj, r
    except Exception as exc:
        r["error"] = f"{type(exc).__name__}:{exc}"
        return None, r
    finally:
        r["duration_seconds"] = round(time.monotonic() - started, 3)


def closure(timeout: float, byte_limit: int, formula_limit: int, tag: str | None) -> dict:
    q, seen, nodes, receipts, unresolved = deque(["overturemaps"]), set(), [], [], []
    truncated = False
    while q:
        if len(seen) >= formula_limit: truncated = True; break
        name = q.popleft()
        if name in seen: continue
        seen.add(name)
        obj, rec = get_json(API.format(name=urllib.parse.quote(name, safe="@+")), timeout, byte_limit)
        rec["formula"] = name; receipts.append(rec)
        if obj is None:
            unresolved.append(name); nodes.append({"name": name, "metadata_acquired": False}); continue
        deps = [str(x) for x in obj.get("dependencies") or []]
        q.extend(x for x in deps if x not in seen)
        stable = (obj.get("bottle") or {}).get("stable") or {}
        bottle = (stable.get("files") or {}).get(tag) if tag else None
        nodes.append({"name": name, "metadata_acquired": True,
                      "version": (obj.get("versions") or {}).get("stable"), "revision": obj.get("revision"),
                      "license": obj.get("license"), "dependencies": deps,
                      "build_dependencies": [str(x) for x in obj.get("build_dependencies") or []],
                      "bottle": {"tag": tag, "available": isinstance(bottle, dict),
                                 "url": bottle.get("url") if isinstance(bottle, dict) else None,
                                 "sha256": bottle.get("sha256") if isinstance(bottle, dict) else None,
                                 "cellar": bottle.get("cellar") if isinstance(bottle, dict) else None,
                                 "root_url": stable.get("root_url")} })
    missing = [n["name"] for n in nodes if n.get("metadata_acquired") and not n["bottle"]["available"]]
    metadata_complete = not unresolved and not truncated and not q
    return {"root_formula": "overturemaps", "target_bottle_tag": tag, "max_formulas": formula_limit,
            "formula_count": len(nodes), "metadata_complete": metadata_complete,
            "closure_complete": bool(tag) and metadata_complete and not missing, "truncated": truncated,
            "unresolved_formulae": unresolved, "missing_linux_bottle_formulae": missing, "nodes": nodes,
            "request_receipts": receipts, "total_bytes_read": sum(r["bytes_read"] for r in receipts),
            "network_error_count": sum(bool(r["error"]) for r in receipts)}


def rows_from(obj: dict) -> list[dict]:
    rows = obj.get("rows")
    if not isinstance(rows, list) or len(rows) < 3: raise ValueError("canonical_rows_missing_or_short")
    out = []
    for row in rows[:3]:
        geom, props = row.get("geometry") or {}, row.get("properties") or {}
        xy = geom.get("coordinates") or []
        if len(xy) != 2: raise ValueError("canonical_point_coordinates_invalid")
        out.append({"parcel_id": row.get("parcel_id") or props.get("parcel_id"),
                    "hmlr_inspire_id": props.get("hmlr_inspire_id"), "longitude": xy[0], "latitude": xy[1],
                    "geometry_type": geom.get("type") or row.get("geometry_type"),
                    "london_authority": props.get("london_authority")})
    return out


def self_test() -> None:
    assert tag_for("x86_64") == "x86_64_linux" and tag_for("aarch64") == "arm64_linux"
    assert tag_for("mips") is None
    assert digest(b"abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    print("SELF_TEST_PASS")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--canonical"); p.add_argument("--fixture"); p.add_argument("--output")
    p.add_argument("--timeout", type=float, default=20); p.add_argument("--max-bytes", type=int, default=500000)
    p.add_argument("--max-formulas", type=int, default=32); p.add_argument("--accessed-at", default="2026-08-03T04:14:00Z")
    p.add_argument("--self-test", action="store_true"); a = p.parse_args()
    if a.self_test: self_test(); return 0
    if not a.canonical or not a.fixture or not a.output: p.error("--canonical, --fixture and --output are required")
    sample = rows_from(json.loads(Path(a.canonical).read_text(encoding="utf-8")))
    fixture = json.loads(Path(a.fixture).read_text(encoding="utf-8")); evidence = fixture.get("source_evidence_manifest") or []
    if len(evidence) < 6: raise ValueError("source_evidence_manifest_incomplete")
    machine, tag = platform.machine(), tag_for(platform.machine())
    tools = {x: shutil.which(x) for x in ["brew", "curl", "tar", "gzip", "zstd", "xz", "patchelf", "ldconfig"]}
    c = closure(a.timeout, a.max_bytes, a.max_formulas, tag)
    blockers = ([] if tag else ["UNSUPPORTED_LINUX_ARCHITECTURE_FOR_HOMEBREW_BOTTLE_TAG"])
    if not tools["brew"]: blockers.append("HOMEBREW_NOT_PRESENT")
    if not c["metadata_complete"]: blockers.append("HOMEBREW_FORMULA_METADATA_CLOSURE_NOT_LIVE_ACQUIRED")
    if not c["closure_complete"]: blockers.append("HOMEBREW_LINUX_BOTTLE_DEPENDENCY_CLOSURE_NOT_ESTABLISHED")
    if not tools["patchelf"]: blockers.append("PATCHELF_NOT_PRESENT_FOR_SAFE_LINUX_RELOCATION_VALIDATION")
    blockers += ["BOTTLE_BODIES_NOT_DOWNLOADED_BY_DESIGN", "THREE_BOUNDED_BBOX_STREAMS_NOT_COMPLETED",
                 "THREE_OVERTURE_BUILDING_FEATURES_NOT_ACQUIRED", "THREE_EXACT_UPRNS_NOT_ACQUIRED",
                 "EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"]
    scope = {"target_bottle_tag": tag, "formula_count": c["formula_count"], "metadata_complete": c["metadata_complete"],
             "closure_complete": c["closure_complete"], "unresolved_formulae": c["unresolved_formulae"],
             "missing_linux_bottle_formulae": c["missing_linux_bottle_formulae"], "request_receipts": c["request_receipts"], "tools": tools}
    runtime = {"source_url": API.format(name="overturemaps"), "accessed_at": a.accessed_at,
               "content_sha256": digest(json.dumps(scope, sort_keys=True, separators=(",", ":")).encode()),
               "hash_scope": "bounded_recursive_homebrew_formula_json_receipts_and_local_tool_inventory",
               "record_scope": "Recursive formula metadata closure capped by formula count, response bytes and timeout; no bottle body or package installation.",
               "relevant_record_ids_or_excerpt": f"arch={machine}; tag={tag}; formulas={c['formula_count']}; metadata_complete={c['metadata_complete']}; closure_complete={c['closure_complete']}; bytes={c['total_bytes_read']}; network_errors={c['network_error_count']}; brew_present={bool(tools['brew'])}; patchelf_present={bool(tools['patchelf'])}",
               "supports_fields": ["formula_dependencies", "linux_bottle_urls", "linux_bottle_sha256", "metadata_closure", "tool_inventory", "no_bottle_body_download", "no_exact_binding_claim"],
               "license_or_terms_url": "https://docs.brew.sh/License"}
    out = {"schema_version": 1, "architecture_version": 3, "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
           "slot_id": "gas_emissions_2", "wave": 359, "accessed_at": a.accessed_at, "state": "NO_DATA_CONTINUE",
           "decision": "HOMEBREW_LINUX_BOTTLE_DEPENDENCY_CLOSURE_GATE_ASSESSED",
           "first_unverified_step": "ASSESS_GHCR_OCI_BOTTLE_MANIFEST_AND_LAYER_METADATA_OR_NO_DATA_CONTINUE",
           "canonical_sample_rows_in_scope": len(sample), "assessments": sample,
           "platform": {"machine": machine, "system": platform.system(), "bottle_tag": tag}, "tools": tools, "closure": c,
           "bottle_body_downloaded": False, "manual_bottle_extraction_attempted": False, "package_install_performed": False,
           "successful_bbox_stream_count": 0, "candidate_feature_count": 0, "business_rows_produced": 0, "parcel_rows_bound": 0,
           "completed_count": 0, "target_count": TARGET, "previous_percent": 0.0, "current_percent": 0.0, "percent_increase": 0.0,
           "blocker": ";".join(dict.fromkeys(blockers)), "source_evidence_manifest": evidence,
           "runtime_source_evidence": [runtime], "fake_data": False, "final_ready": False}
    atomic_json(Path(a.output), out)
    print(json.dumps({"state": out["state"], "formula_count": c["formula_count"], "metadata_complete": c["metadata_complete"],
                      "closure_complete": c["closure_complete"], "total_bytes_read": c["total_bytes_read"],
                      "network_error_count": c["network_error_count"], "business_rows_produced": 0}, sort_keys=True))
    return 0


if __name__ == "__main__": raise SystemExit(main())
