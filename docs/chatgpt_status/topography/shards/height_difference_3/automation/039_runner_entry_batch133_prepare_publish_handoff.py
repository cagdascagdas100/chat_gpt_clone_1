#!/usr/bin/env python3
"""Same-task strict12 entrypoint with fresh-host, runtime-identity and receipt-seal gates."""
from __future__ import annotations
import hashlib,json,os,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
from typing import Any
TASK_ID="height_difference_3-canonical-api-measurement-20260721-01"; CONTINUATION="6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f"; BRANCH="codex/aays-single-runner-v5-20260706"; EXPECTED_ROWS=list(range(61540,61552)); PREFLIGHT_TTL_SECONDS=900
TASK_REL="docs/chatgpt_status/_shared/slots_21/height_difference_3/current_task_latest.json"; HEARTBEAT_PREFLIGHT_REL="docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/045_batch140_fresh_heartbeat_preflight/fresh_runner_heartbeat_preflight.json"; ENV_PREFLIGHT_REL="docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/041_batch137_runtime_environment_preflight/runtime_environment_preflight.json"; RECEIPT_REL="docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/047_batch141_coordinator_rewire_receipt/coordinator_runtime_rewire_receipt.json"; RECEIPT_VALIDATOR_REL="docs/chatgpt_status/topography/shards/height_difference_3/automation/046_validate_batch141_coordinator_rewire_receipt.py"; RECEIPT_VALIDATION_REL="docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/047_batch141_coordinator_rewire_receipt/coordinator_runtime_rewire_receipt_validation.json"
def root(p:Path)->Path:
    for c in (p,*p.parents):
        if (c/"england_map_web").is_dir() and (c/"docs/chatgpt_status").is_dir():return c
    raise RuntimeError("PUBLISHER_REPO_ROOT_NOT_FOUND")
def load(p:Path)->dict[str,Any]:
    v=json.loads(p.read_text(encoding="utf-8-sig"));
    if not isinstance(v,dict):raise ValueError(f"expected JSON object:{p}")
    return v
def run(cmd:list[str],cwd:Path,env:dict[str,str]|None=None)->dict[str,Any]:
    p=subprocess.run(cmd,cwd=cwd,env=env,text=True,capture_output=True,check=False);return {"command":cmd,"exit_code":p.returncode,"stdout":p.stdout[-16000:],"stderr":p.stderr[-16000:]}
def write(p:Path,v:dict[str,Any])->None:p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def norm(v:str)->str:return os.path.normcase(str(Path(v).resolve()))
def parse(v:Any)->datetime:
    t=str(v or "").strip();
    if not t:raise ValueError("missing timestamp")
    if t.endswith("Z"):t=t[:-1]+"+00:00"
    d=datetime.fromisoformat(t);return (d if d.tzinfo else d.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)
def sha(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()
def main()->int:
    script_dir=Path(__file__).resolve().parent; repo=root(script_dir); task=load(repo/TASK_REL)
    if task.get("task_id")!=TASK_ID or task.get("continuation_key")!=CONTINUATION:raise ValueError("current task identity mismatch")
    if task.get("single_runner_only") is not True or task.get("new_runner") is not False or task.get("parallel_runner") is not False:raise ValueError("single-runner contract mismatch")
    hb=load(repo/HEARTBEAT_PREFLIGHT_REL)
    if int(hb.get("schema_version") or 0)<2 or hb.get("task_id")!=TASK_ID or hb.get("continuation_key")!=CONTINUATION or hb.get("fresh_host_heartbeat_passed") is not True:raise ValueError("fresh heartbeat receipt mismatch")
    if hb.get("environment_gate_044_executed") is not True or int(hb.get("environment_gate_044_exit_code") or -1)!=0:raise ValueError("heartbeat chain did not complete 044")
    if float(hb.get("global_heartbeat_age_seconds") or 1e18)>float(hb.get("entry_max_global_heartbeat_age_seconds") or 0):raise ValueError("heartbeat receipt exceeds reserved freshness budget")
    env=load(repo/ENV_PREFLIGHT_REL)
    if int(env.get("schema_version") or 0)<4 or int(env.get("checks_passed") or -1)!=int(env.get("checks_total") or -2) or env.get("bootstrap_042_executed") is not True or int(env.get("bootstrap_042_exit_code") or -1)!=0 or int(env.get("numeric_values_written") or 0)!=0 or env.get("canonical_branch")!=BRANCH:raise ValueError("runtime environment preflight mismatch")
    now=datetime.now(timezone.utc); hbc=parse(hb.get("checked_at_utc")); hbd=parse(hb.get("completed_at_utc")); gen=parse(env.get("generated_at_utc")); until=parse(env.get("valid_until_utc")); ttl=int(env.get("preflight_ttl_seconds") or 0)
    if ttl!=PREFLIGHT_TTL_SECONDS or gen>now or now>until or abs((until-gen).total_seconds()-PREFLIGHT_TTL_SECONDS)>2 or not(hbc<=gen<=hbd):raise ValueError("runtime preflight TTL/window mismatch")
    ri=env.get("runtime_identity") or {}; py=str(ri.get("python_executable") or env.get("python_executable") or "").strip(); ps=str(ri.get("powershell_executable") or env.get("powershell_path") or "").strip(); gx=str(ri.get("git_executable") or env.get("git_executable") or "").strip()
    for p,name in ((py,"Python"),(ps,"PowerShell"),(gx,"Git")):
        if not p or not Path(p).is_file():raise ValueError(f"validated {name} executable missing")
    if norm(py)!=norm(sys.executable):raise ValueError("runtime Python identity drift")
    py=str(Path(sys.executable).resolve()); ps=str(Path(ps).resolve()); gx=str(Path(gx).resolve())
    lh=run([gx,"-C",str(repo),"rev-parse","HEAD"],repo); local=lh["stdout"].strip().lower()
    if lh["exit_code"]!=0 or len(local)!=40 or local!=str(env.get("canonical_head") or "").lower():raise ValueError("runtime local HEAD drift")
    tb=run([gx,"-C",str(repo),"rev-parse",f"HEAD:{TASK_REL}"],repo); task_blob=tb["stdout"].strip().lower()
    if tb["exit_code"]!=0 or len(task_blob)!=40 or task_blob!=str(env.get("canonical_current_task_blob_sha") or "").lower():raise ValueError("runtime current-task blob drift")
    validator=repo/RECEIPT_VALIDATOR_REL; receipt=repo/RECEIPT_REL; validation=repo/RECEIPT_VALIDATION_REL
    if not validator.is_file() or not receipt.is_file():raise FileNotFoundError("receipt validator/receipt missing")
    receipt_sha_before=sha(receipt); renv=os.environ.copy(); renv["AAYS_GIT_EXE"]=gx; vr=run([py,str(validator)],repo,renv)
    if vr["exit_code"]!=0:raise RuntimeError(f"coordinator receipt validation failed:{vr['stderr'][-2400:]}")
    if not validation.is_file():raise FileNotFoundError(validation)
    val=load(validation); receipt_sha_validated=sha(receipt); validation_sha_validated=sha(validation)
    if receipt_sha_before!=receipt_sha_validated or val.get("receipt_sha256")!=receipt_sha_validated:raise RuntimeError("COORDINATOR_RECEIPT_CHANGED_AROUND_046")
    if val.get("status")!="COORDINATOR_REWIRE_RECEIPT_VALIDATED" or val.get("task_id")!=TASK_ID or val.get("continuation_key")!=CONTINUATION or int(val.get("matching_queue_record_count") or 0)!=1 or val.get("local_head")!=local or val.get("fresh_origin_head")!=local or val.get("current_task_blob_sha")!=task_blob or val.get("runtime_override_applied") is not True:raise ValueError("coordinator receipt validation contract mismatch")
    strict=script_dir/"036_run_batch131_strict12_with_local_acceptance.ps1"; manifest_gen=script_dir/"037_prepare_batch132_publish_manifest.py"
    if not strict.is_file() or not manifest_gen.is_file():raise FileNotFoundError("strict/manifest script missing")
    sr=run([ps,"-NoProfile","-ExecutionPolicy","Bypass","-File",str(strict),"-RepoRoot",str(repo),"-PythonExe",py,"-PowerShellExe",ps],repo)
    if sr["exit_code"]!=0:raise RuntimeError(f"strict/local acceptance failed:{sr['stderr'][-2000:]}")
    if sha(receipt)!=receipt_sha_validated or sha(validation)!=validation_sha_validated:raise RuntimeError("CONTROL_PLANE_RECEIPT_OR_VALIDATION_CHANGED_DURING_STRICT")
    acc=load(repo/"docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/029_batch131_strict12_acceptance/batch131_strict12_local_acceptance.json")
    if acc.get("local_acceptance_passed") is not True or [int(v) for v in acc.get("expected_rows") or []]!=EXPECTED_ROWS or acc.get("remote_github_readback_required") is not True:raise ValueError("local acceptance mismatch")
    spec=f"refs/heads/{BRANCH}:refs/remotes/origin/{BRANCH}"; fr=run([gx,"-C",str(repo),"fetch","--no-tags","origin",spec],repo)
    if fr["exit_code"]!=0:raise RuntimeError(f"pre-publish origin fetch failed:{fr['stderr'][-2000:]}")
    hr=run([gx,"-C",str(repo),"rev-parse",f"refs/remotes/origin/{BRANCH}"],repo); pre=hr["stdout"].strip().lower()
    if hr["exit_code"]!=0 or len(pre)!=40:raise RuntimeError("cannot resolve pre-publish origin HEAD")
    manifest=repo/"docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/031_batch132_remote_readback/batch132_publish_manifest.json"; mr=run([py,str(manifest_gen),"--repo-root",str(repo),"--output",str(manifest),"--pre-publish-origin-head",pre],repo)
    if mr["exit_code"]!=0:raise RuntimeError(f"publish manifest generation failed:{mr['stderr'][-2000:]}")
    m=load(manifest)
    if int(m.get("schema_version") or 0)<2 or m.get("ready_for_serial_publisher") is not True or m.get("task_id")!=TASK_ID or m.get("continuation_key")!=CONTINUATION or [int(v) for v in m.get("expected_rows") or []]!=EXPECTED_ROWS or len(m.get("files") or [])!=7 or str(m.get("pre_publish_origin_head") or "").lower()!=pre:raise ValueError("publish manifest mismatch")
    if sha(receipt)!=receipt_sha_validated or sha(validation)!=validation_sha_validated:raise RuntimeError("CONTROL_PLANE_RECEIPT_OR_VALIDATION_CHANGED_BEFORE_HANDOFF")
    out=repo/"docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/033_batch133_coordinator_handoff/batch133_prepare_publish_handoff.json"; payload={"schema_version":7,"slot_id":"height_difference_3","task_id":TASK_ID,"continuation_key":CONTINUATION,"status":"PUBLISH_PENDING_SERIAL_PUBLISHER_REQUIRED","fresh_heartbeat_preflight":HEARTBEAT_PREFLIGHT_REL,"fresh_host_heartbeat_passed":True,"runtime_identity_preflight":ENV_PREFLIGHT_REL,"runtime_preflight_generated_at_utc":env.get("generated_at_utc"),"runtime_preflight_valid_until_utc":env.get("valid_until_utc"),"runtime_preflight_ttl_seconds":PREFLIGHT_TTL_SECONDS,"runtime_preflight_head":local,"runtime_preflight_current_task_blob_sha":task_blob,"coordinator_rewire_receipt":RECEIPT_REL,"coordinator_rewire_receipt_validation":RECEIPT_VALIDATION_REL,"coordinator_rewire_receipt_validated":True,"coordinator_receipt_sha256":receipt_sha_validated,"coordinator_receipt_validation_sha256":validation_sha_validated,"coordinator_receipt_binding_key_sha256":val.get("binding_key_sha256"),"coordinator_action_id":val.get("coordinator_action_id"),"coordinator_receipt_nonce":val.get("receipt_nonce"),"coordinator_receipt_matching_queue_record_count":1,"control_plane_receipt_validation_seal_passed":True,"runtime_entry_fresh_origin_head":val.get("fresh_origin_head"),"runtime_python_executable":py,"runtime_powershell_executable":ps,"runtime_git_executable":gx,"runtime_identity_match_passed":True,"runtime_preflight_freshness_and_head_binding_passed":True,"strict_local_acceptance_passed":True,"canonical_branch":BRANCH,"pre_publish_origin_fetch_refspec":spec,"pre_publish_origin_fetch_performed":True,"pre_publish_origin_head":pre,"expected_rows":EXPECTED_ROWS,"expected_verified_count":12,"publish_manifest":str(manifest.relative_to(repo)).replace("\\","/"),"publish_file_count":7,"serial_publisher_required":True,"child_direct_push_performed":False,"post_publish_entrypoint":"docs/chatgpt_status/topography/shards/height_difference_3/automation/040_runner_entry_batch133_post_publish_remote_readback.py","numeric_final_acceptance":"PENDING_SERIAL_PUBLISH_REMOTE_HISTORY_AND_CONTROL_PLANE_SEAL_READBACK","new_task_created":False,"new_runner_created":False,"parallel_runner_used":False,"numeric_values_changed":0,"final_ready":False,"fake_data":False,"stages":{"coordinator_rewire_receipt_validation":vr,"strict_local_acceptance":sr,"pre_publish_origin_fetch":fr,"pre_publish_origin_head":hr,"publish_manifest":mr}}; write(out,payload); print(json.dumps({"ok":True,"status":payload["status"],"pre_publish_origin_head":pre,"receipt_sha256":receipt_sha_validated,"validation_sha256":validation_sha_validated,"output":str(out)}));return 0
if __name__=="__main__":
    try:raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok":False,"error":f"{type(exc).__name__}: {exc}"}),file=sys.stderr);raise
