#!/usr/bin/env python3
"""Read-only diagnosis of the shared-runner blocker seen by internet_access_3.

Consumes repository evidence only. It does not probe or control OS processes, claim a
slot, mutate queues, write heartbeats, restart a runner, or write business data.
"""
from __future__ import annotations
import argparse,json
from datetime import datetime,timezone
from pathlib import Path
from typing import Any
SLOT="internet_access_3"; BLOCKING_SLOT="height_difference_2"; TASK="aays1-height-difference-2-canonical-export-official-sampling-20260720"
class GateError(RuntimeError):pass
def req(c,m):
    if not c:raise GateError(m)
def load(path:Path,name:str)->dict[str,Any]:
    req(path.is_file() and path.stat().st_size>0,f"{name}: missing/empty")
    try:v=json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:raise GateError(f"{name}: invalid JSON: {exc}") from exc
    req(isinstance(v,dict),f"{name}: object required");return v
def dt(v:Any,name:str)->datetime:
    req(isinstance(v,str) and v.strip(),f"{name}: timestamp required");s=v.strip().replace("Z","+00:00")
    try:x=datetime.fromisoformat(s)
    except Exception as exc:raise GateError(f"{name}: invalid timestamp") from exc
    if x.tzinfo is None:x=x.replace(tzinfo=timezone.utc)
    return x.astimezone(timezone.utc)
def age_hours(now:datetime, value:Any,name:str)->float:
    x=(now-dt(value,name)).total_seconds()/3600;req(x>=0,f"{name}: future timestamp");return round(x,2)
def diagnose(*,global_task,queue_task,queue_refresh,restart_request,bootstrap,daemon_heartbeat,multi_heartbeat,multi_status,now:datetime,stale_hours:float=2.0)->dict[str,Any]:
    req(now.tzinfo is not None,"now timezone required");now=now.astimezone(timezone.utc);req(stale_hours>0,"stale threshold")
    ids=[global_task.get("task_id"),queue_task.get("task_id"),queue_refresh.get("task_id"),restart_request.get("task_id")];req(all(v==TASK for v in ids),"task id mismatch")
    req(global_task.get("slot_id")==BLOCKING_SLOT and queue_task.get("slot_id")==BLOCKING_SLOT,"blocking slot mismatch")
    req(global_task.get("status")=="pickup_requested" and queue_task.get("state")=="pickup_requested","pickup state mismatch")
    task_age=age_hours(now,queue_task.get("selected_at") or queue_task.get("queued_at"),"task selected")
    daemon_age=age_hours(now,daemon_heartbeat.get("heartbeat_at"),"daemon heartbeat")
    bootstrap_age=age_hours(now,bootstrap.get("heartbeat_at"),"bootstrap heartbeat")
    refresh_age=age_hours(now,queue_refresh.get("requested_at"),"queue refresh")
    restart_age=age_hours(now,restart_request.get("created_at"),"restart request")
    legacy_c=any(str(v or "").upper().startswith("C:\\") for v in (multi_heartbeat.get("heartbeat_path"),multi_heartbeat.get("work_root"),multi_status.get("repo_root"),multi_status.get("work_root")))
    recovery_executed=queue_refresh.get("operator_recovery_executed") is True or restart_request.get("operator_recovery_executed") is True
    restart_observed=restart_request.get("runner_restart_observed") is True
    claim_observed=restart_request.get("runner_claim_observed") is True
    gates=[
      {"gate_no":1,"name":"GLOBAL_AND_QUEUE_TASK_CONSISTENCY","state":"PASS","detail":f"{TASK}; slot={BLOCKING_SLOT}; pickup_requested"},
      {"gate_no":2,"name":"PICKUP_WAIT_AGE","state":"BLOCKED_STALE" if task_age>stale_hours else "RECENT","detail":f"selected task age={task_age}h; threshold={stale_hours}h"},
      {"gate_no":3,"name":"STABLE_DAEMON_HEARTBEAT_AGE","state":"BLOCKED_STALE" if daemon_age>stale_hours else "RECENT","detail":f"repository heartbeat age={daemon_age}h; last state={daemon_heartbeat.get('state')}"},
      {"gate_no":4,"name":"BOOTSTRAP_EVIDENCE_AGE","state":"BLOCKED_STALE" if bootstrap_age>stale_hours else "RECENT","detail":f"bootstrap evidence age={bootstrap_age}h; reported pid_alive={bootstrap.get('pid_alive')}"},
      {"gate_no":5,"name":"GUARDED_RECOVERY_REQUEST_PRESENT","state":"PASS","detail":f"queue refresh age={refresh_age}h; restart request age={restart_age}h"},
      {"gate_no":6,"name":"GUARDED_RECOVERY_EXECUTION","state":"PASS" if recovery_executed else "BLOCKED_NOT_EXECUTED","detail":f"operator_recovery_executed={recovery_executed}; runner_restart_observed={restart_observed}; runner_claim_observed={claim_observed}"},
      {"gate_no":7,"name":"LEGACY_C_DRIVE_EVIDENCE","state":"REVIEW_STALE_LEGACY_PATH" if legacy_c else "PASS","detail":"old MULTI_PAGE repository evidence references C: paths" if legacy_c else "no C: legacy path in supplied evidence"},
      {"gate_no":8,"name":"LIVE_OS_PROCESS_BOUNDARY","state":"WAITING_OPERATOR_LIVE_PROBE","detail":"GitHub JSON cannot prove the current Windows process state; no live OS success is claimed"},
      {"gate_no":9,"name":"NO_MUTATION_BOUNDARY","state":"PASS","detail":"read-only diagnosis; no queue, claim, heartbeat, restart, DB, migration or deploy mutation"}]
    blocked=task_age>stale_hours and daemon_age>stale_hours and not recovery_executed
    return {"schema_version":1,"slot_id":SLOT,"status":"BLOCKED_STALE_RUNNER_EVIDENCE_OPERATOR_RECOVERY_NOT_EXECUTED" if blocked else "REVIEW_RUNNER_EVIDENCE","diagnosed_at":now.isoformat(),"blocking_slot_id":BLOCKING_SLOT,"blocking_task_id":TASK,"repository_evidence_only":True,"live_os_process_probe_performed":False,"stale_threshold_hours":stale_hours,"ages_hours":{"pickup_wait":task_age,"daemon_heartbeat":daemon_age,"bootstrap_heartbeat":bootstrap_age,"queue_refresh_request":refresh_age,"restart_request":restart_age},"observations":{"operator_recovery_executed":recovery_executed,"runner_restart_observed":restart_observed,"runner_claim_observed":claim_observed,"legacy_c_drive_evidence":legacy_c,"global_status":global_task.get("status"),"queue_state":queue_task.get("state")},"gates":gates,"internet_access_3_claim_eligible":False,"recommended_operator_boundary":"Use the already-published guarded recovery path for the existing single runner; rerun internet_access_3 eligibility and execution-lock audits only after fresh heartbeat and cleared global task are observed.","auto_claim":False,"queue_submission":False,"create_new_runner":False,"actual_business_data_rows_written":0,"scores_written":0,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False,"final_ready":False}
def main():
    p=argparse.ArgumentParser();
    for n in ("global-task","queue-task","queue-refresh","restart-request","bootstrap","daemon-heartbeat","multi-heartbeat","multi-status"):p.add_argument("--"+n,required=True,type=Path)
    p.add_argument("--output",required=True,type=Path);p.add_argument("--stale-hours",type=float,default=2.0);a=p.parse_args();now=datetime.now(timezone.utc)
    out=diagnose(global_task=load(a.global_task,"global task"),queue_task=load(a.queue_task,"queue task"),queue_refresh=load(a.queue_refresh,"queue refresh"),restart_request=load(a.restart_request,"restart request"),bootstrap=load(a.bootstrap,"bootstrap"),daemon_heartbeat=load(a.daemon_heartbeat,"daemon heartbeat"),multi_heartbeat=load(a.multi_heartbeat,"multi heartbeat"),multi_status=load(a.multi_status,"multi status"),now=now,stale_hours=a.stale_hours)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");print(json.dumps({"status":out["status"],"ages_hours":out["ages_hours"]},sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
