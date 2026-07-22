#!/usr/bin/env python3
"""Revision-8 guarded runtime wrapper for future_growth_1."""
from __future__ import annotations
import importlib.util, json, os, subprocess, sys
from pathlib import Path
from typing import Any

REPO=Path(os.environ.get("AAYS_REPO_ROOT",".")).resolve()
CORE=REPO/"docs/chatgpt_status/aays1/automation/future_growth_1_official_geometry_entry_v8.py"
QUEUE_VALIDATOR=REPO/"docs/chatgpt_status/aays1/shards/future_growth_1/automation/030_validate_revision8_queue_request_contract_v2.py"
QUEUE_SELFTEST=REPO/"docs/chatgpt_status/aays1/shards/future_growth_1/automation/031_selftest_revision8_queue_request_contract_v2.py"
DEPENDENCY_VALIDATOR=REPO/"docs/chatgpt_status/aays1/shards/future_growth_1/automation/034_validate_revision8_predecessor_dependency_v1.py"
DEPENDENCY_SELFTEST=REPO/"docs/chatgpt_status/aays1/shards/future_growth_1/automation/035_selftest_revision8_predecessor_dependency_v1.py"
QUEUE_MANIFEST=REPO/"docs/chatgpt_status/aays1/queue/aays1_future_growth_1_official_geometry_pipeline_v8_20260722.task.json"
PREDECESSOR_STATUS=REPO/"docs/chatgpt_status/_shared/slots_21/height_difference_2/status_latest.json"
DEPENDENCY_OUTPUT=REPO/"england_map_web/data/aays_21_slots/future_growth_1/revision8_predecessor_dependency_validation_latest.json"
OUTPUT_VALIDATOR=REPO/"docs/chatgpt_status/aays1/shards/future_growth_1/automation/022_validate_revision8_runner_output_v1.py"
RUNNER_OUTPUT=REPO/"docs/chatgpt_status/aays1/shards/future_growth_1/runner_outputs/006_official_geometry_pipeline_v8_latest.json"
OUTPUT_VALIDATION=REPO/"docs/chatgpt_status/aays1/shards/future_growth_1/validation/036_revision8_runner_output_runtime_validation_latest.json"
WEB_ACCEPTANCE=REPO/"england_map_web/data/aays_21_slots/future_growth_1/revision8_runtime_acceptance_latest.json"

def run(command:list[str])->subprocess.CompletedProcess[str]:
    return subprocess.run(command,cwd=REPO,text=True,capture_output=True,check=False)

def read_json(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value,dict): raise ValueError(f"{path}: object required")
    return value

def write_json(path:Path,value:dict[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def blocked(status:str,detail:Any)->int:
    write_json(WEB_ACCEPTANCE,{"schema_version":1,"slot_id":"future_growth_1","state":"BLOCKED","status":status,"detail":detail,"runner_execution_claimed":False,"business_progress_claimed":False,"actual_business_data_rows_written":0,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False})
    return 2

def main()->int:
    required=[CORE,QUEUE_VALIDATOR,QUEUE_SELFTEST,DEPENDENCY_VALIDATOR,DEPENDENCY_SELFTEST,QUEUE_MANIFEST,PREDECESSOR_STATUS,OUTPUT_VALIDATOR]
    missing=[str(path) for path in required if not path.is_file()]
    if missing: return blocked("BLOCKED_RUNTIME_REQUIRED_FILE_MISSING",missing)
    dependency_selftest_run=run([sys.executable,str(DEPENDENCY_SELFTEST)])
    try: dependency_selftest=json.loads(dependency_selftest_run.stdout)
    except Exception: dependency_selftest={}
    if dependency_selftest_run.returncode!=0 or dependency_selftest.get("result")!="10/10 PASS":
        return blocked("BLOCKED_PREDECESSOR_DEPENDENCY_SELFTEST",dependency_selftest)
    dependency_run=run([sys.executable,str(DEPENDENCY_VALIDATOR),str(QUEUE_MANIFEST),str(PREDECESSOR_STATUS),"--output",str(DEPENDENCY_OUTPUT)])
    dependency=read_json(DEPENDENCY_OUTPUT) if DEPENDENCY_OUTPUT.is_file() else {}
    if dependency_run.returncode!=0 or dependency.get("result")!="PASS" or dependency.get("dependency_complete") is not True or dependency.get("checks_passed")!=19:
        return blocked("BLOCKED_PREDECESSOR_DEPENDENCY_NOT_COMPLETE",dependency)
    spec=importlib.util.spec_from_file_location("future_growth_1_entry_v8_core",CORE)
    if spec is None or spec.loader is None: return blocked("BLOCKED_CORE_IMPORT_SPEC",{})
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    module.QUEUE_REQUEST_VALIDATOR=QUEUE_VALIDATOR
    module.QUEUE_REQUEST_SELFTEST=QUEUE_SELFTEST
    core_exit=int(module.main())
    if core_exit!=0: return blocked("BLOCKED_CORE_ENTRY",{"exit_code":core_exit})
    if not RUNNER_OUTPUT.is_file(): return blocked("BLOCKED_RUNNER_OUTPUT_MISSING_AFTER_CORE",{})
    output_validation_run=run([sys.executable,str(OUTPUT_VALIDATOR),str(RUNNER_OUTPUT),"--output",str(OUTPUT_VALIDATION)])
    output_validation=read_json(OUTPUT_VALIDATION) if OUTPUT_VALIDATION.is_file() else {}
    if output_validation_run.returncode!=0 or output_validation.get("result")!="PASS" or output_validation.get("checks_passed")!=58 or output_validation.get("checks_total")!=58:
        return blocked("BLOCKED_RUNNER_OUTPUT_ACCEPTANCE",output_validation)
    write_json(WEB_ACCEPTANCE,{"schema_version":1,"slot_id":"future_growth_1","state":"COMPLETED_RUNTIME_ACCEPTANCE","status":"COMPLETED_DEPENDENCY_CORE_AND_58_OUTPUT_GATES","dependency_validation":dependency,"runner_output_validation":output_validation,"runner_execution_claimed":True,"business_progress_claimed":False,"actual_business_data_rows_written":0,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False})
    return 0
if __name__=="__main__": raise SystemExit(main())
