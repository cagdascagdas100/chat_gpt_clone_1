#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path

def require(v:bool,m:str)->None:
    if not v: raise AssertionError(m)

def validate(root:Path)->list[str]:
    index=(root/"index.html").read_text(encoding="utf-8")
    lock=json.loads((root/"execution_lock_latest.json").read_text(encoding="utf-8"))
    progress=json.loads((root/"progress_latest.json").read_text(encoding="utf-8"))
    runner=json.loads((root/"runner_task_latest.json").read_text(encoding="utf-8"))
    checks=[]
    for marker in ('id="executionLockSummary"','id="executionLock"',"execution_lock_latest.json"):
        require(marker in index,f"missing {marker}"); checks.append(marker)
    require(lock["slot_id"]=="internet_access_3","slot"); checks.append("slot")
    require(lock["status"]=="PREPARED_WAITING_EXISTING_RUNNER","status"); checks.append("status")
    require(lock["locked_blob_count"]>=10,"blob count"); checks.append("blob_count")
    require(lock["exact_execution_lock_pass"] is False,"pre-run pass must be false"); checks.append("pre_run_false")
    require(lock["auto_claim"] is False and lock["queue_submission"] is False and lock["create_new_runner"] is False,"mutation guard"); checks.append("mutation_guard")
    require(progress["execution_lock_ready"] is True and progress["exact_execution_lock_pass"] is False,"progress lock fields"); checks.append("progress_fields")
    require(runner["execution_lock_command"].endswith("execution_lock_latest.json"),"runner command"); checks.append("runner_command")
    require(runner["stages"][0]["name"]=="EXACT_EXECUTION_LOCK_AUDIT","first stage"); checks.append("first_stage")
    return checks

def main()->int:
    p=argparse.ArgumentParser();p.add_argument("--web-root",required=True,type=Path);a=p.parse_args();checks=validate(a.web_root)
    print(json.dumps({"passed":len(checks),"total":len(checks),"checks":checks},sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
