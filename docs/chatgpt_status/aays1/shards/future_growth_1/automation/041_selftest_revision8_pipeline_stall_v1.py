#!/usr/bin/env python3
from __future__ import annotations
import importlib.util,json
from datetime import datetime,timezone
from pathlib import Path
HERE=Path(__file__).resolve().parent; TARGET=HERE/"040_detect_revision8_pipeline_stall_v1.py"
spec=importlib.util.spec_from_file_location("validator",TARGET); mod=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(mod)
NOW=datetime(2026,7,22,12,13,51,tzinfo=timezone.utc)
def safe(slot=mod.SLOT_ID): return {"slot_id":slot,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False,"final_ready":False}
def fixture():
    owner="future-growth-1-page-20260722-025600-tr"; blob="a"*40
    return {
      "checkpoint":dict(safe(),sequence=44),
      "status":dict(safe(),checkpoint_sequence=44,task={"runner_output_observed":False}),
      "heartbeat":dict(safe(),checkpoint_sequence=44,heartbeat_kind="PAGE_LEASE_NOT_RUNNER_EXECUTION",owner_page_session_id=owner,lease_expires_at="2026-07-22T13:15:00+03:00"),
      "ownership":dict(safe(),owner_page_session_id=owner),
      "current_task":dict(safe(),owner_page_session_id=owner,task_id=mod.TASK_ID,attempt_id=mod.ATTEMPT_ID,contract_revision=8,runner_pickup_observed=False,runner_output_observed=False,queue_blob_sha=blob),
      "queue":dict(safe(),_blob_sha=blob,task_id=mod.TASK_ID,attempt_id=mod.ATTEMPT_ID,contract_revision=8,target_branch=mod.BRANCH,state="pending",claimable=True,ready_for_claim=True,single_runner_only=True,new_runner=False,parallel_runner=False,sequential_after_task_id=mod.PREDECESSOR_TASK_ID,runner_pickup_observed=False,queued_at="2026-07-22T08:44:00+03:00"),
      "predecessor":{"current_task_id":mod.PREDECESSOR_TASK_ID,"final_ready":False,"state":"pending_guarded_operator_recovery_binary_exact_stream","ready_for_claim":True,"runner_execution_state":"guarded_operator_recovery_available_binary_stream_not_executed_unclaimed","updated_at":"2026-07-21T11:44:00+03:00"},
      "queue_refresh":{"operator_recovery_executed":False,"requested_at":"2026-07-21T11:44:00+03:00","canonical_work_root":r"F:\TerraYield_AAYS_Portable\runner_system\AAYS_WT\AAYS_STABLE_RUNNER_WORKTREES"},
      "reboot_request":{"operator_recovery_executed":False,"runner_restart_observed":False,"runner_claim_observed":False,"created_at":"2026-07-21T11:44:00+03:00"},
      "runner_bootstrap":{"heartbeat_at":"2026-07-09T21:28:10.9349883Z"},
      "daemon_heartbeat":{"heartbeat_at":"2026-07-16T13:45:53.0433295Z","runner_active":True,"lock_valid":True,"processed_task_count":0},
      "multipage_heartbeat":{"work_root":r"C:\AAYS_WT\AAYS_STABLE_RUNNER_WORKTREES"},
      "multipage_status":{"checked_at":"2026-07-07T18:25:04Z"},
    }
def case(name,mutate,expected_result="PASS",expected_stall=True):
    x=fixture(); mutate(x); r=mod.validate(x,NOW)
    return {"name":name,"expected_result":expected_result,"actual_result":r["result"],"expected_stall":expected_stall,"actual_stall":r["stall_detected"],"pass":r["result"]==expected_result and r["stall_detected"] is expected_stall}
def main():
    cs=[
      case("exact_stalled_state",lambda x:None),
      case("wrong_checkpoint_slot",lambda x:x["checkpoint"].__setitem__("slot_id","future_growth_2"),"FAIL",True),
      case("sequence_mismatch",lambda x:x["status"].__setitem__("checkpoint_sequence",43),"FAIL",True),
      case("wrong_task",lambda x:x["current_task"].__setitem__("task_id","wrong"),"FAIL",True),
      case("wrong_attempt",lambda x:x["queue"].__setitem__("attempt_id","wrong"),"FAIL",True),
      case("wrong_revision",lambda x:x["queue"].__setitem__("contract_revision",7),"FAIL",True),
      case("wrong_branch",lambda x:x["queue"].__setitem__("target_branch","main"),"FAIL",True),
      case("not_claimable",lambda x:x["queue"].__setitem__("claimable",False),"FAIL",True),
      case("parallel_runner",lambda x:x["queue"].__setitem__("parallel_runner",True),"FAIL",True),
      case("wrong_predecessor",lambda x:x["queue"].__setitem__("sequential_after_task_id","wrong"),"FAIL",True),
      case("pickup_claim",lambda x:x["queue"].__setitem__("runner_pickup_observed",True),"FAIL",True),
      case("lease_not_expired",lambda x:x["heartbeat"].__setitem__("lease_expires_at","2026-07-22T18:15:00+03:00"),"FAIL",True),
      case("fresh_predecessor",lambda x:x["predecessor"].__setitem__("updated_at","2026-07-22T14:00:00+03:00"),"FAIL",True),
      case("fresh_daemon_no_stall",lambda x:x["daemon_heartbeat"].__setitem__("heartbeat_at","2026-07-22T12:00:00Z"),"FAIL",False),
      case("recovery_executed_no_stall",lambda x:(x["queue_refresh"].__setitem__("operator_recovery_executed",True),x["reboot_request"].__setitem__("operator_recovery_executed",True)),"FAIL",False),
      case("queue_blob_mismatch",lambda x:x["current_task"].__setitem__("queue_blob_sha","b"*40),"FAIL",True),
      case("unsafe_truth",lambda x:x["queue"].__setitem__("fake_data",True),"FAIL",True),
      case("daemon_processed_nonzero",lambda x:x["daemon_heartbeat"].__setitem__("processed_task_count",1),"FAIL",True),
    ]
    n=sum(c["pass"] for c in cs)
    out={"schema_version":1,"slot_id":mod.SLOT_ID,"selftest_kind":"REVISION8_LONG_PENDING_STALL_DIAGNOSTIC","result":f"{n}/{len(cs)} PASS","passed":n,"total":len(cs),"cases":cs,"runner_execution_claimed":False,"business_progress_claimed":False,"final_ready":False}
    print(json.dumps(out,ensure_ascii=False,indent=2)); return 0 if n==len(cs) else 2
if __name__=="__main__": raise SystemExit(main())
