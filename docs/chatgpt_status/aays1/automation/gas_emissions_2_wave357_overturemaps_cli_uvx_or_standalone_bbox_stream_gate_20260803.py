#!/usr/bin/env python3
"""Wave357: bounded official overturemaps CLI uvx/standalone bbox stream gate."""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, subprocess, tempfile, time
from pathlib import Path
from typing import Any

PACKAGE_SPEC = "overturemaps==1.0.1"
MAX_LINES_PER_BBOX = 25
BBOX_PAD = 0.00035


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def load_assessments(path: Path) -> list[dict[str, Any]]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    rows = obj.get("rows") or []
    if len(rows) < 3:
        raise ValueError("canonical sample must contain at least three rows")
    out = []
    for row in rows[:3]:
        props = row.get("properties") or {}
        lon = float(props.get("hmlr_lon", row.get("geometry", {}).get("coordinates", [None, None])[0]))
        lat = float(props.get("hmlr_lat", row.get("geometry", {}).get("coordinates", [None, None])[1]))
        out.append({
            "parcel_id": row["parcel_id"],
            "hmlr_inspire_id": str(props["hmlr_inspire_id"]),
            "longitude": lon,
            "latitude": lat,
            "geometry_type": row.get("geometry_type") or row.get("geometry", {}).get("type"),
            "london_authority": props.get("london_authority"),
            "bbox": [round(lon-BBOX_PAD, 7), round(lat-BBOX_PAD, 7), round(lon+BBOX_PAD, 7), round(lat+BBOX_PAD, 7)],
        })
    return out


def run_bounded(command: list[str], timeout: int, env: dict[str, str]) -> dict[str, Any]:
    started = time.monotonic()
    try:
        cp = subprocess.run(command, text=True, capture_output=True, timeout=timeout, env=env, check=False)
        stdout = cp.stdout or ""
        stderr = cp.stderr or ""
        return {
            "command": command,
            "returncode": cp.returncode,
            "timed_out": False,
            "duration_seconds": round(time.monotonic()-started, 3),
            "stdout_bytes": len(stdout.encode("utf-8", "replace")),
            "stderr_bytes": len(stderr.encode("utf-8", "replace")),
            "stdout_sha256": sha256_bytes(stdout.encode("utf-8", "replace")),
            "stderr_sha256": sha256_bytes(stderr.encode("utf-8", "replace")),
            "stdout_excerpt": stdout[:1000],
            "stderr_excerpt": stderr[:2000],
            "stdout_text": stdout,
        }
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or "") if isinstance(e.stdout, str) else (e.stdout or b"").decode("utf-8", "replace")
        err = (e.stderr or "") if isinstance(e.stderr, str) else (e.stderr or b"").decode("utf-8", "replace")
        return {
            "command": command, "returncode": None, "timed_out": True,
            "duration_seconds": round(time.monotonic()-started, 3),
            "stdout_bytes": len(out.encode()), "stderr_bytes": len(err.encode()),
            "stdout_sha256": sha256_bytes(out.encode()), "stderr_sha256": sha256_bytes(err.encode()),
            "stdout_excerpt": out[:1000], "stderr_excerpt": err[:2000], "stdout_text": out,
        }


def choose_cli(env: dict[str, str], help_timeout: int) -> tuple[list[str] | None, dict[str, Any]]:
    standalone = shutil.which("overturemaps")
    uvx = shutil.which("uvx")
    receipt: dict[str, Any] = {"standalone_path": standalone, "uvx_path": uvx, "package_spec": PACKAGE_SPEC}
    if standalone:
        prefix = [standalone]
        mode = "standalone"
    elif uvx:
        prefix = [uvx, "--no-cache", PACKAGE_SPEC]
        mode = "uvx"
    else:
        receipt.update({"mode": None, "ready": False, "reason": "NO_UVX_OR_STANDALONE_BINARY"})
        return None, receipt
    result = run_bounded(prefix + ["--help"], help_timeout, env)
    ready = result.get("returncode") == 0 and "download" in (result.get("stdout_text") or "").lower()
    result.pop("stdout_text", None)
    receipt.update({"mode": mode, "ready": ready, "help_receipt": result})
    return (prefix if ready else None), receipt


def parse_candidates(text: str) -> tuple[list[dict[str, Any]], int]:
    candidates: list[dict[str, Any]] = []
    parsed = 0
    for line in text.splitlines():
        if len(candidates) >= MAX_LINES_PER_BBOX:
            break
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        parsed += 1
        props = obj.get("properties") or {}
        candidate_id = obj.get("id") or props.get("id") or props.get("@id")
        bbox = obj.get("bbox")
        geom_type = (obj.get("geometry") or {}).get("type")
        candidates.append({"id": candidate_id, "bbox": bbox, "geometry_type": geom_type})
    return candidates, parsed


def execute(args: argparse.Namespace) -> dict[str, Any]:
    canonical = Path(args.canonical)
    fixture_path = Path(args.fixture)
    output = Path(args.output)
    assessments = load_assessments(canonical)
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="aays-wave357-") as td:
        env = os.environ.copy()
        env.update({"UV_CACHE_DIR": str(Path(td)/"uv-cache"), "TERM": "dumb", "NO_COLOR": "1"})
        prefix, cli = choose_cli(env, args.help_timeout)
        streams = []
        candidate_count = 0
        success_count = 0
        if prefix:
            for a in assessments:
                bbox = ",".join(str(v) for v in a["bbox"])
                cmd = prefix + ["download", f"--bbox={bbox}", "-f", "geojsonseq", "--type=building", "--connect_timeout", "5", "--stac"]
                receipt = run_bounded(cmd, args.bbox_timeout, env)
                raw = receipt.pop("stdout_text", "")
                candidates, parsed = parse_candidates(raw)
                receipt.update({"parcel_id": a["parcel_id"], "bbox": a["bbox"], "candidate_count": len(candidates), "parsed_geojsonseq_lines": parsed, "candidates": candidates})
                candidate_count += len(candidates)
                if receipt.get("returncode") == 0:
                    success_count += 1
                streams.append(receipt)
        else:
            streams = [{"parcel_id": a["parcel_id"], "bbox": a["bbox"], "attempted": False, "reason": "CLI_NOT_READY"} for a in assessments]
    runtime_receipt = {
        "cli": cli,
        "stream_receipts": streams,
        "successful_bbox_stream_count": success_count,
        "candidate_feature_count": candidate_count,
        "full_geoparquet_downloaded": False,
        "max_lines_per_bbox": MAX_LINES_PER_BBOX,
    }
    runtime_norm = json.dumps(runtime_receipt, sort_keys=True, separators=(",", ":")).encode()
    if not cli.get("ready"):
        blocker = "OVERTUREMAPS_CLI_UVX_PACKAGE_NOT_RESOLVABLE_AND_STANDALONE_BINARY_NOT_PRESENT;THREE_BOUNDED_BBOX_STREAMS_NOT_EXECUTED;THREE_OVERTURE_BUILDING_FEATURES_NOT_ACQUIRED;THREE_EXACT_UPRNS_NOT_ACQUIRED;EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"
    elif candidate_count == 0:
        blocker = "OVERTUREMAPS_CLI_THREE_BOUNDED_BBOX_STREAMS_RETURNED_NO_USABLE_CANDIDATES;THREE_OVERTURE_BUILDING_FEATURES_NOT_ACQUIRED;THREE_EXACT_UPRNS_NOT_ACQUIRED;EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"
    else:
        blocker = "OVERTUREMAPS_CLI_NEARBY_BUILDING_CANDIDATES_NOT_EXACTLY_BOUND_TO_HMLR_PARCELS;THREE_EXACT_UPRNS_NOT_ACQUIRED;EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"
    runtime_evidence = {
        "accessed_at": args.accessed_at,
        "content_sha256": sha256_bytes(runtime_norm),
        "hash_scope": "bounded_uvx_or_standalone_help_and_three_bbox_stream_receipts",
        "license_or_terms_url": "https://github.com/OvertureMaps/overturemaps-py/blob/main/LICENSE",
        "record_scope": "Existing standalone binary or uvx package-resolution help gate plus up to three bounded GeoJSONSeq bbox streams; no full GeoParquet download or exact binding claim.",
        "relevant_record_ids_or_excerpt": f"mode={cli.get('mode')}; ready={cli.get('ready')}; successful_bbox_stream_count={success_count}; candidate_feature_count={candidate_count}",
        "source_url": "https://github.com/OvertureMaps/overturemaps-py",
        "supports_fields": ["uvx_resolution", "standalone_binary_presence", "three_bounded_bbox_streams", "candidate_count", "no_full_download", "no_exact_binding_claim"],
    }
    payload = {
        "schema_version": 1, "architecture_version": 3, "workstream_id": "AAYS_21_SLOT_SAFE_PARALLEL_V1",
        "slot_id": "gas_emissions_2", "wave": 357, "accessed_at": args.accessed_at,
        "decision": "OVERTUREMAPS_CLI_UVX_OR_STANDALONE_THREE_BBOX_STREAM_GATE_ASSESSED",
        "state": "NO_DATA_CONTINUE", "blocker": blocker,
        "first_unverified_step": "ASSESS_OVERTUREMAPS_UVX_GIT_SOURCE_OR_HOMEBREW_STANDALONE_THREE_BBOX_STREAM_OR_NO_DATA_CONTINUE",
        "canonical_sample_rows_in_scope": 3, "assessments": assessments,
        "runtime_receipt": runtime_receipt,
        "source_evidence_manifest": fixture["source_evidence_manifest"],
        "runtime_source_evidence": [runtime_evidence],
        "business_rows_produced": 0, "parcel_rows_bound": 0, "candidate_feature_count": candidate_count,
        "completed_count": 0, "target_count": 30761, "previous_percent": 0.0, "current_percent": 0.0, "percent_increase": 0.0,
        "full_geoparquet_downloaded": False, "fake_data": False, "final_ready": False,
    }
    atomic_json(output, payload)
    return payload


def self_test() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        canonical = root/"canonical.json"
        fixture = root/"fixture.json"
        output = root/"output.json"
        canonical.write_text(json.dumps({"rows":[
            {"parcel_id":"parcel_1","geometry_type":"Point","geometry":{"coordinates":[-0.04,51.67]},"properties":{"hmlr_inspire_id":"1","hmlr_lon":-0.04,"hmlr_lat":51.67,"london_authority":"Enfield"}},
            {"parcel_id":"parcel_2","geometry_type":"Point","geometry":{"coordinates":[-0.05,51.68]},"properties":{"hmlr_inspire_id":"2","hmlr_lon":-0.05,"hmlr_lat":51.68,"london_authority":"Enfield"}},
            {"parcel_id":"parcel_3","geometry_type":"Point","geometry":{"coordinates":[-0.06,51.69]},"properties":{"hmlr_inspire_id":"3","hmlr_lon":-0.06,"hmlr_lat":51.69,"london_authority":"Enfield"}}]}))
        fixture.write_text(json.dumps({"source_evidence_manifest":[]}))
        ns=argparse.Namespace(canonical=str(canonical),fixture=str(fixture),output=str(output),help_timeout=1,bbox_timeout=1,accessed_at="2026-08-03T00:55:00Z")
        result=execute(ns)
        assert result["state"] == "NO_DATA_CONTINUE"
        assert result["business_rows_produced"] == 0
        assert len(result["assessments"]) == 3
        assert output.exists()
    print("SELF_TEST_PASS")


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--canonical")
    p.add_argument("--fixture")
    p.add_argument("--output")
    p.add_argument("--help-timeout",type=int,default=120)
    p.add_argument("--bbox-timeout",type=int,default=45)
    p.add_argument("--accessed-at",default="2026-08-03T00:55:00Z")
    p.add_argument("--self-test",action="store_true")
    a=p.parse_args()
    if a.self_test:
        self_test(); return
    for name in ("canonical","fixture","output"):
        if not getattr(a,name): p.error(f"--{name.replace('_','-')} is required")
    execute(a)

if __name__ == "__main__":
    main()
