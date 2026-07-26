#!/usr/bin/env python3
"""Validate the bound coordinator receipt for the Batch143 sealed wrapper chain."""
from __future__ import annotations
import hashlib, json, os, shutil, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
TASK_ID="height_difference_3-canonical-api-measurement-20260721-01"; ATTEMPT_ID="height-difference-3-20260721-011"; IDEMPOTENCY="height_difference_3:canonical_security_stream:hmlr_ea_terrain50:v1"; CONTINUATION="6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f"; BRANCH="codex/aays-single-runner-v5-20260706"
EFFECTIVE_RUN="docs/chatgpt_status/topography/shards/height_difference_3/automation/048_runner_entry_batch143_receipt_sealed_prepare_publish.py"; EFFECTIVE_POST="docs/chatgpt_status/topography/shards/height_difference_3/automation/049_runner_entry_batch143_receipt_sealed_post_publish.py"; UNDER_RUN="docs/chatgpt_status/topography/shards/height_difference_3/automation/039_runner_entry_batch133_prepare_publish_handoff.py"; UNDER_POST="docs/chatgpt_status/topography/shards/height_difference_3/automation/040_runner_entry_batch133_post_publish_remote_readback.py"
REQUEST_REL="docs/chatgpt_status/_shared/slots_21/height_difference_3/coordinator_requests/001_same_task_rewire_to_canonical_noarg.json"; TASK_REL="docs/chatgpt_status/_shared/slots_21/height_difference_3/current_task_latest.json"; QUEUE_REL="docs/chatgpt_status/topography/queue/height_difference_3_canonical_api_measurement_20260721_01.v3.task.json"; QUEUE_ROOT="docs/chatgpt_status/topography/queue"; RECEIPT_REL="docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/047_batch141_coordinator_rewire_receipt/coordinator_runtime_rewire_receipt.json"; VALIDATION_REL="docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/047_batch141_coordinator_rewire_receipt/coordinator_runtime_rewire_receipt_validation.json"; RECEIPT_TTL_SECONDS=600
PREFLIGHT_OUTPUTS={"043":"docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/039_batch136_exact_head_preflight/exact_branch_head_and_dependency_preflight_runtime.json","045":"docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/045_batch140_fresh_heartbeat_preflight/fresh_runner_heartbeat_preflight.json","044":"docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/041_batch137_runtime_environment_preflight/runtime_environment_preflight.json","042":"docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/037_batch135_fresh_origin_wiring_qa/fresh_origin_wiring_preflight_runtime.json","041":"docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/035_batch134_coordinator_wiring_qa/coordinator_wiring_request_validation.json"}
def root(p:Path)->Path:
    for c in (p,*p.parents):
        if (c/"england_map_web").is_dir() and (c/"docs/chatgpt_status").is_dir(): return c
    raise RuntimeError("REPO_ROOT_NOT_FOUND")
def load(p:Path)->dict[str,Any]:
    v=json.loads(p.read_text(encoding="utf-8-sig"));
    if not isinstance(v,dict): raise ValueError(f"expected object:{p}")
    return v
def parse(v:Any)->datetime:
    t=str(v or "").strip();
    if not t: raise ValueError("missing timestamp")
    if t.endswith("Z"): t=t[:-1]+"+00:00"
    d=datetime.fromisoformat(t); return (d if d.tzinfo else d.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)
def sha(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()
def bind(parts:list[str])->str:return hashlib.sha256("|".join(parts).encode()).hexdigest()
def gitexe()->str:
    t=str(os.environ.get("AAYS_GIT_EXE") or "git").strip(); q=shutil.which(t)
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
    out=set()
    for line in raw.splitlines():
        t=line.strip(); t=t[5:] if t.startswith("HEAD:") else t
        if t:out.add(t)
    return sorted(out)
def main()->int:
    r=root(Path(__file__).resolve()); g=gitexe(); rp=r/RECEIPT_REL
    if not rp.is_file():raise FileNotFoundError(rp)
    receipt=load(rp); receipt_sha=sha(rp); task=load(r/TASK_REL); req=load(r/REQUEST_REL); queue=load(r/QUEUE_REL); checks=[]
    def need(n:str,p:bool,d:Any=None):
        checks.append({"name":n,"passed":bool(p),"detail":d})
        if not p:raise RuntimeError(f"COORDINATOR_RECEIPT_FAILED:{n}:{d}")
    need("receipt_schema",int(receipt.get("schema_version") or 0)>=3); need("receipt_identity",receipt.get("task_id")==TASK_ID and receipt.get("attempt_id")==ATTEMPT_ID and receipt.get("idempotency_key")==IDEMPOTENCY and receipt.get("continuation_key")==CONTINUATION); need("task_identity",task.get("task_id")==TASK_ID and task.get("attempt_id")==ATTEMPT_ID and task.get("idempotency_key")==IDEMPOTENCY and task.get("continuation_key")==CONTINUATION); need("request_identity",req.get("task_id")==TASK_ID and req.get("attempt_id")==ATTEMPT_ID and req.get("idempotency_key")==IDEMPOTENCY and req.get("continuation_key")==CONTINUATION); need("queue_identity",queue.get("task_id")==TASK_ID and queue.get("attempt_id")==ATTEMPT_ID and queue.get("idempotency_key")==IDEMPOTENCY)
    action=str(receipt.get("coordinator_action_id") or "").strip(); nonce=str(receipt.get("receipt_nonce") or "").strip(); need("action_id",len(action)>=8); need("nonce",len(nonce)==32); need("runtime_override",receipt.get("runtime_override_applied") is True); need("sealed_wrappers",receipt.get("sealed_wrapper_chain_required") is True and receipt.get("effective_runtime_script")==EFFECTIVE_RUN and receipt.get("effective_post_publish_script")==EFFECTIVE_POST and receipt.get("underlying_runtime_script")==UNDER_RUN and receipt.get("underlying_post_publish_script")==UNDER_POST)
    now=datetime.now(timezone.utc); age=(now-parse(receipt.get("receipt_created_at_utc"))).total_seconds(); need("ttl",age>=-2 and age<=RECEIPT_TTL_SECONDS,age)
    spec=f"refs/heads/{BRANCH}:refs/remotes/origin/{BRANCH}"; git(g,r,"fetch","--no-tags","origin",spec); local=git(g,r,"rev-parse","HEAD").lower(); remote=git(g,r,"rev-parse",f"refs/remotes/origin/{BRANCH}").lower(); need("fresh_origin",len(local)==40 and local==remote); need("head_binding",receipt.get("local_head")==local and receipt.get("fresh_origin_head")==remote)
    rb=blob(g,r,"HEAD",REQUEST_REL); tb=blob(g,r,"HEAD",TASK_REL); qb=blob(g,r,"HEAD",QUEUE_REL); need("request_blob",receipt.get("request_blob_sha")==rb); need("task_blob",receipt.get("current_task_blob_sha")==tb); need("queue_blob",receipt.get("source_queue_blob_sha")==qb)
    combined=sorted(set(hits(git(g,r,"grep","-l","-F",TASK_ID,"HEAD","--",QUEUE_ROOT,check=False)))&set(hits(git(g,r,"grep","-l","-F",ATTEMPT_ID,"HEAD","--",QUEUE_ROOT,check=False)))&set(hits(git(g,r,"grep","-l","-F",IDEMPOTENCY,"HEAD","--",QUEUE_ROOT,check=False)))); need("single_queue",combined==[QUEUE_REL],combined)
    actual={}; saved=receipt.get("preflight_output_sha256") or {}
    for k,rel in PREFLIGHT_OUTPUTS.items():
        p=r/rel; need(f"preflight_{k}_exists",p.is_file()); v=load(p); need(f"preflight_{k}_slot",v.get("slot_id")=="height_difference_3"); actual[k]=sha(p); need(f"preflight_{k}_sha",saved.get(k)==actual[k])
    key=bind([TASK_ID,ATTEMPT_ID,IDEMPOTENCY,CONTINUATION,rb,tb,qb,local,*(actual[k] for k in ("043","045","044","042","041")),EFFECTIVE_RUN,EFFECTIVE_POST,UNDER_RUN,UNDER_POST,action,nonce]); need("binding",receipt.get("binding_key_sha256")==key)
    out=r/VALIDATION_REL; result={"schema_version":4,"slot_id":"height_difference_3","task_id":TASK_ID,"attempt_id":ATTEMPT_ID,"idempotency_key":IDEMPOTENCY,"continuation_key":CONTINUATION,"status":"COORDINATOR_REWIRE_RECEIPT_VALIDATED","validated_at_utc":now.isoformat().replace("+00:00","Z"),"receipt_age_seconds":age,"receipt_ttl_seconds":RECEIPT_TTL_SECONDS,"receipt_sha256":receipt_sha,"receipt_nonce":nonce,"coordinator_action_id":action,"local_head":local,"fresh_origin_head":remote,"request_blob_sha":rb,"current_task_blob_sha":tb,"source_queue_blob_sha":qb,"matching_queue_record_count":1,"matching_queue_records":combined,"preflight_output_sha256":actual,"binding_key_sha256":key,"effective_runtime_script":EFFECTIVE_RUN,"effective_post_publish_script":EFFECTIVE_POST,"underlying_runtime_script":UNDER_RUN,"underlying_post_publish_script":UNDER_POST,"sealed_wrapper_chain_required":True,"runtime_override_applied":True,"checks_passed":len(checks),"checks_total":len(checks),"checks":checks,"new_task_created":False,"new_runner_created":False,"parallel_runner_used":False,"queue_mutated_by_slot":False,"numeric_values_written":0,"final_ready":False,"fake_data":False}; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); print(json.dumps({"ok":True,"status":result["status"],"receipt_sha256":receipt_sha,"binding_key":key,"effective_runtime_script":EFFECTIVE_RUN,"effective_post_publish_script":EFFECTIVE_POST,"output":str(out)})); return 0
if __name__=="__main__":
    try:raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok":False,"error":f"{type(exc).__name__}: {exc}"}),file=sys.stderr); raise
