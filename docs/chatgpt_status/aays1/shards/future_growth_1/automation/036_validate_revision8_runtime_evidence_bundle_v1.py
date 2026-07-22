#!/usr/bin/env python3
"""Fail-closed validator for the revision-8 runtime evidence bundle."""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from pathlib import Path
from typing import Any

SLOT_ID="future_growth_1"
WORKSTREAM_ID="AAYS_21_SLOT_SAFE_PARALLEL_V1"
TASK_ID="aays1-future-growth-1-official-geometry-pipeline-20260721"
ATTEMPT_ID="future-growth-1-20260722-005"
CONTRACT_REVISION=8
SHA256_RE=re.compile(r"^[0-9a-f]{64}$")
QUEUE_EXPECTED_OUTPUTS={
 "docs/chatgpt_status/aays1/shards/future_growth_1/runner_outputs/006_official_geometry_pipeline_v8_latest.json",
 "england_map_web/data/aays_21_slots/future_growth_1/geometry_runner_status_v8_latest.json",
 "england_map_web/data/aays_21_slots/future_growth_1/canonical_rows_20_24_latest.json",
 "england_map_web/data/aays_21_slots/future_growth_1/revision8_relation_pair_input_validation_latest.json",
 "england_map_web/data/aays_21_slots/future_growth_1/geometry_wave_4/verified/official_geometry_relations_v3_latest.json",
 "england_map_web/data/aays_21_slots/future_growth_1/geometry_wave_5/verified/planning_constraint_query_validation_v8_latest.json",
 "england_map_web/data/aays_21_slots/future_growth_1/revision8_predecessor_dependency_validation_latest.json",
 "docs/chatgpt_status/aays1/shards/future_growth_1/validation/036_revision8_runner_output_runtime_validation_latest.json",
 "docs/chatgpt_status/aays1/shards/future_growth_1/validation/038_revision8_runtime_evidence_bundle_latest.json",
 "england_map_web/data/aays_21_slots/future_growth_1/revision8_runtime_acceptance_latest.json",
}
PRE_ACCEPTANCE_OUTPUTS=QUEUE_EXPECTED_OUTPUTS-{
 "docs/chatgpt_status/aays1/shards/future_growth_1/validation/038_revision8_runtime_evidence_bundle_latest.json",
 "england_map_web/data/aays_21_slots/future_growth_1/revision8_runtime_acceptance_latest.json",
}
FORBIDDEN_PATH_TOKENS=("future_growth_2","future_growth_3")

def read_json(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value,dict): raise ValueError(f"{path}: JSON object required")
    return value

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda:fh.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def safe_truth(value:dict[str,Any])->bool:
    return all(value.get(k) is False for k in ("fake_data","db_write","migration","production_deploy","final_ready"))

def validate(repo:Path, queue:dict[str,Any])->dict[str,Any]:
    outputs=queue.get("expected_outputs")
    outputs=outputs if isinstance(outputs,list) else []
    checks:dict[str,bool]={
      "queue_slot_exact":queue.get("slot_id")==SLOT_ID,
      "queue_task_exact":queue.get("task_id")==TASK_ID,
      "queue_attempt_exact":queue.get("attempt_id")==ATTEMPT_ID,
      "queue_revision_exact":queue.get("contract_revision")==CONTRACT_REVISION,
      "queue_expected_outputs_exact_10":len(outputs)==10 and set(outputs)==QUEUE_EXPECTED_OUTPUTS,
      "queue_single_runner_only":queue.get("single_runner_only") is True and queue.get("new_runner") is False and queue.get("parallel_runner") is False,
      "queue_truth_flags_safe":safe_truth(queue),
      "output_paths_slot_local":all("future_growth_1" in p for p in outputs),
      "output_paths_no_forbidden_slot":all(not any(t in p for t in FORBIDDEN_PATH_TOKENS) for p in outputs),
    }
    files=[]
    payloads={}
    for rel in sorted(PRE_ACCEPTANCE_OUTPUTS):
        path=repo/rel
        exists=path.is_file()
        checks[f"exists:{rel}"]=exists
        if not exists: continue
        size=path.stat().st_size
        sha=sha256_file(path)
        checks[f"nonempty:{rel}"]=size>0
        checks[f"sha256:{rel}"]=SHA256_RE.fullmatch(sha) is not None
        try:
            payload=read_json(path); payloads[rel]=payload
            checks[f"json_object:{rel}"]=True
            checks[f"slot_exact:{rel}"]=payload.get("slot_id")==SLOT_ID
        except Exception:
            checks[f"json_object:{rel}"]=False
            checks[f"slot_exact:{rel}"]=False
        files.append({"path":rel,"bytes":size,"sha256":sha})
    runner=payloads.get("docs/chatgpt_status/aays1/shards/future_growth_1/runner_outputs/006_official_geometry_pipeline_v8_latest.json",{})
    dep=payloads.get("england_map_web/data/aays_21_slots/future_growth_1/revision8_predecessor_dependency_validation_latest.json",{})
    outval=payloads.get("docs/chatgpt_status/aays1/shards/future_growth_1/validation/036_revision8_runner_output_runtime_validation_latest.json",{})
    checks.update({
      "all_preacceptance_files_present":len(files)==8,
      "all_file_hashes_unique":len({f["sha256"] for f in files})==len(files),
      "runner_workstream_exact":runner.get("workstream_id")==WORKSTREAM_ID,
      "runner_task_exact":runner.get("task_id")==TASK_ID,
      "runner_attempt_exact":runner.get("attempt_id")==ATTEMPT_ID,
      "runner_revision_exact":runner.get("contract_revision")==CONTRACT_REVISION,
      "runner_completed_state":isinstance(runner.get("state"),str) and runner["state"].startswith("COMPLETED"),
      "runner_business_zero":runner.get("actual_business_data_rows_written")==0,
      "runner_truth_flags_safe":safe_truth(runner),
      "dependency_pass":dep.get("result")=="PASS" and dep.get("dependency_complete") is True,
      "dependency_checks_19":dep.get("checks_passed")==19 and dep.get("checks_total")==19,
      "dependency_truth_flags_safe":safe_truth(dep),
      "runner_output_validation_pass":outval.get("result")=="PASS",
      "runner_output_validation_checks_58":outval.get("checks_passed")==58 and outval.get("checks_total")==58,
      "runner_output_validation_truth_safe":outval.get("business_progress_claimed") is False and outval.get("final_ready") is False,
    })
    failed=[k for k,v in checks.items() if not v]
    return {"schema_version":1,"slot_id":SLOT_ID,"workstream_id":WORKSTREAM_ID,"validation_kind":"REVISION8_RUNTIME_EVIDENCE_BUNDLE_FAIL_CLOSED","result":"PASS" if not failed else "FAIL","checks_passed":sum(checks.values()),"checks_total":len(checks),"checks":checks,"failed_checks":failed,"files":files,"preacceptance_files_expected":8,"queue_outputs_expected":10,"runner_execution_claimed":False,"business_progress_claimed":False,"actual_business_data_rows_written":0,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("repo",type=Path); p.add_argument("queue",type=Path); p.add_argument("--output",type=Path); args=p.parse_args()
    try: result=validate(args.repo.resolve(),read_json(args.queue))
    except Exception as exc: result={"schema_version":1,"slot_id":SLOT_ID,"validation_kind":"REVISION8_RUNTIME_EVIDENCE_BUNDLE_FAIL_CLOSED","result":"FAIL","checks_passed":0,"checks_total":1,"checks":{"load":False},"failed_checks":[f"{type(exc).__name__}:{exc}"],"runner_execution_claimed":False,"business_progress_claimed":False,"actual_business_data_rows_written":0,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
    text=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
    if args.output: args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(text,encoding="utf-8")
    else: sys.stdout.write(text)
    return 0 if result["result"]=="PASS" else 2
if __name__=="__main__": raise SystemExit(main())
