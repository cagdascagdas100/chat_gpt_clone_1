#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, math, os
from pathlib import Path
from typing import Any

REPO = Path(os.environ.get("AAYS_REPO_ROOT", ".")).resolve()
TASK_ID = "height-difference-1-official-boundary-elevation-samples-20260720"
PAYLOAD_REVISION = 13
ATTEMPT_ID = "official-source-batch-004-revision-13-direct-os-terrain50-crosscheck"
IDEMPOTENCY_KEY = "height_difference_1-004-20260720"
SCRIPT_REL = "docs/chatgpt_status/topography/shards/height_difference_1/automation/038_height_difference_1_revision_13_direct_os_terrain50_crosscheck_20260721.py"
SAFETY = ("final_ready","product_final_ready","fake_data","db_write","migration","production_deploy")


def finite(v: Any) -> bool:
    return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(float(v))


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()


def hex64(v: Any) -> bool:
    return isinstance(v,str) and len(v)==64 and all(c in "0123456789abcdefABCDEF" for c in v)


def validate_payload(payload: Any, expected_script_sha: str) -> tuple[list[str],dict[str,Any]]:
    blockers=[]; facts={}
    if not isinstance(payload,dict): return ["OUTPUT_ROOT_NOT_OBJECT"],facts
    expected={"task_id":TASK_ID,"payload_revision":PAYLOAD_REVISION,"attempt_id":ATTEMPT_ID,"idempotency_key":IDEMPOTENCY_KEY,"script_path":SCRIPT_REL,"script_sha256":expected_script_sha}
    for k,v in expected.items():
        actual=payload.get(k)
        if k=="payload_revision":
            try: actual=int(actual)
            except Exception: actual=-1
        if actual!=v: blockers.append(f"OUTPUT_IDENTITY_MISMATCH:{k}")
    for f in SAFETY:
        if payload.get(f) is not False: blockers.append(f"OUTPUT_SAFETY_FLAG_NOT_FALSE:{f}")
    rows=payload.get("rows"); counts=payload.get("counts")
    if not isinstance(rows,list): blockers.append("OUTPUT_ROWS_NOT_LIST"); rows=[]
    if not isinstance(counts,dict): blockers.append("OUTPUT_COUNTS_NOT_OBJECT"); counts={}
    direct_ok=0; accepted=0; invalid=[]
    for i,row in enumerate(rows):
        if not isinstance(row,dict): blockers.append(f"OUTPUT_ROW_NOT_OBJECT:{i}"); continue
        direct=row.get("revision_13_direct_os_terrain50")
        os50=row.get("os_terrain50")
        if isinstance(direct,dict) and direct.get("ok") is True: direct_ok+=1
        if not bool(row.get("accepted_measured_row")): continue
        accepted+=1; reasons=[]
        if not isinstance(direct,dict) or direct.get("ok") is not True: reasons.append("DIRECT_OS_GATE_NOT_OK")
        if not isinstance(os50,dict) or os50.get("ok") is not True: reasons.append("OS_TERRAIN50_NOT_OK")
        else:
            if os50.get("horizontal_crs")!="EPSG:27700": reasons.append("OS_CRS_MISMATCH")
            if os50.get("vertical_crs")!="EPSG:5701": reasons.append("OS_VERTICAL_CRS_MISMATCH")
            hdr=os50.get("header") or {}
            if hdr.get("ncols")!=200 or hdr.get("nrows")!=200: reasons.append("OS_HEADER_NOT_200_BY_200")
            if not finite(hdr.get("cellsize")) or abs(float(hdr["cellsize"])-50.0)>1e-9: reasons.append("OS_CELLSIZE_NOT_50M")
            if os50.get("nodata") is not False: reasons.append("OS_NODATA_NOT_FALSE")
            for k in ("source_archive_sha256","source_grid_sha256","vertical_metadata_sha256","products_response_sha256","downloads_response_sha256"):
                if not hex64(os50.get(k)): reasons.append(f"OS_HASH_INVALID:{k}")
            if not finite(os50.get("elevation_m")): reasons.append("OS_ELEVATION_NON_NUMERIC")
            if not finite(os50.get("representative_to_cell_center_distance_m")) or float(os50["representative_to_cell_center_distance_m"])>math.sqrt(2)*25+0.001: reasons.append("OS_CELL_CENTER_DISTANCE_INVALID")
            if "not_parcel_range" not in str(os50.get("role") or ""): reasons.append("OS_ROLE_MISMATCH")
        gate=row.get("revision_10_evidence_gate") or {}
        diff=gate.get("ea_os_median_absolute_difference_m")
        if not finite(diff) or float(diff)>8.0: reasons.append("EA_OS_DIFFERENCE_INVALID_OR_OVER_8M")
        if reasons: invalid.append({"row_index":i,"reasons":reasons})
    expected_counts={"candidate_rows":len(rows),"revision_13_direct_os_terrain50_rows":direct_ok,"official_three_source_height_difference_rows":accepted,"official_three_source_measured_rows":accepted}
    for k,v in expected_counts.items():
        actual=counts.get(k)
        if not finite(actual) or int(actual)!=v: blockers.append(f"COUNT_MISMATCH:{k}")
    if invalid: blockers.append("ACCEPTED_ROWS_FAIL_REVISION_13_DIRECT_OS_GATE")
    direct_errors=int(counts.get("revision_13_direct_os_terrain50_error_rows",0) or 0) if finite(counts.get("revision_13_direct_os_terrain50_error_rows",0)) else -1
    if direct_errors>0 and payload.get("status")!="BLOCKED_DIRECT_OS_TERRAIN50_CROSSCHECK": blockers.append("DIRECT_OS_ERROR_STATUS_MISMATCH")
    if direct_errors==0:
        expected_status="MEASURED_OFFICIAL_HEIGHT_DIFFERENCE_ROWS_AVAILABLE" if accepted else "NO_DATA_NOT_INFERRED"
        if payload.get("status")!=expected_status: blockers.append("OUTPUT_STATUS_COUNT_MISMATCH")
    facts={"candidate_rows":len(rows),"direct_os_rows":direct_ok,"direct_os_error_rows":direct_errors,"accepted_rows":accepted,"invalid_accepted_rows":invalid}
    return blockers,facts


def main() -> int:
    script=REPO/SCRIPT_REL
    queue=REPO/"docs/chatgpt_status/topography/queue/height_difference_1_004_official_boundary_numeric_samples_20260720.v3.task.json"
    runner=REPO/"docs/chatgpt_status/topography/shards/height_difference_1/runner_outputs/015_revision_13_direct_os_terrain50_crosscheck_latest.json"
    web=REPO/"england_map_web/data/aays_21_slots/height_difference_1/revision_13_direct_os_terrain50_crosscheck_latest.json"
    snapshot=REPO/"docs/chatgpt_status/topography/shards/height_difference_1/source_snapshots/015_revision_13_direct_os_terrain50_crosscheck_manifest_latest.json"
    report=REPO/"docs/chatgpt_status/topography/shards/height_difference_1/reports/020_height_difference_1_revision_13_direct_os_terrain50_crosscheck_result.md"
    readback=REPO/"docs/chatgpt_status/topography/shards/height_difference_1/runner_outputs/024_revision_13_output_integrity_readback_latest.json"
    paths={"script":script,"queue":queue,"runner_output":runner,"web_output":web,"snapshot":snapshot,"report":report}
    blockers=[]; hashes={}; facts={}; snapfacts={}
    for name,path in paths.items():
        if not path.is_file(): blockers.append(f"MISSING_REQUIRED_ARTIFACT:{name}")
    expected_script_sha=sha(script) if script.is_file() else ""
    if script.is_file(): hashes["script_sha256"]=expected_script_sha
    if queue.is_file():
        try:
            q=read(queue)
            expected={"task_id":TASK_ID,"payload_revision":PAYLOAD_REVISION,"attempt_id":ATTEMPT_ID,"idempotency_key":IDEMPOTENCY_KEY,"script_path":SCRIPT_REL}
            for k,v in expected.items():
                actual=q.get(k)
                if k=="payload_revision":
                    try: actual=int(actual)
                    except Exception: actual=-1
                if actual!=v: blockers.append(f"QUEUE_IDENTITY_MISMATCH:{k}")
            hashes["queue_sha256"]=sha(queue)
        except Exception as exc: blockers.append(f"QUEUE_PARSE_ERROR:{type(exc).__name__}")
    if runner.is_file():
        try:
            payload=read(runner); b,facts=validate_payload(payload,expected_script_sha); blockers.extend(b); hashes["runner_output_sha256"]=sha(runner)
        except Exception as exc: blockers.append(f"RUNNER_OUTPUT_PARSE_ERROR:{type(exc).__name__}")
    if web.is_file(): hashes["web_output_sha256"]=sha(web)
    if runner.is_file() and web.is_file() and hashes.get("runner_output_sha256")!=hashes.get("web_output_sha256"): blockers.append("RUNNER_AND_WEB_OUTPUT_HASH_MISMATCH")
    if snapshot.is_file():
        try:
            s=read(snapshot)
            snapfacts={k:s.get(k) for k in ("task_id","payload_revision","attempt_id","idempotency_key","script_path","script_sha256","runner_web_output_sha256","candidate_rows","direct_ea_resample_rows","direct_os_terrain50_rows","direct_os_terrain50_error_rows","accepted_official_height_difference_rows")}
            expected={"task_id":TASK_ID,"payload_revision":PAYLOAD_REVISION,"attempt_id":ATTEMPT_ID,"idempotency_key":IDEMPOTENCY_KEY,"script_path":SCRIPT_REL,"script_sha256":expected_script_sha}
            for k,v in expected.items():
                actual=s.get(k)
                if k=="payload_revision":
                    try: actual=int(actual)
                    except Exception: actual=-1
                if actual!=v: blockers.append(f"SNAPSHOT_IDENTITY_MISMATCH:{k}")
            if runner.is_file() and s.get("runner_web_output_sha256")!=hashes.get("runner_output_sha256"): blockers.append("SNAPSHOT_OUTPUT_SHA256_MISMATCH")
            pairs={"candidate_rows":"candidate_rows","direct_os_terrain50_rows":"direct_os_rows","direct_os_terrain50_error_rows":"direct_os_error_rows","accepted_official_height_difference_rows":"accepted_rows"}
            for sk,fk in pairs.items():
                if not finite(s.get(sk)) or int(s[sk])!=int(facts.get(fk,-1)): blockers.append(f"SNAPSHOT_COUNT_MISMATCH:{sk}")
            for f in SAFETY:
                if s.get(f) is not False: blockers.append(f"SNAPSHOT_SAFETY_FLAG_NOT_FALSE:{f}")
            hashes["snapshot_sha256"]=sha(snapshot)
        except Exception as exc: blockers.append(f"SNAPSHOT_PARSE_ERROR:{type(exc).__name__}")
    if report.is_file(): hashes["report_sha256"]=sha(report)
    status="REVISION_13_OUTPUT_INTEGRITY_VERIFIED" if not blockers else "REVISION_13_OUTPUT_INTEGRITY_BLOCKED"
    result={"schema_version":1,"slot_id":"height_difference_1","task_id":TASK_ID,"payload_revision":PAYLOAD_REVISION,"status":status,"blockers":blockers,"facts":facts,"snapshot_facts":snapfacts,"artifact_paths":{k:str(v) for k,v in paths.items()},"artifact_sha256":hashes,"terminal_marker_trust_allowed":not blockers,"measured_rows_trust_allowed":not blockers and int(facts.get("accepted_rows",0))>0,"valid_no_data_terminal":not blockers and int(facts.get("accepted_rows",0))==0,"final_ready":False,"product_final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
    readback.parent.mkdir(parents=True,exist_ok=True); readback.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"ok":not blockers,"status":status,"blockers":blockers,"readback":str(readback)}))
    return 0 if not blockers else 2


if __name__=="__main__":
    raise SystemExit(main())
