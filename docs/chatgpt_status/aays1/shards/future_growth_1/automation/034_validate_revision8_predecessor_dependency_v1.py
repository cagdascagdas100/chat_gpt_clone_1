#!/usr/bin/env python3
"""Fail-closed predecessor completion validator for future_growth_1 revision-8."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from typing import Any

SLOT_ID="future_growth_1"
TASK_ID="aays1-future-growth-1-official-geometry-pipeline-20260721"
ATTEMPT_ID="future-growth-1-20260722-005"
CONTRACT_REVISION=8
PREDECESSOR_SLOT_ID="height_difference_2"
PREDECESSOR_TASK_ID="aays1-height-difference-2-canonical-export-official-sampling-20260720"

def read_json(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value,dict): raise ValueError(f"{path}: object required")
    return value

def completed_text(value:Any)->bool:
    return isinstance(value,str) and value.lower().startswith("completed")

def validate(queue:dict[str,Any], predecessor:dict[str,Any])->dict[str,Any]:
    checks={
      "queue_slot_exact":queue.get("slot_id")==SLOT_ID,
      "queue_task_exact":queue.get("task_id")==TASK_ID,
      "queue_attempt_exact":queue.get("attempt_id")==ATTEMPT_ID,
      "queue_revision_exact":queue.get("contract_revision")==CONTRACT_REVISION,
      "queue_pending_claimable":queue.get("state")=="pending" and queue.get("claimable") is True and queue.get("ready_for_claim") is True,
      "queue_single_shared_runner_only":queue.get("single_runner_only") is True and queue.get("new_runner") is False and queue.get("parallel_runner") is False,
      "queue_predecessor_exact":queue.get("sequential_after_task_id")==PREDECESSOR_TASK_ID,
      "predecessor_slot_exact":predecessor.get("slot_id")==PREDECESSOR_SLOT_ID,
      "predecessor_task_exact":predecessor.get("current_task_id")==PREDECESSOR_TASK_ID,
      "predecessor_state_completed":completed_text(predecessor.get("state")),
      "predecessor_runner_completed":completed_text(predecessor.get("runner_execution_state")),
      "predecessor_queue_completed":completed_text(predecessor.get("queue_status")),
      "predecessor_exact_seed_rows":isinstance(predecessor.get("candidate_seed_rows_written"),int) and predecessor["candidate_seed_rows_written"]>=3,
      "predecessor_exact_hmlr_polygons":isinstance(predecessor.get("hmlr_exact_polygon_rows_written"),int) and predecessor["hmlr_exact_polygon_rows_written"]>=3,
      "predecessor_ea_samples":isinstance(predecessor.get("ea_dtm1m_polygon_sample_rows_written"),int) and predecessor["ea_dtm1m_polygon_sample_rows_written"]>=3,
      "predecessor_os_crosschecks":isinstance(predecessor.get("os_terrain50_crosscheck_rows_written"),int) and predecessor["os_terrain50_crosscheck_rows_written"]>=3,
      "predecessor_http_acceptance":isinstance(predecessor.get("port_8012_acceptance_rows_written"),int) and predecessor["port_8012_acceptance_rows_written"]>=1,
      "predecessor_truth_flags_safe":predecessor.get("fake_data") is False and predecessor.get("db_write") is False and predecessor.get("migration") is False and predecessor.get("production_deploy") is False,
      "future_queue_truth_flags_safe":queue.get("fake_data") is False and queue.get("db_write") is False and queue.get("migration") is False and queue.get("production_deploy") is False and queue.get("final_ready") is False,
    }
    failed=[k for k,v in checks.items() if not v]
    return {
      "schema_version":1,"slot_id":SLOT_ID,
      "validation_kind":"REVISION8_PREDECESSOR_COMPLETION_FAIL_CLOSED",
      "result":"PASS" if not failed else "FAIL",
      "checks_passed":sum(checks.values()),"checks_total":len(checks),
      "checks":checks,"failed_checks":failed,
      "dependency_complete":not failed,
      "predecessor_slot_id":PREDECESSOR_SLOT_ID,
      "predecessor_task_id":PREDECESSOR_TASK_ID,
      "predecessor_state":predecessor.get("state"),
      "predecessor_runner_execution_state":predecessor.get("runner_execution_state"),
      "predecessor_queue_status":predecessor.get("queue_status"),
      "runner_execution_claimed":False,"polygon_relation_claimed":False,
      "business_progress_claimed":False,"actual_business_data_rows_written":0,
      "final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False,
    }

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("queue",type=Path); p.add_argument("predecessor_status",type=Path); p.add_argument("--output",type=Path); args=p.parse_args()
    try: result=validate(read_json(args.queue),read_json(args.predecessor_status))
    except Exception as exc:
        result={"schema_version":1,"slot_id":SLOT_ID,"validation_kind":"REVISION8_PREDECESSOR_COMPLETION_FAIL_CLOSED","result":"FAIL","checks_passed":0,"checks_total":1,"checks":{"json_load":False},"failed_checks":[f"json_load:{type(exc).__name__}:{exc}"],"dependency_complete":False,"runner_execution_claimed":False,"business_progress_claimed":False,"actual_business_data_rows_written":0,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
    text=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
    if args.output: args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(text,encoding="utf-8")
    else: sys.stdout.write(text)
    return 0 if result["result"]=="PASS" else 2
if __name__=="__main__": raise SystemExit(main())
