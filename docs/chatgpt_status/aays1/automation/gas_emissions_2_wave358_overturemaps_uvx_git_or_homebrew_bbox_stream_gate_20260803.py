#!/usr/bin/env python3
"""Wave358: bounded official overturemaps uvx Git-source/Homebrew bbox stream gate."""
from __future__ import annotations
import argparse, hashlib, json, os, pathlib, shutil, subprocess, sys, tempfile, time

GIT_SOURCE = "git+https://github.com/OvertureMaps/overturemaps-py.git@main"
TARGET_IDS = {"parcel_30762", "parcel_30763", "parcel_30764"}

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def atomic_write(path: pathlib.Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    os.replace(tmp, path)

def load_rows(path: pathlib.Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = [r for r in data.get("rows", []) if r.get("parcel_id") in TARGET_IDS]
    if len(rows) != 3:
        raise ValueError(f"expected 3 canonical rows, found {len(rows)}")
    return rows

def bbox_for(row: dict, pad: float = 0.00035) -> list[float]:
    lon, lat = row["geometry"]["coordinates"]
    return [round(lon-pad, 7), round(lat-pad, 7), round(lon+pad, 7), round(lat+pad, 7)]

def run_bounded(cmd: list[str], timeout: int, env: dict[str,str]) -> dict:
    started = time.monotonic()
    try:
        cp = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            timeout=timeout, env=env, check=False)
        return {
            "attempted": True, "returncode": cp.returncode, "timed_out": False,
            "duration_seconds": round(time.monotonic()-started, 3),
            "stdout_excerpt": cp.stdout[:8000], "stderr_excerpt": cp.stderr[:8000],
            "stdout_sha256": sha256_text(cp.stdout), "stderr_sha256": sha256_text(cp.stderr),
        }
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        err = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return {
            "attempted": True, "returncode": None, "timed_out": True,
            "duration_seconds": round(time.monotonic()-started, 3),
            "stdout_excerpt": out[:8000], "stderr_excerpt": err[:8000],
            "stdout_sha256": sha256_text(out), "stderr_sha256": sha256_text(err),
        }

def self_test() -> None:
    row = {"geometry":{"coordinates":[-0.04,51.67]}}
    assert bbox_for(row) == [-0.04035, 51.66965, -0.03965, 51.67035]
    print("SELF_TEST_PASS")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--canonical")
    ap.add_argument("--fixture")
    ap.add_argument("--output")
    ap.add_argument("--help-timeout", type=int, default=120)
    ap.add_argument("--bbox-timeout", type=int, default=45)
    ap.add_argument("--accessed-at", required=False)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test(); return 0
    if not (args.canonical and args.fixture and args.output):
        ap.error("--canonical, --fixture and --output are required")
    rows = load_rows(pathlib.Path(args.canonical))
    fixture = json.loads(pathlib.Path(args.fixture).read_text(encoding="utf-8"))
    accessed_at = args.accessed_at or fixture.get("source_evidence_manifest",[{}])[0].get("accessed_at")
    assessments = []
    for r in rows:
        assessments.append({
            "parcel_id":r["parcel_id"],
            "hmlr_inspire_id":r["properties"]["hmlr_inspire_id"],
            "longitude":r["properties"]["hmlr_lon"],
            "latitude":r["properties"]["hmlr_lat"],
            "london_authority":r["properties"]["london_authority"],
            "geometry_type":r["geometry_type"],
            "bbox":bbox_for(r),
        })
    uvx = shutil.which("uvx")
    brew = shutil.which("brew")
    standalone = shutil.which("overturemaps")
    with tempfile.TemporaryDirectory(prefix="aays-wave358-") as td:
        env = dict(os.environ)
        env.update({
            "UV_CACHE_DIR": str(pathlib.Path(td)/"uv-cache"),
            "UV_TOOL_DIR": str(pathlib.Path(td)/"uv-tools"),
            "UV_PYTHON_INSTALL_DIR": str(pathlib.Path(td)/"uv-python"),
            "UV_NO_PROGRESS": "1",
            "GIT_TERMINAL_PROMPT": "0",
        })
        git_help = {"attempted":False,"reason":"UVX_NOT_PRESENT"}
        cli_cmd_prefix = None
        mode = None
        if uvx:
            cli_cmd_prefix = [uvx, "--from", GIT_SOURCE, "overturemaps"]
            git_help = run_bounded(cli_cmd_prefix + ["--help"], args.help_timeout, env)
            if git_help.get("returncode") == 0:
                mode = "uvx_git_source"
        if mode is None and standalone:
            standalone_help = run_bounded([standalone, "--help"], args.help_timeout, env)
            if standalone_help.get("returncode") == 0:
                mode = "standalone_existing"
                cli_cmd_prefix = [standalone]
        else:
            standalone_help = {"attempted":False,"reason":"STANDALONE_NOT_USED_OR_NOT_PRESENT"}
        brew_info = {"attempted":False,"reason":"BREW_NOT_PRESENT"}
        if brew:
            brew_info = run_bounded([brew, "info", "--json=v2", "overturemaps"], min(args.help_timeout,60), env)
        streams = []
        candidates = []
        if mode and cli_cmd_prefix:
            for a in assessments:
                bbox = ",".join(str(x) for x in a["bbox"])
                cmd = cli_cmd_prefix + ["download", f"--bbox={bbox}", "-f", "geojsonseq", "--type=building",
                                        "--connect_timeout=5", "--request_timeout=10"]
                rec = run_bounded(cmd, args.bbox_timeout, env)
                lines = [ln for ln in rec.get("stdout_excerpt","").splitlines() if ln.strip()][:25]
                parsed = []
                for ln in lines:
                    try:
                        obj = json.loads(ln)
                        parsed.append({"id":obj.get("id") or obj.get("properties",{}).get("id"),
                                       "bbox":obj.get("bbox"),
                                       "geometry_type":(obj.get("geometry") or {}).get("type")})
                    except Exception:
                        continue
                rec.update({"parcel_id":a["parcel_id"],"bbox":a["bbox"],"parsed_feature_count":len(parsed)})
                streams.append(rec)
                candidates.extend({"parcel_id":a["parcel_id"],**p} for p in parsed)
        else:
            streams = [{"parcel_id":a["parcel_id"],"bbox":a["bbox"],"attempted":False,"reason":"CLI_NOT_READY"} for a in assessments]
        successful = sum(1 for r in streams if r.get("returncode") == 0)
        blocker_parts = []
        if not uvx: blocker_parts.append("UVX_NOT_PRESENT")
        elif git_help.get("returncode") != 0: blocker_parts.append("OVERTUREMAPS_UVX_GIT_SOURCE_NOT_RESOLVED_OR_EXECUTABLE")
        if not brew: blocker_parts.append("HOMEBREW_NOT_PRESENT")
        if not standalone: blocker_parts.append("STANDALONE_OVERTUREMAPS_BINARY_NOT_PRESENT")
        if successful < 3: blocker_parts.append("THREE_BOUNDED_BBOX_STREAMS_NOT_COMPLETED")
        if not candidates: blocker_parts.append("THREE_OVERTURE_BUILDING_FEATURES_NOT_ACQUIRED")
        blocker_parts += ["THREE_EXACT_UPRNS_NOT_ACQUIRED","EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"]
        next_step = ("ASSESS_OVERTURE_BUILDING_CANDIDATE_EXACT_UPRN_OR_PARCEL_BINDING_OR_NO_DATA_CONTINUE"
                     if candidates else
                     "ASSESS_HOMEBREW_LINUX_BOTTLE_DEPENDENCY_CLOSURE_OR_NO_DATA_CONTINUE")
        runtime_excerpt = (
            f"uvx_present={bool(uvx)}; git_help_returncode={git_help.get('returncode')}; "
            f"git_help_timed_out={git_help.get('timed_out')}; brew_present={bool(brew)}; "
            f"standalone_present={bool(standalone)}; successful_bbox_stream_count={successful}; "
            f"candidate_feature_count={len(candidates)}"
        )
        runtime = [{
            "accessed_at":accessed_at,
            "source_url":"https://github.com/OvertureMaps/overturemaps-py.git",
            "license_or_terms_url":"https://github.com/OvertureMaps/overturemaps-py/blob/main/LICENSE",
            "record_scope":"Temporary uvx Git-source help resolution, optional existing Homebrew/standalone discovery, and up to three bounded GeoJSONSeq bbox streams.",
            "supports_fields":["uvx_git_source_resolution","homebrew_presence","standalone_presence","three_bounded_bbox_streams","candidate_count","no_exact_binding_claim"],
            "hash_scope":"bounded_uvx_git_source_homebrew_and_bbox_stream_receipts",
            "relevant_record_ids_or_excerpt":runtime_excerpt,
            "content_sha256":sha256_text(runtime_excerpt),
        }]
        payload = {
            "schema_version":1,"architecture_version":3,"workstream_id":"AAYS_21_SLOT_SAFE_PARALLEL_V1",
            "slot_id":"gas_emissions_2","wave":358,"accessed_at":accessed_at,
            "decision":"OVERTUREMAPS_UVX_GIT_SOURCE_OR_HOMEBREW_THREE_BBOX_STREAM_GATE_ASSESSED",
            "state":"NO_DATA_CONTINUE","assessments":assessments,
            "uvx_present":bool(uvx),"brew_present":bool(brew),"standalone_binary_present":bool(standalone),
            "execution_mode":mode,"git_source_help":git_help,"brew_info":brew_info,
            "bbox_streams":streams,"successful_bbox_stream_count":successful,
            "candidate_feature_count":len(candidates),"candidates":candidates[:75],
            "business_rows_produced":0,"parcel_rows_bound":0,
            "full_geoparquet_downloaded":False,"persistent_package_install_performed":False,
            "blocker":";".join(blocker_parts),"first_unverified_step":next_step,
            "completed_count":0,"target_count":30761,"previous_percent":0.0,"current_percent":0.0,"percent_increase":0.0,
            "source_evidence_manifest":fixture["source_evidence_manifest"],
            "runtime_source_evidence":runtime,"fake_data":False,"final_ready":False,
        }
        atomic_write(pathlib.Path(args.output), payload)
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
