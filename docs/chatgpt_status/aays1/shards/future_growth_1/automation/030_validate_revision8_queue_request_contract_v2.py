#!/usr/bin/env python3
"""Revision-8 queue/request validator v3, retained on the v2 runtime path."""
from __future__ import annotations
import argparse, importlib.util, json, sys
from pathlib import Path

BASE=Path(__file__).with_name("026_validate_revision8_queue_request_contract_v1.py")
spec=importlib.util.spec_from_file_location("queue_validator_v1",BASE)
mod=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(mod)
mod.REQUIRED_ACCEPTANCE.update({
  "runner_output_validator_selftest_expected":"18/18 PASS",
  "runtime_wrapper_selftest_expected":"10/10 PASS",
  "runtime_wrapper_static_checks_expected":18,
  "predecessor_dependency_selftest_expected":"10/10 PASS",
  "predecessor_dependency_checks_expected":19,
  "predecessor_dependency_complete_required":True,
})
mod.REQUIRED_QUEUE_PATH_KEYS.update({"predecessor_dependency_validator_path","predecessor_dependency_selftest_path"})

SLOT_ID=mod.SLOT_ID
TASK_ID=mod.TASK_ID
ATTEMPT_ID=mod.ATTEMPT_ID
CONTRACT_REVISION=mod.CONTRACT_REVISION
REQUIRED_ACCEPTANCE=mod.REQUIRED_ACCEPTANCE
REQUIRED_QUEUE_PATH_KEYS=mod.REQUIRED_QUEUE_PATH_KEYS
read_json=mod.read_json
BASE_VALIDATE=mod.validate
PREDECESSOR_TASK_ID="aays1-height-difference-2-canonical-export-official-sampling-20260720"
PREDECESSOR_STATUS_PATH="docs/chatgpt_status/_shared/slots_21/height_difference_2/status_latest.json"
EXPECTED_OUTPUTS={
  "docs/chatgpt_status/aays1/shards/future_growth_1/runner_outputs/006_official_geometry_pipeline_v8_latest.json",
  "england_map_web/data/aays_21_slots/future_growth_1/geometry_runner_status_v8_latest.json",
  "england_map_web/data/aays_21_slots/future_growth_1/canonical_rows_20_24_latest.json",
  "england_map_web/data/aays_21_slots/future_growth_1/revision8_relation_pair_input_validation_latest.json",
  "england_map_web/data/aays_21_slots/future_growth_1/geometry_wave_4/verified/official_geometry_relations_v3_latest.json",
  "england_map_web/data/aays_21_slots/future_growth_1/geometry_wave_5/verified/planning_constraint_query_validation_v8_latest.json",
  "england_map_web/data/aays_21_slots/future_growth_1/revision8_predecessor_dependency_validation_latest.json",
  "docs/chatgpt_status/aays1/shards/future_growth_1/validation/036_revision8_runner_output_runtime_validation_latest.json",
  "england_map_web/data/aays_21_slots/future_growth_1/revision8_runtime_acceptance_latest.json",
}

def validate(queue,readiness):
    result=BASE_VALIDATE(queue,readiness)
    outputs=queue.get("expected_outputs")
    result["checks"]["expected_outputs_complete"]=isinstance(outputs,list) and len(outputs)==len(EXPECTED_OUTPUTS) and set(outputs)==EXPECTED_OUTPUTS
    serialized=json.dumps({"queue":queue,"readiness":readiness},ensure_ascii=False,sort_keys=True)
    normalized=serialized.replace(PREDECESSOR_TASK_ID,"").replace(PREDECESSOR_STATUS_PATH,"")
    result["checks"]["no_cross_slot_tokens"]=("height_difference_2" not in normalized and "future_growth_2" not in normalized and "future_growth_3" not in normalized)
    failed=[k for k,v in result["checks"].items() if not v]
    result.update(schema_version=3,validation_kind="REVISION8_QUEUE_REQUEST_DEPENDENCY_AND_NINE_OUTPUT_FAIL_CLOSED",result="PASS" if not failed else "FAIL",checks_passed=sum(result["checks"].values()),checks_total=len(result["checks"]),failed_checks=failed,runner_output_validator_selftest_expected="18/18 PASS",expected_output_count=9)
    return result

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("queue",type=Path); p.add_argument("readiness",type=Path); p.add_argument("--output",type=Path); args=p.parse_args()
    try: result=validate(read_json(args.queue),read_json(args.readiness))
    except Exception as exc: result={"schema_version":3,"slot_id":SLOT_ID,"validation_kind":"REVISION8_QUEUE_REQUEST_DEPENDENCY_AND_NINE_OUTPUT_FAIL_CLOSED","result":"FAIL","checks_passed":0,"checks_total":1,"checks":{"json_load":False},"failed_checks":[f"json_load:{type(exc).__name__}:{exc}"],"runner_execution_claimed":False,"business_progress_claimed":False,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
    text=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
    if args.output: args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(text,encoding="utf-8")
    else: sys.stdout.write(text)
    return 0 if result["result"]=="PASS" else 2
if __name__=="__main__": raise SystemExit(main())
