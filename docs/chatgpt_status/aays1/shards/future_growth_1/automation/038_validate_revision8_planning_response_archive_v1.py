#!/usr/bin/env python3
"""Fail-closed archive validator for 19 Planning Data response payloads."""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

SLOT_ID="future_growth_1"
WORKSTREAM_ID="AAYS_21_SLOT_SAFE_PARALLEL_V1"
TASK_ID="aays1-future-growth-1-official-geometry-pipeline-20260721"
ATTEMPT_ID="future-growth-1-20260722-005"
CONTRACT_REVISION=8
EXPECTED_HOST="www.planning.data.gov.uk"
EXPECTED_PATH="/entity.json"
ALLOWED_DATASETS={"brownfield-land","conservation-area","listed-building","green-belt","flood-risk-zone","article-4-direction-area","tree-preservation-zone"}
REQUIRED_FIELDS={"entity","dataset","reference","name","start-date","end-date","geometry","point","quality"}
SHA256_RE=re.compile(r"^[0-9a-f]{64}$")
OUTPUT_DIR_SUFFIX=Path("docs/chatgpt_status/aays1/shards/future_growth_1/runner_outputs/006_official_geometry_pipeline_v8_latest/planning_constraint_queries")
QUERY_VALIDATION_REL=Path("england_map_web/data/aays_21_slots/future_growth_1/geometry_wave_5/verified/planning_constraint_query_validation_v8_latest.json")

def read_json(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value,dict): raise ValueError(f"{path}: JSON object required")
    return value

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda:fh.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def resolve_under_repo(repo:Path,value:Any)->Path|None:
    if not isinstance(value,str) or not value: return None
    raw=Path(value)
    path=raw.resolve() if raw.is_absolute() else (repo/raw).resolve()
    try: path.relative_to(repo.resolve())
    except ValueError: return None
    return path

def request_contract(url:Any)->bool:
    if not isinstance(url,str): return False
    p=urlsplit(url)
    if p.scheme!="https" or p.hostname!=EXPECTED_HOST or p.path!=EXPECTED_PATH: return False
    q=parse_qs(p.query,keep_blank_values=True)
    try: limit=int(q.get("limit",[""])[0])
    except Exception: return False
    return (set(q.get("dataset",[]))==ALLOWED_DATASETS and set(q.get("field",[]))==REQUIRED_FIELDS and q.get("period")==["current"] and len(q.get("latitude",[]))==1 and len(q.get("longitude",[]))==1 and 1<=limit<=100)

def safe_truth(value:dict[str,Any])->bool:
    return all(value.get(k) is False for k in ("fake_data","db_write","migration","production_deploy","final_ready"))

def validate(repo:Path,queue:dict[str,Any],runner:dict[str,Any])->dict[str,Any]:
    repo=repo.resolve()
    evidence=runner.get("planning_query_evidence")
    rows=evidence.get("rows") if isinstance(evidence,dict) else None
    rows=rows if isinstance(rows,list) else []
    manifest_path=resolve_under_repo(repo,queue.get("planning_query_manifest_path"))
    validation_path=(repo/QUERY_VALIDATION_REL).resolve()
    evidence_path=(repo/OUTPUT_DIR_SUFFIX/"execution_evidence_manifest.json").resolve()
    source_sha=runner.get("source_sha256") if isinstance(runner.get("source_sha256"),dict) else {}
    checks:dict[str,bool]={
      "queue_slot_exact":queue.get("slot_id")==SLOT_ID,
      "queue_task_exact":queue.get("task_id")==TASK_ID,
      "queue_attempt_exact":queue.get("attempt_id")==ATTEMPT_ID,
      "queue_revision_exact":queue.get("contract_revision")==CONTRACT_REVISION,
      "runner_slot_exact":runner.get("slot_id")==SLOT_ID,
      "runner_workstream_exact":runner.get("workstream_id")==WORKSTREAM_ID,
      "runner_task_exact":runner.get("task_id")==TASK_ID,
      "runner_attempt_exact":runner.get("attempt_id")==ATTEMPT_ID,
      "runner_revision_exact":runner.get("contract_revision")==CONTRACT_REVISION,
      "runner_completed":isinstance(runner.get("state"),str) and runner["state"].startswith("COMPLETED"),
      "runner_truth_safe":safe_truth(runner) and runner.get("actual_business_data_rows_written")==0,
      "evidence_object":isinstance(evidence,dict),
      "evidence_counts_19":isinstance(evidence,dict) and evidence.get("request_count")==19 and evidence.get("network_requests_executed")==19 and evidence.get("rows_completed")==19,
      "evidence_no_promotion":isinstance(evidence,dict) and evidence.get("promotion_eligible_rows")==0 and evidence.get("scores_emitted")==0 and evidence.get("dry_run") is False and evidence.get("final_ready") is False,
      "rows_exact_19":len(rows)==19,
      "row_numbers_ordered":[r.get("row_no") for r in rows if isinstance(r,dict)]==list(range(1,20)),
      "manifest_path_safe":manifest_path is not None,
      "manifest_present":manifest_path is not None and manifest_path.is_file(),
      "evidence_manifest_present":evidence_path.is_file(),
      "query_validation_present":validation_path.is_file(),
    }
    manifest={}
    if manifest_path is not None and manifest_path.is_file():
        try: manifest=read_json(manifest_path)
        except Exception: manifest={}
    manifest_rows=manifest.get("rows") if isinstance(manifest.get("rows"),list) else []
    checks["manifest_rows_exact_19"]=len(manifest_rows)==19
    checks["manifest_sha_matches"]=manifest_path is not None and manifest_path.is_file() and isinstance(evidence,dict) and sha256_file(manifest_path)==evidence.get("manifest_sha256")
    checks["source_sha_query_evidence_matches"]=evidence_path.is_file() and sha256_file(evidence_path)==source_sha.get("query_evidence")
    checks["source_sha_query_validation_matches"]=validation_path.is_file() and sha256_file(validation_path)==source_sha.get("query_validation")
    if evidence_path.is_file():
        try: checks["evidence_manifest_equals_runner"]=read_json(evidence_path)==evidence
        except Exception: checks["evidence_manifest_equals_runner"]=False
    else: checks["evidence_manifest_equals_runner"]=False
    if validation_path.is_file():
        try:
            qv=read_json(validation_path)
            checks["query_validation_pass_19"]=qv.get("result")=="PASS" and qv.get("rows_validated")==19 and qv.get("polygon_relation_claimed") is False
        except Exception: checks["query_validation_pass_19"]=False
    else: checks["query_validation_pass_19"]=False
    files=[]; seen_paths=set(); total_entities=0
    for idx in range(1,20):
        row=rows[idx-1] if idx-1<len(rows) and isinstance(rows[idx-1],dict) else {}
        mrow=manifest_rows[idx-1] if idx-1<len(manifest_rows) and isinstance(manifest_rows[idx-1],dict) else {}
        path=resolve_under_repo(repo,row.get("response_path")); rel=None
        if path is not None:
            try: rel=path.relative_to(repo)
            except ValueError: rel=None
        prefix=f"row_{idx:02d}"
        checks[f"{prefix}_row_no"]=row.get("row_no")==idx
        checks[f"{prefix}_request_exact"]=row.get("request_url")==mrow.get("request_url") and request_contract(row.get("request_url"))
        checks[f"{prefix}_path_safe"]=path is not None and rel is not None and "future_growth_1" in str(rel)
        checks[f"{prefix}_path_exact_name"]=path is not None and rel is not None and path.name==f"row_{idx:05d}.json" and rel.parent==OUTPUT_DIR_SUFFIX
        checks[f"{prefix}_path_unique"]=path is not None and str(path) not in seen_paths
        if path is not None: seen_paths.add(str(path))
        exists=path is not None and path.is_file()
        checks[f"{prefix}_file_present"]=exists
        checks[f"{prefix}_file_nonempty"]=exists and path.stat().st_size>0
        sha=sha256_file(path) if exists else ""
        checks[f"{prefix}_sha_match"]=exists and SHA256_RE.fullmatch(str(row.get("response_sha256") or "")) is not None and sha==row.get("response_sha256")
        payload={}
        if exists:
            try: payload=read_json(path)
            except Exception: payload={}
        entities=payload.get("entities") if isinstance(payload.get("entities"),list) else []
        checks[f"{prefix}_entity_count_match"]=isinstance(row.get("entity_count"),int) and row.get("entity_count")==len(entities) and 0<=len(entities)<=100
        ids=[]; entity_ok=True
        for entity in entities:
            if not isinstance(entity,dict): entity_ok=False; continue
            ids.append(entity.get("entity"))
            if not REQUIRED_FIELDS.issubset(entity): entity_ok=False
            if not isinstance(entity.get("entity"),int): entity_ok=False
            if entity.get("dataset") not in ALLOWED_DATASETS: entity_ok=False
            if entity.get("end-date") not in ("",None): entity_ok=False
        checks[f"{prefix}_entities_contract"]=entity_ok and len(ids)==len(set(ids))
        zero=row.get("zero_result_semantics")
        checks[f"{prefix}_zero_semantics"]=(len(entities)==0 and zero=="NO_DATA_COVERAGE_NOT_PROOF") or (len(entities)>0 and zero in ("",None))
        checks[f"{prefix}_no_promotion"]=row.get("promotion_eligible") is False and row.get("score") is None
        total_entities+=len(entities)
        files.append({"row_no":idx,"path":str(rel) if rel else None,"bytes":path.stat().st_size if exists else 0,"sha256":sha,"entity_count":len(entities)})
    checks["unique_response_paths_19"]=len(seen_paths)==19
    checks["entities_read_matches"]=isinstance(evidence,dict) and evidence.get("entities_read")==total_entities
    failed=[k for k,v in checks.items() if not v]
    return {"schema_version":1,"slot_id":SLOT_ID,"workstream_id":WORKSTREAM_ID,"validation_kind":"REVISION8_PLANNING_RESPONSE_ARCHIVE_FAIL_CLOSED","result":"PASS" if not failed else "FAIL","checks_passed":sum(checks.values()),"checks_total":len(checks),"checks":checks,"failed_checks":failed,"rows_validated":19 if not failed else sum(1 for i in range(1,20) if checks.get(f"row_{i:02d}_file_present")),"response_files":files,"entities_read":total_entities,"runner_execution_claimed":False,"business_progress_claimed":False,"actual_business_data_rows_written":0,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("repo",type=Path); p.add_argument("queue",type=Path); p.add_argument("runner_output",type=Path); p.add_argument("--output",type=Path); a=p.parse_args()
    try: result=validate(a.repo,read_json(a.queue),read_json(a.runner_output))
    except Exception as exc: result={"schema_version":1,"slot_id":SLOT_ID,"validation_kind":"REVISION8_PLANNING_RESPONSE_ARCHIVE_FAIL_CLOSED","result":"FAIL","checks_passed":0,"checks_total":1,"checks":{"load":False},"failed_checks":[f"{type(exc).__name__}:{exc}"],"runner_execution_claimed":False,"business_progress_claimed":False,"actual_business_data_rows_written":0,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
    text=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
    if a.output: a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(text,encoding="utf-8")
    else: sys.stdout.write(text)
    return 0 if result["result"]=="PASS" else 2
if __name__=="__main__": raise SystemExit(main())
