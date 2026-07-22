#!/usr/bin/env python3
"""Revision-8 queue/request validator v2 with the expanded 18/18 output selftest contract."""
from __future__ import annotations
import argparse, importlib.util, json, sys
from pathlib import Path

BASE=Path(__file__).with_name("026_validate_revision8_queue_request_contract_v1.py")
spec=importlib.util.spec_from_file_location("queue_validator_v1",BASE)
mod=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(mod)
mod.REQUIRED_ACCEPTANCE["runner_output_validator_selftest_expected"]="18/18 PASS"

SLOT_ID=mod.SLOT_ID
TASK_ID=mod.TASK_ID
ATTEMPT_ID=mod.ATTEMPT_ID
CONTRACT_REVISION=mod.CONTRACT_REVISION
REQUIRED_ACCEPTANCE=mod.REQUIRED_ACCEPTANCE
REQUIRED_QUEUE_PATH_KEYS=mod.REQUIRED_QUEUE_PATH_KEYS
validate=mod.validate
read_json=mod.read_json

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("queue",type=Path); p.add_argument("readiness",type=Path); p.add_argument("--output",type=Path); args=p.parse_args()
    try: result=validate(read_json(args.queue),read_json(args.readiness))
    except Exception as exc: result={"schema_version":2,"slot_id":SLOT_ID,"validation_kind":"REVISION8_QUEUE_AND_OFFICIAL_REQUEST_CONTRACT_V2_FAIL_CLOSED","result":"FAIL","checks_passed":0,"checks_total":1,"checks":{"json_load":False},"failed_checks":[f"json_load:{type(exc).__name__}:{exc}"],"runner_execution_claimed":False,"business_progress_claimed":False,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
    result["schema_version"]=2; result["validation_kind"]="REVISION8_QUEUE_AND_OFFICIAL_REQUEST_CONTRACT_V2_FAIL_CLOSED"; result["runner_output_validator_selftest_expected"]="18/18 PASS"
    text=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
    if args.output: args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(text,encoding="utf-8")
    else: sys.stdout.write(text)
    return 0 if result["result"]=="PASS" else 2
if __name__=="__main__": raise SystemExit(main())
