#!/usr/bin/env python3
"""Fail-closed exact branch/HEAD and tracked-input preflight for height_difference_3."""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from typing import Any
BRANCH="codex/aays-single-runner-v5-20260706"
TASK_REL="docs/chatgpt_status/_shared/slots_21/height_difference_3/current_task_latest.json"
ENV_GATE_REL="docs/chatgpt_status/topography/shards/height_difference_3/automation/044_run_batch137_runtime_environment_preflight.py"
TASK_ID="height_difference_3-canonical-api-measurement-20260721-01"
CONT="6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f"
EXPECTED_READ_PATH_COUNT=48
EXPECTED_OUTPUT_COUNT=19

def root(p:Path)->Path:
    for c in (p,*p.parents):
        if (c/"england_map_web").is_dir() and (c/"docs/chatgpt_status").is_dir(): return c
    raise RuntimeError("REPO_ROOT_NOT_FOUND")
def git(repo:Path,*args:str)->str:
    p=subprocess.run(["git","-C",str(repo),*args],text=True,capture_output=True,check=False)
    if p.returncode: raise RuntimeError(f"git {' '.join(args)} failed: {p.stderr[-1600:]}")
    return p.stdout.strip()
def load(p:Path)->dict[str,Any]:
    v=json.loads(p.read_text(encoding="utf-8-sig"));
    if not isinstance(v,dict): raise ValueError(f"expected JSON object: {p}")
    return v

def main()->int:
    repo=root(Path(__file__).resolve())
    branch=git(repo,"symbolic-ref","--quiet","--short","HEAD")
    if branch!=BRANCH: raise RuntimeError(f"WRONG_OR_DETACHED_BRANCH:{branch!r}:expected={BRANCH}")
    spec=f"refs/heads/{BRANCH}:refs/remotes/origin/{BRANCH}"
    git(repo,"fetch","--no-tags","origin",spec)
    remote=git(repo,"rev-parse",f"refs/remotes/origin/{BRANCH}"); local=git(repo,"rev-parse","HEAD")
    if local!=remote: raise RuntimeError(f"LOCAL_HEAD_NOT_FRESH_ORIGIN:{local}:{remote}")
    task=load(repo/TASK_REL)
    if task.get("task_id")!=TASK_ID or task.get("continuation_key")!=CONT: raise ValueError("current task identity mismatch")
    reads=[str(x) for x in task.get("read_paths") or []]; outs=[str(x) for x in task.get("expected_outputs") or []]
    if len(reads)!=EXPECTED_READ_PATH_COUNT: raise ValueError(f"expected {EXPECTED_READ_PATH_COUNT} read paths, got {len(reads)}")
    if len(outs)!=EXPECTED_OUTPUT_COUNT: raise ValueError(f"expected {EXPECTED_OUTPUT_COUNT} outputs, got {len(outs)}")
    if len(set(reads))!=len(reads) or len(set(outs))!=len(outs): raise ValueError("duplicate task path")
    tracked=[]
    for rel in reads:
        p=subprocess.run(["git","-C",str(repo),"cat-file","-e",f"HEAD:{rel}"],text=True,capture_output=True,check=False)
        if p.returncode: raise RuntimeError(f"UNTRACKED_OR_MISSING_READ_PATH:{rel}:{p.stderr[-600:]}")
        tracked.append({"path":rel,"tracked_at_head":True})
    status=git(repo,"status","--porcelain","--untracked-files=no","--",*reads)
    if status: raise RuntimeError(f"TASK_READ_PATH_WORKTREE_DIRTY:{status[-4000:]}")
    gate=repo/ENV_GATE_REL
    if not gate.is_file(): raise FileNotFoundError(gate)
    p=subprocess.run([sys.executable,str(gate)],cwd=repo,text=True,capture_output=True,check=False)
    if p.returncode: raise RuntimeError(f"BATCH139_ENVIRONMENT_GATE_FAILED:{p.stderr[-3000:]}")
    payload={"schema_version":5,"slot_id":"height_difference_3","canonical_branch":BRANCH,"symbolic_branch_verified":True,"explicit_fetch_refspec":spec,"local_head":local,"fresh_remote_head":remote,"exact_head_parity":True,"current_task_read_path_count":len(reads),"current_task_expected_output_count":len(outs),"generated_expected_outputs_not_required_at_head":True,"all_read_paths_tracked_at_head":True,"read_path_rows":tracked,"task_read_path_worktree_clean":True,"environment_gate_044_executed":True,"environment_gate_044_exit_code":p.returncode,"environment_gate_044_stdout_tail":p.stdout[-4000:],"coordinator_action_performed":False,"queue_mutated":False,"runner_started":False,"numeric_values_written":0,"final_ready":False,"fake_data":False}
    out=repo/"docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/039_batch136_exact_head_preflight/exact_branch_head_and_dependency_preflight_runtime.json"
    out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"ok":True,"head":local,"read_paths":len(reads),"outputs":len(outs),"output":str(out)})); return 0
if __name__=="__main__":
    try: raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok":False,"error":f"{type(exc).__name__}: {exc}"}),file=sys.stderr); raise
