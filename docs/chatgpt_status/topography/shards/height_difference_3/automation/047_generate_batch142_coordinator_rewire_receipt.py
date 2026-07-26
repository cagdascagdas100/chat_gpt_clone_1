#!/usr/bin/env python3
"""Generate evidence-bound coordinator receipt for the directly sealed 039/040 chain."""
from __future__ import annotations
import argparse,hashlib,json,os,secrets,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
from typing import Any
TASK_ID="height_difference_3-canonical-api-measurement-20260721-01";ATTEMPT_ID="height-difference-3-20260721-011";IDEMPOTENCY="height_difference_3:canonical_security_stream:hmlr_ea_terrain50:v1";CONTINUATION="6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f";BRANCH="codex/aays-single-runner-v5-20260706";RUN039="docs/chatgpt_status/topography/shards/height_difference_3/automation/039_runner_entry_batch133_prepare_publish_handoff.py";POST040="docs/chatgpt_status/topography/shards/height_difference_3/automation/040_runner_entry_batch133_post_publish_remote_readback.py"
REQUEST_REL="docs/chatgpt_status/_shared/slots_21/height_difference_3/coordinator_requests/001_same_task_rewire_to_canonical_noarg.json";TASK_REL="docs/chatgpt_status/_shared/slots_21/height_difference_3/current_task_latest.json";QUEUE_REL="docs/chatgpt_status/topography/queue/height_difference_3_canonical_api_measurement_20260721_01.v3.task.json";QUEUE_ROOT="docs/chatgpt_status/topography/queue";RECEIPT_REL="docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/047_batch141_coordinator_rewire_receipt/coordinator_runtime_rewire_receipt.json"
PREFLIGHT_OUTPUTS={"043":"docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/039_batch136_exact_head_preflight/exact_branch_head_and_dependency_preflight_runtime.json","045":"docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/045_batch140_fresh_heartbeat_preflight/fresh_runner_heartbeat_preflight.json","044":"docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/041_batch137_runtime_environment_preflight/runtime_environment_preflight.json","042":"docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/037_batch135_fresh_origin_wiring_qa/fresh_origin_wiring_preflight_runtime.json","041":"docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/035_batch134_coordinator_wiring_qa/coordinator_wiring_request_validation.json"}
def root(p:Path)->Path:
    for c in (p,*p.parents):
        if (c/"england_map_web").is_dir() and (c/"docs/chatgpt_status").is_dir():return c
    raise RuntimeError("REPO_ROOT_NOT_FOUND")
def load(p:Path)->dict[str,Any]:
    v=json.loads(p.read_text(encoding="utf-8-sig"));
    if not isinstance(v,dict):raise ValueError(f"expected object:{p}")
    return v
def sha(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()
def bind(parts:list[str])->str:return hashlib.sha256("|".join(parts).encode()).hexdigest()
def gitexe()->str:
    t=str(os.environ.get("AAYS_GIT_EXE") or "git").strip();q=shutil.which(t)
    if q:return str(Path(q).resolve())
    p=Path(t)
    if p.is_file():return str(p.resolve())
    raise RuntimeError("GIT_EXECUTABLE_NOT_FOUND")
def git(g:str,r:Path,*a:str,check:bool=True)->str:
    p=subprocess.run([g,"-C",str(r),*a],text=True,capture_output=True,check=False)
    if check and p.returncode:raise RuntimeError(f"git {' '.join(a)} failed:{p.stderr[-1200:]}")
    return p.stdout.strip()
def blob(g:str,r:Path,ref:str,rel:str)->str:
    v=git(g,r,"rev-parse",f"{ref}:{rel}").lower()
    if len(v)!=40:raise ValueError(f"bad blob:{rel}:{v}")
    return v
def hits(raw:str)->list[str]:
    s=set()
    for line in raw.splitlines():
        t=line.strip();t=t[5:] if t.startswith("HEAD:") else t
        if t:s.add(t)
    return sorted(s)
def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("--coordinator-action-id",required=True);ap.add_argument("--effective-runtime-script",required=True);ap.add_argument("--effective-post-publish-script",required=True);ap.add_argument("--runtime-override-applied",action="store_true");a=ap.parse_args()
    if not a.runtime_override_applied:raise ValueError("runtime override attestation missing")
    if a.effective_runtime_script!=RUN039 or a.effective_post_publish_script!=POST040:raise ValueError("effective coordinator entrypoint mismatch")
    action=a.coordinator_action_id.strip()
    if len(action)<8:raise ValueError("coordinator action id too short")
    r=root(Path(__file__).resolve());g=gitexe();req=load(r/REQUEST_REL);task=load(r/TASK_REL);queue=load(r/QUEUE_REL)
    for obj,name in ((req,"request"),(task,"task")):
        if obj.get("task_id")!=TASK_ID or obj.get("attempt_id")!=ATTEMPT_ID or obj.get("idempotency_key")!=IDEMPOTENCY or obj.get("continuation_key")!=CONTINUATION:raise ValueError(f"{name} identity mismatch")
    if queue.get("task_id")!=TASK_ID or queue.get("attempt_id")!=ATTEMPT_ID or queue.get("idempotency_key")!=IDEMPOTENCY:raise ValueError("queue stable identity mismatch")
    spec=f"refs/heads/{BRANCH}:refs/remotes/origin/{BRANCH}";git(g,r,"fetch","--no-tags","origin",spec);local=git(g,r,"rev-parse","HEAD").lower();remote=git(g,r,"rev-parse",f"refs/remotes/origin/{BRANCH}").lower()
    if len(local)!=40 or local!=remote:raise RuntimeError(f"LOCAL_HEAD_NOT_FRESH_ORIGIN:{local}:{remote}")
    rb=blob(g,r,"HEAD",REQUEST_REL);tb=blob(g,r,"HEAD",TASK_REL);qb=blob(g,r,"HEAD",QUEUE_REL);combined=sorted(set(hits(git(g,r,"grep","-l","-F",TASK_ID,"HEAD","--",QUEUE_ROOT,check=False)))&set(hits(git(g,r,"grep","-l","-F",ATTEMPT_ID,"HEAD","--",QUEUE_ROOT,check=False)))&set(hits(git(g,r,"grep","-l","-F",IDEMPOTENCY,"HEAD","--",QUEUE_ROOT,check=False))))
    if combined!=[QUEUE_REL]:raise RuntimeError(f"DUPLICATE_OR_MISSING_QUEUE_RECORD:{combined}")
    ph={}
    for k,rel in PREFLIGHT_OUTPUTS.items():
        p=r/rel
        if not p.is_file():raise FileNotFoundError(p)
        v=load(p)
        if v.get("slot_id")!="height_difference_3":raise ValueError(f"preflight slot mismatch:{k}")
        if v.get("task_id") is not None and v.get("task_id")!=TASK_ID:raise ValueError(f"preflight task mismatch:{k}")
        if v.get("continuation_key") is not None and v.get("continuation_key")!=CONTINUATION:raise ValueError(f"preflight continuation mismatch:{k}")
        ph[k]=sha(p)
    nonce=secrets.token_hex(16);created=datetime.now(timezone.utc).isoformat().replace("+00:00","Z");key=bind([TASK_ID,ATTEMPT_ID,IDEMPOTENCY,CONTINUATION,rb,tb,qb,local,*(ph[k] for k in ("043","045","044","042","041")),RUN039,POST040,action,nonce])
    payload={"schema_version":3,"slot_id":"height_difference_3","status":"COORDINATOR_RUNTIME_REWIRE_RECEIPT","task_id":TASK_ID,"attempt_id":ATTEMPT_ID,"idempotency_key":IDEMPOTENCY,"continuation_key":CONTINUATION,"receipt_created_at_utc":created,"coordinator_action_id":action,"receipt_nonce":nonce,"local_head":local,"fresh_origin_head":remote,"fresh_origin_fetch_refspec":spec,"request_blob_sha":rb,"current_task_blob_sha":tb,"source_queue_blob_sha":qb,"queue_census_basis":["task_id","attempt_id","idempotency_key"],"matching_queue_record_count":1,"matching_queue_records":combined,"preflight_output_sha256":ph,"binding_key_sha256":key,"runtime_override_applied":True,"effective_runtime_script":RUN039,"effective_post_publish_script":POST040,"direct_entrypoint_control_plane_seal_required":True,"coordinator_only":True,"new_queue_record_created":False,"new_task_created":False,"new_runner_created":False,"parallel_runner_used":False,"queue_mutated_by_slot":False,"numeric_values_written":0,"final_ready":False,"fake_data":False}
    out=r/RECEIPT_REL;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");print(json.dumps({"ok":True,"status":payload["status"],"action_id":action,"queue_records":1,"head":local,"receipt_nonce":nonce,"binding_key":key,"output":str(out)}));return 0
if __name__=="__main__":
    try:raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok":False,"error":f"{type(exc).__name__}: {exc}"}),file=sys.stderr);raise
