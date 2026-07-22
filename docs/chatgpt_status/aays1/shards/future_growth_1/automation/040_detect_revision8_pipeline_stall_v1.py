#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID="future_growth_1"
TASK_ID="aays1-future-growth-1-official-geometry-pipeline-20260721"
ATTEMPT_ID="future-growth-1-20260722-005"
CONTRACT_REVISION=8
BRANCH="codex/aays-single-runner-v5-20260706"
PREDECESSOR_TASK_ID="aays1-height-difference-2-canonical-export-official-sampling-20260720"

def read_json(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value,dict): raise ValueError(f"{path}: JSON object required")
    return value

def parse_time(value:Any)->datetime|None:
    if not isinstance(value,str) or not value: return None
    text=value.strip()
    if text.endswith("Z"): text=text[:-1]+"+00:00"
    try: dt=datetime.fromisoformat(text)
    except ValueError: return None
    if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def age_seconds(now:datetime,value:Any)->float|None:
    dt=parse_time(value)
    return None if dt is None else max(0.0,(now-dt).total_seconds())

def safe_truth(value:dict[str,Any])->bool:
    return all(value.get(k) is False for k in ("fake_data","db_write","migration","production_deploy","final_ready"))

def validate(p:dict[str,dict[str,Any]],now:datetime)->dict[str,Any]:
    cp=p["checkpoint"]; status=p["status"]; heartbeat=p["heartbeat"]; ownership=p["ownership"]
    task=p["current_task"]; queue=p["queue"]; pred=p["predecessor"]; refresh=p["queue_refresh"]
    reboot=p["reboot_request"]; bootstrap=p["runner_bootstrap"]; daemon=p["daemon_heartbeat"]
    multi_hb=p["multipage_heartbeat"]; multi_status=p["multipage_status"]
    queue_age=age_seconds(now,queue.get("queued_at")); pred_age=age_seconds(now,pred.get("updated_at"))
    daemon_age=age_seconds(now,daemon.get("heartbeat_at")); bootstrap_age=age_seconds(now,bootstrap.get("heartbeat_at"))
    multi_age=age_seconds(now,multi_status.get("checked_at")); refresh_age=age_seconds(now,refresh.get("requested_at")); reboot_age=age_seconds(now,reboot.get("created_at"))
    lease_dt=parse_time(heartbeat.get("lease_expires_at")); lease_expired=lease_dt is not None and lease_dt<now
    runner_stale=daemon_age is not None and daemon_age>6*3600
    predecessor_stale=pred_age is not None and pred_age>6*3600
    queue_wait_long=queue_age is not None and queue_age>4*3600
    recovery_wait_long=refresh_age is not None and refresh_age>6*3600 and reboot_age is not None and reboot_age>6*3600
    checks={
      "checkpoint_slot_exact":cp.get("slot_id")==SLOT_ID,
      "status_slot_exact":status.get("slot_id")==SLOT_ID,
      "heartbeat_slot_exact":heartbeat.get("slot_id")==SLOT_ID,
      "ownership_slot_exact":ownership.get("slot_id")==SLOT_ID,
      "task_slot_exact":task.get("slot_id")==SLOT_ID,
      "queue_slot_exact":queue.get("slot_id")==SLOT_ID,
      "checkpoint_sequence_44_or_newer":isinstance(cp.get("sequence"),int) and cp["sequence"]>=44,
      "status_sequence_matches":status.get("checkpoint_sequence")==cp.get("sequence"),
      "heartbeat_sequence_matches":heartbeat.get("checkpoint_sequence")==cp.get("sequence"),
      "task_identity_exact":task.get("task_id")==TASK_ID and task.get("attempt_id")==ATTEMPT_ID and task.get("contract_revision")==CONTRACT_REVISION,
      "queue_identity_exact":queue.get("task_id")==TASK_ID and queue.get("attempt_id")==ATTEMPT_ID and queue.get("contract_revision")==CONTRACT_REVISION,
      "queue_branch_exact":queue.get("target_branch")==BRANCH,
      "queue_pending_claimable":queue.get("state")=="pending" and queue.get("claimable") is True and queue.get("ready_for_claim") is True,
      "queue_single_runner_only":queue.get("single_runner_only") is True and queue.get("new_runner") is False and queue.get("parallel_runner") is False,
      "queue_predecessor_exact":queue.get("sequential_after_task_id")==PREDECESSOR_TASK_ID,
      "queue_pickup_not_observed":queue.get("runner_pickup_observed") is False and task.get("runner_pickup_observed") is False,
      "runner_output_not_observed":task.get("runner_output_observed") is False and status.get("task",{}).get("runner_output_observed") is False,
      "page_lease_kind_exact":heartbeat.get("heartbeat_kind")=="PAGE_LEASE_NOT_RUNNER_EXECUTION",
      "page_owner_consistent":heartbeat.get("owner_page_session_id")==ownership.get("owner_page_session_id")==task.get("owner_page_session_id"),
      "page_lease_expired_detected":lease_expired,
      "predecessor_task_exact":pred.get("current_task_id")==PREDECESSOR_TASK_ID,
      "predecessor_not_complete":pred.get("final_ready") is False and not str(pred.get("state","")).lower().startswith("completed"),
      "predecessor_ready_but_unclaimed":pred.get("ready_for_claim") is True and pred.get("runner_execution_state")=="guarded_operator_recovery_available_binary_stream_not_executed_unclaimed",
      "predecessor_stale_detected":predecessor_stale,
      "queue_wait_long_detected":queue_wait_long,
      "daemon_heartbeat_stale_detected":runner_stale and daemon.get("runner_active") is True and daemon.get("lock_valid") is True,
      "daemon_processed_zero":daemon.get("processed_task_count")==0,
      "operator_recovery_not_executed":refresh.get("operator_recovery_executed") is False and reboot.get("operator_recovery_executed") is False,
      "runner_restart_not_observed":reboot.get("runner_restart_observed") is False and reboot.get("runner_claim_observed") is False,
      "recovery_request_wait_long_detected":recovery_wait_long,
      "bootstrap_stale_detected":bootstrap_age is not None and bootstrap_age>24*3600,
      "legacy_multipage_stale_detected":multi_age is not None and multi_age>24*3600,
      "legacy_multipage_wrong_root_detected":str(multi_hb.get("work_root","")).startswith("C:\\") and str(refresh.get("canonical_work_root","")).startswith("F:\\"),
      "active_queue_preserved":task.get("queue_blob_sha")==queue.get("_blob_sha"),
      "truth_flags_safe":all(safe_truth(x) for x in (cp,status,heartbeat,ownership,task,queue)),
    }
    failed=[k for k,v in checks.items() if not v]
    external_stall=all([checks["predecessor_not_complete"],checks["queue_wait_long_detected"],checks["daemon_heartbeat_stale_detected"],checks["operator_recovery_not_executed"],checks["runner_restart_not_observed"]])
    return {
      "schema_version":1,"slot_id":SLOT_ID,"workstream_id":"AAYS_21_SLOT_SAFE_PARALLEL_V1",
      "diagnostic_kind":"REVISION8_LONG_PENDING_SINGLE_RUNNER_STALL_FAIL_CLOSED",
      "result":"PASS" if not failed else "FAIL","checks_passed":sum(checks.values()),"checks_total":len(checks),"checks":checks,"failed_checks":failed,
      "stall_detected":external_stall,"stall_classification":"CONFIRMED_EXTERNAL_SHARED_RUNNER_STALL" if external_stall else "NO_CONFIRMED_EXTERNAL_STALL",
      "local_page_lease_expired":lease_expired,
      "ages_seconds":{"queue":queue_age,"predecessor_status":pred_age,"daemon_heartbeat":daemon_age,"bootstrap_heartbeat":bootstrap_age,"multipage_status":multi_age,"queue_refresh_request":refresh_age,"reboot_request":reboot_age},
      "safe_repair_actions":["RENEW_EXPIRED_PAGE_LEASE_SAME_OWNER_ONLY","PRESERVE_EXISTING_REVISION8_QUEUE_AND_TASK_ID","DO_NOT_START_NEW_OR_PARALLEL_RUNNER","DO_NOT_BYPASS_PREDECESSOR","REQUIRE_EXISTING_F_HOST_GUARDED_OPERATOR_RECOVERY","REQUIRE_FRESH_DAEMON_HEARTBEAT_BEFORE_PICKUP","REQUIRE_SINGLE_CLAIM_AND_OUTPUT_READBACK_BEFORE_PROGRESS"],
      "local_queue_mutation_required":False,"external_host_action_required":external_stall,
      "runner_execution_claimed":False,"business_progress_claimed":False,"actual_business_data_rows_written":0,
      "final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False,
    }

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("bundle",type=Path); ap.add_argument("--now",required=True); ap.add_argument("--output",type=Path); a=ap.parse_args()
    try:
        now=parse_time(a.now)
        if now is None: raise ValueError("invalid --now")
        result=validate(read_json(a.bundle),now)
    except Exception as exc:
        result={"schema_version":1,"slot_id":SLOT_ID,"diagnostic_kind":"REVISION8_LONG_PENDING_SINGLE_RUNNER_STALL_FAIL_CLOSED","result":"FAIL","checks_passed":0,"checks_total":1,"failed_checks":[f"{type(exc).__name__}:{exc}"],"stall_detected":False,"runner_execution_claimed":False,"business_progress_claimed":False,"actual_business_data_rows_written":0,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
    text=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
    if a.output: a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(text,encoding="utf-8")
    else: sys.stdout.write(text)
    return 0 if result["result"]=="PASS" else 2
if __name__=="__main__": raise SystemExit(main())
