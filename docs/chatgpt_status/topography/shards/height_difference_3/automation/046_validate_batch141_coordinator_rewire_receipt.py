#!/usr/bin/env python3
"""Validate the bound coordinator receipt immediately before 039 strict runtime.

The legacy queue predates continuation_key, so duplicate census uses the stable
(task_id, attempt_id, idempotency_key) identity. Batch142 additionally binds a
coordinator action id, one-time receipt nonce and exact receipt SHA-256 so 039
can verify that the receipt did not change after validation.
"""
from __future__ import annotations
import hashlib, json, os, shutil, subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
TASK_ID="height_difference_3-canonical-api-measurement-20260721-01"; ATTEMPT_ID="height-difference-3-20260721-011"; IDEMPOTENCY="height_difference_3:canonical_security_stream:hmlr_ea_terrain50:v1"; CONTINUATION="6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f"; BRANCH="codex/aays-single-runner-v5-20260706"
RUN039="docs/chatgpt_status/topography/shards/height_difference_3/automation/039_runner_entry_batch133_prepare_publish_handoff.py"; POST040="docs/chatgpt_status/topography/shards/height_difference_3/automation/040_runner_entry_batch133_post_publish_remote_readback.py"; REQUEST_REL="docs/chatgpt_status/_shared/slots_21/height_difference_3/coordinator_requests/001_same_task_rewire_to_canonical_noarg.json"; TASK_REL="docs/chatgpt_status/_shared/slots_21/height_difference_3/current_task_latest.json"; QUEUE_REL="docs/chatgpt_status/topography/queue/height_difference_3_canonical_api_measurement_20260721_01.v3.task.json"; QUEUE_ROOT="docs/chatgpt_status/topography/queue"
RECEIPT_REL="docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/047_batch141_coordinator_rewire_receipt/coordinator_runtime_rewire_receipt.json"; VALIDATION_REL="docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/047_batch141_coordinator_rewire_receipt/coordinator_runtime_rewire_receipt_validation.json"; RECEIPT_TTL_SECONDS=600
PREFLIGHT_OUTPUTS={"043":"docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/039_batch136_exact_head_preflight/exact_branch_head_and_dependency_preflight_runtime.json","045":"docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/045_batch140_fresh_heartbeat_preflight/fresh_runner_heartbeat_preflight.json","044":"docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/041_batch137_runtime_environment_preflight/runtime_environment_preflight.json","042":"docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/037_batch135_fresh_origin_wiring_qa/fresh_origin_wiring_preflight_runtime.json","041":"docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/035_batch134_coordinator_wiring_qa/coordinator_wiring_request_validation.json"}
def repo_root(start:Path)->Path:
    for c in (start,*start.parents):
        if (c/"england_map_web").is_dir() and (c/"docs"/"chatgpt_status").is_dir(): return c
    raise RuntimeError("REPO_ROOT_NOT_FOUND")
def load_json(path:Path)->dict[str,Any]:
    v=json.loads(path.read_text(encoding="utf-8-sig"));
    if not isinstance(v,dict): raise ValueError(f"expected JSON object:{path}")
    return v
def parse_utc(value:Any)->datetime:
    t=str(value or "").strip();
    if not t: raise ValueError("missing timestamp")
    if t.endswith("Z"): t=t[:-1]+"+00:00"
    d=datetime.fromisoformat(t)
    if d.tzinfo is None: d=d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc)
def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()
def binding_key(parts:list[str])->str: return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
def resolve_git()->str:
    token=str(os.environ.get("AAYS_GIT_EXE") or "git").strip(); found=shutil.which(token)
    if found: return str(Path(found).resolve())
    p=Path(token)
    if p.is_file(): return str(p.resolve())
    raise RuntimeError(f"GIT_EXECUTABLE_NOT_FOUND:{token}")
def run_git(git:str,repo:Path,*args:str,check:bool=True)->str:
    p=subprocess.run([git,"-C",str(repo),*args],text=True,capture_output=True,check=False)
    if check and p.returncode!=0: raise RuntimeError(f"git {' '.join(args)} failed:{p.stderr[-1600:]}")
    return p.stdout.strip()
def git_blob(git:str,repo:Path,ref:str,rel:str)->str:
    v=run_git(git,repo,"rev-parse",f"{ref}:{rel}").lower()
    if len(v)!=40: raise ValueError(f"invalid Git blob:{ref}:{rel}:{v}")
    return v
def normalize_grep_hits(raw:str)->list[str]:
    hits=set()
    for line in raw.splitlines():
        token=line.strip()
        if token.startswith("HEAD:"): token=token[5:]
        if token: hits.add(token)
    return sorted(hits)
def main()->int:
    repo=repo_root(Path(__file__).resolve()); git=resolve_git(); receipt_path=repo/RECEIPT_REL
    if not receipt_path.is_file(): raise FileNotFoundError(f"coordinator rewire receipt missing:{receipt_path}")
    receipt=load_json(receipt_path); receipt_sha=sha256_file(receipt_path); task=load_json(repo/TASK_REL); request=load_json(repo/REQUEST_REL); queue=load_json(repo/QUEUE_REL); checks=[]
    def require(name:str,passed:bool,detail:Any=None):
        checks.append({"name":name,"passed":bool(passed),"detail":detail})
        if not passed: raise RuntimeError(f"COORDINATOR_RECEIPT_FAILED:{name}:{detail}")
    require("receipt_schema",int(receipt.get("schema_version") or 0)>=2,receipt.get("schema_version")); require("receipt_status",receipt.get("status")=="COORDINATOR_RUNTIME_REWIRE_RECEIPT",receipt.get("status")); require("receipt_identity",receipt.get("task_id")==TASK_ID and receipt.get("attempt_id")==ATTEMPT_ID and receipt.get("idempotency_key")==IDEMPOTENCY and receipt.get("continuation_key")==CONTINUATION); require("task_identity",task.get("task_id")==TASK_ID and task.get("attempt_id")==ATTEMPT_ID and task.get("idempotency_key")==IDEMPOTENCY and task.get("continuation_key")==CONTINUATION); require("request_identity",request.get("task_id")==TASK_ID and request.get("attempt_id")==ATTEMPT_ID and request.get("idempotency_key")==IDEMPOTENCY and request.get("continuation_key")==CONTINUATION); require("queue_identity",queue.get("task_id")==TASK_ID and queue.get("attempt_id")==ATTEMPT_ID and queue.get("idempotency_key")==IDEMPOTENCY)
    action_id=str(receipt.get("coordinator_action_id") or "").strip(); nonce=str(receipt.get("receipt_nonce") or "").strip(); require("coordinator_action_id",len(action_id)>=8,action_id); require("receipt_nonce",len(nonce)==32,nonce); require("runtime_override_applied",receipt.get("runtime_override_applied") is True); require("effective_entrypoints",receipt.get("effective_runtime_script")==RUN039 and receipt.get("effective_post_publish_script")==POST040); require("no_duplicate_creation",receipt.get("new_queue_record_created") is False and receipt.get("new_task_created") is False and receipt.get("new_runner_created") is False and receipt.get("parallel_runner_used") is False); require("coordinator_only",receipt.get("coordinator_only") is True)
    now=datetime.now(timezone.utc); created=parse_utc(receipt.get("receipt_created_at_utc")); age=(now-created).total_seconds(); require("receipt_not_future",age>=-2.0,{"age_seconds":age}); require("receipt_ttl",age<=RECEIPT_TTL_SECONDS,{"age_seconds":age,"max_age_seconds":RECEIPT_TTL_SECONDS})
    fetch_spec=f"refs/heads/{BRANCH}:refs/remotes/origin/{BRANCH}"; run_git(git,repo,"fetch","--no-tags","origin",fetch_spec); local_head=run_git(git,repo,"rev-parse","HEAD").lower(); remote_head=run_git(git,repo,"rev-parse",f"refs/remotes/origin/{BRANCH}").lower(); require("local_head_fresh_origin",len(local_head)==40 and local_head==remote_head,{"local":local_head,"remote":remote_head}); require("receipt_head_binding",receipt.get("local_head")==local_head and receipt.get("fresh_origin_head")==remote_head,{"receipt_local":receipt.get("local_head"),"receipt_remote":receipt.get("fresh_origin_head")})
    request_blob=git_blob(git,repo,"HEAD",REQUEST_REL); task_blob=git_blob(git,repo,"HEAD",TASK_REL); queue_blob=git_blob(git,repo,"HEAD",QUEUE_REL); require("request_blob_binding",receipt.get("request_blob_sha")==request_blob); require("task_blob_binding",receipt.get("current_task_blob_sha")==task_blob); require("queue_blob_binding",receipt.get("source_queue_blob_sha")==queue_blob)
    task_hits=normalize_grep_hits(run_git(git,repo,"grep","-l","-F",TASK_ID,"HEAD","--",QUEUE_ROOT,check=False)); attempt_hits=normalize_grep_hits(run_git(git,repo,"grep","-l","-F",ATTEMPT_ID,"HEAD","--",QUEUE_ROOT,check=False)); idem_hits=normalize_grep_hits(run_git(git,repo,"grep","-l","-F",IDEMPOTENCY,"HEAD","--",QUEUE_ROOT,check=False)); combined_hits=sorted(set(task_hits).intersection(attempt_hits).intersection(idem_hits)); require("single_queue_record_for_stable_identity",combined_hits==[QUEUE_REL],combined_hits); require("receipt_duplicate_census",receipt.get("queue_census_basis")==["task_id","attempt_id","idempotency_key"] and int(receipt.get("matching_queue_record_count") or -1)==1 and receipt.get("matching_queue_records")==[QUEUE_REL])
    receipt_hashes=receipt.get("preflight_output_sha256") or {}; actual_hashes={}
    for key,rel in PREFLIGHT_OUTPUTS.items():
        path=repo/rel; require(f"preflight_{key}_exists",path.is_file(),rel); payload=load_json(path); require(f"preflight_{key}_slot",payload.get("slot_id")=="height_difference_3",payload.get("slot_id"));
        if payload.get("task_id") is not None: require(f"preflight_{key}_task",payload.get("task_id")==TASK_ID,payload.get("task_id"))
        if payload.get("continuation_key") is not None: require(f"preflight_{key}_continuation",payload.get("continuation_key")==CONTINUATION,payload.get("continuation_key"))
        actual=sha256_file(path); actual_hashes[key]=actual; require(f"preflight_{key}_sha256",receipt_hashes.get(key)==actual)
    expected_binding=binding_key([TASK_ID,ATTEMPT_ID,IDEMPOTENCY,CONTINUATION,request_blob,task_blob,queue_blob,local_head,*(actual_hashes[k] for k in ("043","045","044","042","041")),RUN039,POST040,action_id,nonce]); require("receipt_binding_key",receipt.get("binding_key_sha256")==expected_binding)
    output=repo/VALIDATION_REL; result={"schema_version":3,"slot_id":"height_difference_3","task_id":TASK_ID,"attempt_id":ATTEMPT_ID,"idempotency_key":IDEMPOTENCY,"continuation_key":CONTINUATION,"status":"COORDINATOR_REWIRE_RECEIPT_VALIDATED","validated_at_utc":now.isoformat().replace("+00:00","Z"),"receipt_age_seconds":age,"receipt_ttl_seconds":RECEIPT_TTL_SECONDS,"receipt_sha256":receipt_sha,"receipt_nonce":nonce,"coordinator_action_id":action_id,"fresh_origin_fetch_refspec":fetch_spec,"local_head":local_head,"fresh_origin_head":remote_head,"request_blob_sha":request_blob,"current_task_blob_sha":task_blob,"source_queue_blob_sha":queue_blob,"queue_census_basis":["task_id","attempt_id","idempotency_key"],"matching_queue_record_count":1,"matching_queue_records":combined_hits,"preflight_output_sha256":actual_hashes,"binding_key_sha256":expected_binding,"effective_runtime_script":RUN039,"effective_post_publish_script":POST040,"runtime_override_applied":True,"checks_passed":len(checks),"checks_total":len(checks),"checks":checks,"new_task_created":False,"new_runner_created":False,"parallel_runner_used":False,"queue_mutated_by_slot":False,"numeric_values_written":0,"final_ready":False,"fake_data":False}; output.parent.mkdir(parents=True,exist_ok=True); output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); print(json.dumps({"ok":True,"status":result["status"],"queue_records":1,"head":local_head,"receipt_sha256":receipt_sha,"receipt_nonce":nonce,"binding_key":expected_binding,"output":str(output)})); return 0
if __name__=="__main__":
    try: raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok":False,"error":f"{type(exc).__name__}: {exc}"}),file=sys.stderr); raise
