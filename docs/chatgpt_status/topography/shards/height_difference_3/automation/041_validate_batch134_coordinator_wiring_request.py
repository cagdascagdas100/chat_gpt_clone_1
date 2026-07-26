#!/usr/bin/env python3
"""Fail-closed same-task coordinator wiring validator for height_difference_3 Batch139."""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from typing import Any
TASK_ID="height_difference_3-canonical-api-measurement-20260721-01"; ATTEMPT="height-difference-3-20260721-011"; CONT="6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f"; BRANCH="codex/aays-single-runner-v5-20260706"
LEGACY="docs/chatgpt_status/topography/shards/height_difference_3/automation/023_runner_entry_canonical_api_measurement.py"; RUN039="docs/chatgpt_status/topography/shards/height_difference_3/automation/039_runner_entry_batch133_prepare_publish_handoff.py"; POST040="docs/chatgpt_status/topography/shards/height_difference_3/automation/040_runner_entry_batch133_post_publish_remote_readback.py"; P037="docs/chatgpt_status/topography/shards/height_difference_3/automation/037_prepare_batch132_publish_manifest.py"; READ038="docs/chatgpt_status/topography/shards/height_difference_3/automation/038_verify_batch132_origin_remote_readback.ps1"
REQUEST="docs/chatgpt_status/_shared/slots_21/height_difference_3/coordinator_requests/001_same_task_rewire_to_canonical_noarg.json"; TASK="docs/chatgpt_status/_shared/slots_21/height_difference_3/current_task_latest.json"; QUEUE="docs/chatgpt_status/topography/queue/height_difference_3_canonical_api_measurement_20260721_01.v3.task.json"; OWNER="docs/chatgpt_status/_shared/slots_21/height_difference_3/ownership_latest.json"
V041="docs/chatgpt_status/topography/shards/height_difference_3/automation/041_validate_batch134_coordinator_wiring_request.py"; B042="docs/chatgpt_status/topography/shards/height_difference_3/automation/042_run_batch135_fresh_origin_wiring_preflight.py"; H043="docs/chatgpt_status/topography/shards/height_difference_3/automation/043_run_batch136_exact_branch_head_and_dependency_preflight.py"; E044="docs/chatgpt_status/topography/shards/height_difference_3/automation/044_run_batch137_runtime_environment_preflight.py"
S036="docs/chatgpt_status/topography/shards/height_difference_3/automation/036_run_batch131_strict12_with_local_acceptance.ps1"; S033="docs/chatgpt_status/topography/shards/height_difference_3/automation/033_run_batch130_prepare12_strict_measurement_chain.ps1"; S032="docs/chatgpt_status/topography/shards/height_difference_3/automation/032_run_batch129_range_extract_and_prepare12.ps1"; R076="docs/chatgpt_status/topography/shards/height_difference_3/runner_inputs/076_batch138_runtime_executable_identity_resume.json"; R077="docs/chatgpt_status/topography/shards/height_difference_3/runner_inputs/077_batch139_remote_history_binding_resume.json"; ENVOUT="docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/041_batch137_runtime_environment_preflight/runtime_environment_preflight.json"
EXPECTED_ROWS=list(range(61540,61552)); NREAD=48; NOUT=19

def root(p:Path)->Path:
    for c in (p,*p.parents):
        if (c/"england_map_web").is_dir() and (c/"docs/chatgpt_status").is_dir(): return c
    raise RuntimeError("REPO_ROOT_NOT_FOUND")
def load(p:Path)->dict[str,Any]:
    v=json.loads(p.read_text(encoding="utf-8-sig"));
    if not isinstance(v,dict): raise ValueError(f"expected object: {p}")
    return v
def git(repo:Path,*a:str)->str:
    p=subprocess.run(["git","-C",str(repo),*a],text=True,capture_output=True,check=False)
    if p.returncode: raise RuntimeError(f"git {' '.join(a)} failed: {p.stderr[-1200:]}")
    return p.stdout.strip()
def blob(repo:Path,ref:str,rel:str)->str:
    v=git(repo,"rev-parse",f"{ref}:{rel}").lower()
    if len(v)!=40: raise ValueError(f"bad blob:{ref}:{rel}:{v}")
    return v

def main()->int:
    repo=root(Path(__file__).resolve()); req=load(repo/REQUEST); task=load(repo/TASK); queue=load(repo/QUEUE); own=load(repo/OWNER); checks=[]
    def ck(n:str,p:bool,d:Any=None):
        checks.append({"name":n,"passed":bool(p),"detail":d})
        if not p: raise ValueError(f"wiring validation failed:{n}:{d}")
    ck("schema6",int(req.get("schema_version") or 0)>=6); ck("identity",req.get("task_id")==TASK_ID and req.get("attempt_id")==ATTEMPT and req.get("continuation_key")==CONT)
    ck("no_duplicate",req.get("new_task_forbidden") is True and req.get("duplicate_task_forbidden") is True and req.get("new_runner_forbidden") is True and req.get("parallel_runner_forbidden") is True)
    ck("task_identity",task.get("task_id")==TASK_ID and task.get("attempt_id")==ATTEMPT and task.get("continuation_key")==CONT); ck("task_entrypoints",task.get("script_path")==RUN039 and task.get("post_publish_script_path")==POST040)
    reads=list(task.get("read_paths") or []); outs=list(task.get("expected_outputs") or []); ck("task_48_reads",len(reads)==NREAD,len(reads)); ck("task_19_outputs",len(outs)==NOUT,len(outs)); ck("resume076_readable",R076 in reads); ck("resume077_readable",R077 in reads); ck("env_identity_is_generated_output",ENVOUT in outs and ENVOUT not in reads)
    ck("queue_identity",queue.get("task_id")==TASK_ID and queue.get("attempt_id")==ATTEMPT); ck("queue_single_runner",queue.get("single_runner_only") is True and queue.get("new_runner") is False and queue.get("parallel_runner") is False); ck("queue_script_known",queue.get("script_path") in {LEGACY,RUN039},queue.get("script_path"))
    spec=f"refs/heads/{BRANCH}:refs/remotes/origin/{BRANCH}"; git(repo,"fetch","--no-tags","origin",spec); remote=git(repo,"rev-parse",f"refs/remotes/origin/{BRANCH}"); local=git(repo,"rev-parse","HEAD"); ck("heads",len(remote)==40 and len(local)==40)
    pre=req.get("preconditions") or {}; ck("scope_contract",int(pre.get("canonical_current_task_read_path_count_required") or 0)==NREAD and int(pre.get("canonical_current_task_expected_output_count_required") or 0)==NOUT); ck("identity_contract",pre.get("runtime_executable_identity_required") is True and pre.get("preflight_python_must_equal_runtime_python") is True and pre.get("preflight_powershell_must_equal_runtime_powershell") is True and pre.get("preflight_git_must_equal_remote_readback_git") is True); ck("history_preconditions",pre.get("fresh_pre_publish_origin_head_required") is True and pre.get("remote_history_binding_required") is True)
    tb=blob(repo,remote,TASK); qb=blob(repo,remote,QUEUE); ck("task_pin",tb==str(pre.get("canonical_current_task_expected_blob_sha") or "").lower(),tb); ck("queue_pin",qb==str(pre.get("legacy_queue_expected_blob_sha") or "").lower(),qb); ck("local_task_remote",blob(repo,"HEAD",TASK)==tb); ck("local_queue_remote",blob(repo,"HEAD",QUEUE)==qb)
    paths=[REQUEST,TASK,QUEUE,P037,RUN039,POST040,READ038,V041,B042,H043,E044,S036,S033,S032,R076,R077]; rb={}; rows=[]
    for rel in paths:
        lb=blob(repo,"HEAD",rel); r=blob(repo,remote,rel); ck(f"parity:{rel}",lb==r,{"local":lb,"remote":r}); rb[rel]=r; rows.append({"path":rel,"local_head_blob":lb,"remote_blob":r})
    ck("critical_clean",git(repo,"status","--porcelain","--untracked-files=no","--",*paths)=="")
    vc=req.get("validator_chain") or {}; ic=req.get("runtime_identity_chain") or {}; hc=req.get("remote_history_chain") or {}; ov=req.get("coordinator_runtime_override") or {}
    pins=[("043",vc.get("exact_branch_head_gate_expected_blob_sha"),H043),("044",vc.get("runtime_environment_gate_expected_blob_sha"),E044),("042",vc.get("fresh_origin_bootstrap_expected_blob_sha"),B042),("041",vc.get("same_task_validator_expected_blob_sha"),V041),("039",ov.get("runtime_script_expected_blob_sha"),RUN039),("040",ov.get("post_publish_script_expected_blob_sha"),POST040),("037",hc.get("publish_manifest_037_expected_blob_sha"),P037),("038",hc.get("remote_readback_038_expected_blob_sha"),READ038),("036",ic.get("strict036_expected_blob_sha"),S036),("033",ic.get("strict033_expected_blob_sha"),S033),("032",ic.get("strict032_expected_blob_sha"),S032),("076",ic.get("resume_076_expected_blob_sha"),R076),("077",hc.get("resume_077_expected_blob_sha"),R077)]
    for n,p,rel in pins: ck(f"pin_{n}",str(p or "").lower()==rb[rel],{"pin":p,"remote":rb[rel]})
    ck("identity_propagation",ic.get("python_executable_propagates_044_039_036_033_032_and_040") is True and ic.get("powershell_executable_propagates_044_039_036_033_032_and_040") is True and ic.get("git_executable_propagates_044_039_handoff_040_038") is True and ic.get("runtime_039_consumes_preflight_identity_record") is True and ic.get("post_publish_040_consumes_039_identity_handoff") is True)
    ck("history_binding",hc.get("runtime_039_captures_fresh_pre_publish_origin_head") is True and hc.get("manifest_binds_pre_publish_origin_head") is True and hc.get("pre_publish_head_must_be_ancestor_of_remote_head") is True and hc.get("first_full_blob_materialization_commit_required_when_not_already_present") is True and hc.get("already_present_at_pre_publish_head_is_idempotent_no_replay_state") is True and hc.get("post_publish_040_requires_remote_history_binding") is True)
    ck("override",ov.get("use_existing_queue_record") is True and ov.get("do_not_create_new_queue_record") is True and ov.get("runtime_script_path")==RUN039 and ov.get("post_publish_script_path")==POST040 and ov.get("runtime_arguments")==[] and ov.get("post_publish_arguments")==[]); ck("rows",[int(x) for x in req.get("expected_rows") or []]==EXPECTED_ROWS)
    os=str(own.get("state") or ""); oid=own.get("owner_page_session_id"); ck("owner_safe",os=="UNCLAIMED" or (os=="CLAIMED" and oid=="chatgpt-height-difference-3-batch139-20260726"),{"state":os,"owner":oid})
    out=repo/"docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/035_batch134_coordinator_wiring_qa/coordinator_wiring_request_validation.json"; payload={"schema_version":7,"slot_id":"height_difference_3","task_id":TASK_ID,"continuation_key":CONT,"status":"ALREADY_ALIGNED" if queue.get("script_path")==RUN039 else "SAFE_FOR_COORDINATOR_RUNTIME_REWIRE_AFTER_ALL_PREFLIGHT_GATES","checks_passed":len(checks),"checks_total":len(checks),"checks":checks,"fresh_remote_head":remote,"critical_blob_parity":rows,"expected_read_path_count":NREAD,"expected_output_count":NOUT,"runtime_executable_identity_chain_pinned":True,"pre_publish_origin_head_and_remote_history_binding_pinned":True,"runtime_environment_record_is_generated_expected_output":True,"fresh_host_heartbeat_still_required":True,"coordinator_action_performed":False,"legacy_queue_mutated":False,"new_task_created":False,"new_runner_created":False,"numeric_values_written":0,"expected_rows":EXPECTED_ROWS,"final_ready":False,"fake_data":False}; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); print(json.dumps({"ok":True,"checks":len(checks),"output":str(out)})); return 0
if __name__=="__main__":
    try: raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok":False,"error":f"{type(exc).__name__}: {exc}"}),file=sys.stderr); raise
