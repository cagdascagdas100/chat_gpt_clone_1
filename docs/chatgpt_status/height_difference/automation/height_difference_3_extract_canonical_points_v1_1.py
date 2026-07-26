from __future__ import annotations

import hashlib
import json
import math
import os
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO

SLOT_ID = "height_difference_3"
TASK_VERSION = "1.1-exact-blob-low-memory-point-extraction-duplicate-guard"
ATTEMPT_ID = "height-difference-3-20260722-002"
SOURCE_BRANCH = "codex/aays-single-runner-v5-20260706"
SOURCE_PATH = "england_map_web/data/parcel_security_scores_rechecked_0_120m_spatial.geojson"
BLOB_SHA = "bb48164e7a0af78df875f30421a6a3068c43edb8"
EXPECTED_FEATURE_COUNT = 92283
TARGET_IDS = ["parcel_61523", "parcel_61524", "parcel_61525"]
CHUNK_BYTES = 1024 * 1024
FEATURES_ARRAY_RE = re.compile(br'"features"\s*:\s*\[')
OUTPUT_REL = Path("docs/chatgpt_status/height_difference/runner_outputs/height_difference_3_canonical_points_latest.json")
RECONCILIATION_REL = Path("docs/chatgpt_status/height_difference/runner_outputs/height_difference_3_canonical_points_reconciliation_latest.json")
WEBSITE_REL = Path("england_map_web/data/height_difference/height_difference_3_canonical_points_latest.json")

def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def git_text(repo_root: Path, *args: str) -> str:
    completed = subprocess.run(["git", "-C", str(repo_root), *args], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
    return completed.stdout.strip()

def write_json_atomic(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(path.name + ".tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temp_path, path)

def normalise_target(feature: dict) -> dict:
    properties = feature.get("properties") or {}
    geometry = feature.get("geometry") or {}
    coordinates = geometry.get("coordinates")
    parcel_id = properties.get("security_parcel_id") or properties.get("parcel_id")
    longitude = None
    latitude = None
    if isinstance(coordinates, list) and len(coordinates) >= 2:
        try:
            longitude = float(coordinates[0]); latitude = float(coordinates[1])
        except (TypeError, ValueError):
            longitude = None; latitude = None
    finite_coordinates = bool(longitude is not None and latitude is not None and math.isfinite(longitude) and math.isfinite(latitude) and -180.0 <= longitude <= 180.0 and -90.0 <= latitude <= 90.0)
    return {"parcel_id": parcel_id, "geometry_type": geometry.get("type"), "longitude": longitude, "latitude": latitude, "finite_coordinates": finite_coordinates, "lsoa_code": properties.get("security_lsoa_code"), "lsoa_name": properties.get("security_lsoa_name"), "borough_code": properties.get("security_borough"), "source_blob_sha": BLOB_SHA}

def stream_targets(handle: BinaryIO, sha256: hashlib._Hash, *, chunk_bytes: int = CHUNK_BYTES) -> tuple[dict[str, dict], dict]:
    found: dict[str, dict] = {}
    target_occurrences: Counter[str] = Counter()
    targets = set(TARGET_IDS)
    metrics: dict[str, object] = {"parser":"binary-feature-object-stream-v2-full-array-duplicate-guard","chunk_bytes":chunk_bytes,"features_array_found":False,"features_array_closed":False,"features_scanned":0,"expected_feature_count":EXPECTED_FEATURE_COUNT,"feature_count_matches_expected":False,"targets_found":[],"target_first_seen_order":[],"target_occurrence_counts":{target_id:0 for target_id in TARGET_IDS},"duplicate_target_ids":[],"all_targets_first_found_at_feature":None,"max_feature_object_bytes":0,"full_feature_array_parsed":False,"full_stream_hashed":False,"source_bytes_streamed":0,"error":None}
    tail=b""; located=False; parse_enabled=True; root_object=bytearray(); depth=0; in_string=False; escaped=False
    while True:
        chunk=handle.read(chunk_bytes)
        if not chunk: break
        sha256.update(chunk); metrics["source_bytes_streamed"]=int(metrics["source_bytes_streamed"])+len(chunk)
        if not located:
            data=tail+chunk; match=FEATURES_ARRAY_RE.search(data)
            if match is None:
                tail=data[-128:]; continue
            located=True; metrics["features_array_found"]=True; pending=data[match.end():]; tail=b""
        else:
            pending=chunk
        if not parse_enabled: continue
        position=0
        while position < len(pending):
            byte=pending[position]; position+=1
            if depth==0:
                if byte in b" \t\r\n,": continue
                if byte==ord("]"):
                    metrics["features_array_closed"]=True; metrics["full_feature_array_parsed"]=metrics.get("error") is None; parse_enabled=False; break
                if byte!=ord("{"):
                    metrics["error"]=f"UNEXPECTED_FEATURE_TOKEN_{byte}"; parse_enabled=False; break
                root_object=bytearray(b"{"); depth=1; in_string=False; escaped=False; continue
            root_object.append(byte)
            if in_string:
                if escaped: escaped=False
                elif byte==ord("\\"): escaped=True
                elif byte==ord('"'): in_string=False
                continue
            if byte==ord('"'): in_string=True
            elif byte==ord("{"): depth+=1
            elif byte==ord("}"):
                depth-=1
                if depth==0:
                    metrics["features_scanned"]=int(metrics["features_scanned"])+1
                    metrics["max_feature_object_bytes"]=max(int(metrics["max_feature_object_bytes"]),len(root_object))
                    try:
                        feature=json.loads(root_object.decode("utf-8"))
                    except Exception as exc:
                        metrics["error"]=f"FEATURE_JSON_PARSE_FAILED: {exc}"; parse_enabled=False; break
                    if isinstance(feature,dict):
                        properties=feature.get("properties") or {}; parcel_id=None
                        if isinstance(properties,dict): parcel_id=properties.get("security_parcel_id") or properties.get("parcel_id")
                        if parcel_id in targets:
                            target_id=str(parcel_id); target_occurrences[target_id]+=1
                            if target_id not in found:
                                found[target_id]=feature; first_seen=list(metrics["target_first_seen_order"]); first_seen.append(target_id); metrics["target_first_seen_order"]=first_seen
                            metrics["targets_found"]=[item for item in TARGET_IDS if item in found]
                            metrics["target_occurrence_counts"]={item:int(target_occurrences[item]) for item in TARGET_IDS}
                            metrics["duplicate_target_ids"]=[item for item in TARGET_IDS if target_occurrences[item]>1]
                            if len(found)==len(targets) and metrics["all_targets_first_found_at_feature"] is None: metrics["all_targets_first_found_at_feature"]=int(metrics["features_scanned"])
                    root_object=bytearray()
    metrics["full_stream_hashed"]=True; metrics["feature_count_matches_expected"]=int(metrics["features_scanned"])==EXPECTED_FEATURE_COUNT
    if located and metrics["error"] is None and not metrics["features_array_closed"]:
        metrics["error"]="FEATURES_ARRAY_NOT_CLOSED"; metrics["full_feature_array_parsed"]=False
    return found,metrics

def main() -> int:
    repo_root=Path(os.environ.get("AAYS_REPO_ROOT",r"F:\chatgpt\chat_gpt_clone_1_main")).resolve(); generated_at=utc_now(); errors:list[str]=[]
    try:
        object_type=git_text(repo_root,"cat-file","-t",BLOB_SHA); object_size=int(git_text(repo_root,"cat-file","-s",BLOB_SHA)); path_blob_sha=git_text(repo_root,"rev-parse",f"{SOURCE_BRANCH}:{SOURCE_PATH}")
    except Exception as exc:
        object_type=None; object_size=None; path_blob_sha=None; errors.append(f"CANONICAL_GIT_OBJECT_CHECK_FAILED: {exc}")
    found:dict[str,dict]={}; metrics:dict[str,object]={"parser":"binary-feature-object-stream-v2-full-array-duplicate-guard","chunk_bytes":CHUNK_BYTES,"features_array_found":False,"features_array_closed":False,"features_scanned":0,"expected_feature_count":EXPECTED_FEATURE_COUNT,"feature_count_matches_expected":False,"targets_found":[],"target_first_seen_order":[],"target_occurrence_counts":{target_id:0 for target_id in TARGET_IDS},"duplicate_target_ids":[],"all_targets_first_found_at_feature":None,"max_feature_object_bytes":0,"full_feature_array_parsed":False,"full_stream_hashed":False,"source_bytes_streamed":0,"error":"NOT_STARTED"}; source_sha256=None
    if not errors and object_type=="blob" and path_blob_sha==BLOB_SHA:
        process=subprocess.Popen(["git","-C",str(repo_root),"cat-file","blob",BLOB_SHA],stdout=subprocess.PIPE,stderr=subprocess.PIPE); assert process.stdout is not None
        digest=hashlib.sha256(); found,metrics=stream_targets(process.stdout,digest); stderr=process.stderr.read().decode("utf-8",errors="replace") if process.stderr else ""; return_code=process.wait(); source_sha256=digest.hexdigest()
        if return_code!=0: errors.append(f"GIT_CAT_FILE_STREAM_FAILED_{return_code}: {stderr.strip()}")
        if metrics.get("error"): errors.append(str(metrics["error"]))
    else:
        if object_type!="blob": errors.append(f"CANONICAL_OBJECT_TYPE_MISMATCH: {object_type}")
        if path_blob_sha!=BLOB_SHA: errors.append(f"CANONICAL_PATH_BLOB_MISMATCH: {path_blob_sha}")
    ordered_rows=[normalise_target(found[item]) for item in TARGET_IDS if item in found]; ordered_ids=[row.get("parcel_id") for row in ordered_rows]
    exact_order=ordered_ids==TARGET_IDS; unique_output_ids=len(set(ordered_ids))==len(TARGET_IDS); unique_source_occurrences=all(int((metrics.get("target_occurrence_counts") or {}).get(item,0))==1 for item in TARGET_IDS)
    all_points=len(ordered_rows)==len(TARGET_IDS) and all(row.get("geometry_type")=="Point" for row in ordered_rows); all_finite=len(ordered_rows)==len(TARGET_IDS) and all(bool(row.get("finite_coordinates")) for row in ordered_rows)
    full_size_hashed=bool(object_size is not None and int(metrics.get("source_bytes_streamed",0))==object_size); full_feature_array_parsed=bool(metrics.get("full_feature_array_parsed")); feature_count_matches=bool(metrics.get("feature_count_matches_expected"))
    if len(ordered_rows)!=len(TARGET_IDS): errors.append(f"TARGET_COUNT_MISMATCH: {len(ordered_rows)}")
    if not exact_order: errors.append(f"TARGET_ORDER_MISMATCH: {ordered_ids}")
    if not unique_output_ids: errors.append("TARGET_OUTPUT_IDS_NOT_UNIQUE")
    if not unique_source_occurrences: errors.append("TARGET_SOURCE_OCCURRENCE_MISMATCH: "+json.dumps(metrics.get("target_occurrence_counts"),sort_keys=True))
    if not all_points: errors.append("NON_POINT_OR_MISSING_GEOMETRY")
    if not all_finite: errors.append("NON_FINITE_OR_OUT_OF_RANGE_COORDINATE")
    if not full_size_hashed: errors.append("FULL_CANONICAL_STREAM_NOT_HASHED")
    if not full_feature_array_parsed: errors.append("FULL_FEATURE_ARRAY_NOT_PARSED")
    if not feature_count_matches: errors.append(f"FEATURE_COUNT_MISMATCH: {metrics.get('features_scanned')} != {EXPECTED_FEATURE_COUNT}")
    passed=not errors
    common={"schema_version":3,"slot_id":SLOT_ID,"task_version":TASK_VERSION,"attempt_id":ATTEMPT_ID,"generated_at":generated_at,"state":"CANONICAL_POINT_EXTRACTION_PASS" if passed else "CANONICAL_POINT_EXTRACTION_BLOCKED","source":{"branch":SOURCE_BRANCH,"path":SOURCE_PATH,"git_blob_sha":BLOB_SHA,"resolved_path_blob_sha":path_blob_sha,"git_object_type":object_type,"source_size_bytes":object_size,"stream_sha256":source_sha256,"expected_feature_count":EXPECTED_FEATURE_COUNT},"target_ids":TARGET_IDS,"canonical_point_rows":ordered_rows if passed else [],"canonical_point_row_count":len(ordered_rows) if passed else 0,"stream_metrics":metrics,"acceptance":{"exact_path_blob_match":path_blob_sha==BLOB_SHA,"exact_target_order":exact_order,"unique_output_target_ids":unique_output_ids,"unique_source_target_occurrences":unique_source_occurrences,"all_point_geometry":all_points,"all_finite_coordinates":all_finite,"full_stream_hashed":full_size_hashed,"full_feature_array_parsed":full_feature_array_parsed,"feature_count_matches_expected":feature_count_matches,"passed":passed},"errors":errors,"output_semantics":"CANONICAL_POINTS_ONLY_NO_BOUNDARY_NO_ELEVATION","actual_business_data_rows_written":0,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False,"final_ready":False}
    reconciliation={**common,"reconciliation_kind":"EXACT_BLOB_FULL_ARRAY_ORDERED_THREE_POINT_EXTRACTION","expected_target_count":len(TARGET_IDS),"observed_target_count":len(ordered_rows)}; website={**common,"website_row_kind":"CANONICAL_POINT_PREPARATION_ROWS","rows_visible":len(ordered_rows) if passed else 0}
    write_json_atomic(repo_root/OUTPUT_REL,common); write_json_atomic(repo_root/RECONCILIATION_REL,reconciliation); write_json_atomic(repo_root/WEBSITE_REL,website)
    print(f"SLOT_ID={SLOT_ID}"); print(f"CANONICAL_POINT_EXTRACTION_PASS={str(passed).lower()}"); print(f"CANONICAL_POINT_ROWS={len(ordered_rows) if passed else 0}"); print(f"STREAM_FEATURES_SCANNED={metrics.get('features_scanned',0)}"); print(f"FULL_FEATURE_ARRAY_PARSED={str(full_feature_array_parsed).lower()}"); print(f"FEATURE_COUNT_MATCHES={str(feature_count_matches).lower()}"); print(f"TARGET_DUPLICATES={len(metrics.get('duplicate_target_ids') or [])}"); print(f"FULL_STREAM_HASHED={str(full_size_hashed).lower()}"); print("FINAL_READY=false")
    return 0 if passed else 2

if __name__=="__main__":
    raise SystemExit(main())
