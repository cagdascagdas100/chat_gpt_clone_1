#!/usr/bin/env python3
"""Post-publish readback with remote-history and control-plane receipt seals."""
from __future__ import annotations
import hashlib,json,os,subprocess,sys
from pathlib import Path
from typing import Any
TASK_ID="height_difference_3-canonical-api-measurement-20260721-01"; CONTINUATION="6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f"; EXPECTED_ROWS=list(range(61540,61552))
RECEIPT_REL="docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/047_batch141_coordinator_rewire_receipt/coordinator_runtime_rewire_receipt.json"; VALIDATION_REL="docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/047_batch141_coordinator_rewire_receipt/coordinator_runtime_rewire_receipt_validation.json"
def root(p:Path)->Path:
    for c in (p,*p.parents):
        if (c/"england_map_web").is_dir() and (c/"docs/chatgpt_status").is_dir():return c
    raise RuntimeError("PUBLISHER_REPO_ROOT_NOT_FOUND")
def load(p:Path)->dict[str,Any]:
    v=json.loads(p.read_text(encoding="utf-8-sig"));
    if not isinstance(v,dict):raise ValueError(f"expected JSON object:{p}")
    return v
def run(cmd:list[str],cwd:Path)->dict[str,Any]:
    p=subprocess.run(cmd,cwd=cwd,text=True,capture_output=True,check=False);return {"command":cmd,"exit_code":p.returncode,"stdout":p.stdout[-16000:],"stderr":p.stderr[-16000:]}
def write(p:Path,v:dict[str,Any])->None:p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def norm(v:str)->str:return os.path.normcase(str(Path(v).resolve()))
def sha(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()
def main()->int:
    script_dir=Path(__file__).resolve().parent; repo=root(script_dir); task=load(repo/"docs/chatgpt_status/_shared/slots_21/height_difference_3/current_task_latest.json")
    if task.get("task_id")!=TASK_ID or task.get("continuation_key")!=CONTINUATION:raise ValueError("current task/continuation mismatch")
    hp=repo/"docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/033_batch133_coordinator_handoff/batch133_prepare_publish_handoff.json"; h=load(hp)
    if int(h.get("schema_version") or 0)<7 or h.get("status")!="PUBLISH_PENDING_SERIAL_PUBLISHER_REQUIRED" or [int(v) for v in h.get("expected_rows") or []]!=EXPECTED_ROWS:raise ValueError("pre-publish handoff seal/schema mismatch")
    if h.get("runtime_identity_match_passed") is not True or h.get("fresh_host_heartbeat_passed") is not True or h.get("runtime_preflight_freshness_and_head_binding_passed") is not True or h.get("control_plane_receipt_validation_seal_passed") is not True:raise ValueError("pre-publish runtime/control-plane gates missing")
    receipt=repo/RECEIPT_REL; validation=repo/VALIDATION_REL
    if not receipt.is_file() or not validation.is_file():raise FileNotFoundError("receipt/validation missing")
    expected_receipt=str(h.get("coordinator_receipt_sha256") or ""); expected_validation=str(h.get("coordinator_receipt_validation_sha256") or "")
    if len(expected_receipt)!=64 or len(expected_validation)!=64:raise ValueError("handoff receipt seal missing")
    before_receipt=sha(receipt); before_validation=sha(validation)
    if before_receipt!=expected_receipt or before_validation!=expected_validation:raise RuntimeError("CONTROL_PLANE_SEAL_CHANGED_BEFORE_REMOTE_READBACK")
    val=load(validation)
    if val.get("receipt_sha256")!=expected_receipt or val.get("binding_key_sha256")!=h.get("coordinator_receipt_binding_key_sha256") or val.get("coordinator_action_id")!=h.get("coordinator_action_id") or val.get("receipt_nonce")!=h.get("coordinator_receipt_nonce"):raise ValueError("handoff/validation seal identity mismatch")
    pre=str(h.get("pre_publish_origin_head") or "").strip().lower()
    if len(pre)!=40 or h.get("pre_publish_origin_fetch_performed") is not True:raise ValueError("pre-publish origin proof missing")
    py=str(h.get("runtime_python_executable") or "").strip(); ps=str(h.get("runtime_powershell_executable") or "").strip(); gx=str(h.get("runtime_git_executable") or "").strip()
    for p,name in ((py,"Python"),(ps,"PowerShell"),(gx,"Git")):
        if not p or not Path(p).is_file():raise ValueError(f"handoff runtime {name} missing")
    if norm(py)!=norm(sys.executable):raise ValueError("post-publish Python identity drift")
    ps=str(Path(ps).resolve()); gx=str(Path(gx).resolve()); verifier=script_dir/"038_verify_batch132_origin_remote_readback.ps1"
    if not verifier.is_file():raise FileNotFoundError(verifier)
    rr=run([ps,"-NoProfile","-ExecutionPolicy","Bypass","-File",str(verifier),"-RepoRoot",str(repo),"-GitExe",gx],repo)
    if rr["exit_code"]!=0:raise RuntimeError(f"origin remote readback failed:{rr['stderr'][-2000:]}")
    if sha(receipt)!=expected_receipt or sha(validation)!=expected_validation:raise RuntimeError("CONTROL_PLANE_SEAL_CHANGED_DURING_REMOTE_READBACK")
    remote=load(repo/"docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/031_batch132_remote_readback/batch132_origin_remote_readback.json")
    if int(remote.get("schema_version") or 0)<3 or remote.get("task_id")!=TASK_ID or remote.get("continuation_key")!=CONTINUATION or [int(v) for v in remote.get("expected_rows") or []]!=EXPECTED_ROWS or str(remote.get("pre_publish_origin_head") or "").strip().lower()!=pre:raise ValueError("remote readback identity/history mismatch")
    if remote.get("pre_publish_head_is_ancestor_of_remote_head") is not True or remote.get("remote_history_binding_passed") is not True or remote.get("remote_history_and_commit_delta_binding_passed") is not True:raise ValueError("remote history binding failed")
    material=str(remote.get("first_full_blob_materialization_commit") or "").strip().lower(); history=str(remote.get("history_mode") or ""); delta=str(remote.get("materialization_commit_delta_gate_mode") or ""); candidate=remote.get("publisher_commit_candidate")
    if len(material)!=40 or remote.get("materialization_commit_is_ancestor_of_remote_head") is not True:raise ValueError("materialization commit invalid")
    if history=="FIRST_FULL_BLOB_MATERIALIZATION_COMMIT_FOUND":
        if remote.get("materialization_commit_changes_all_manifest_paths") is not True or str(candidate or "").strip().lower()!=material or delta!="ALL_SEVEN_MANIFEST_PATHS_CHANGED_IN_MATERIALIZATION_COMMIT":raise ValueError("materialization delta gate failed")
    elif history=="ALREADY_PRESENT_AT_PREPUBLISH_HEAD_NO_REPLAY_REQUIRED":
        if delta!="ALREADY_PRESENT_NO_REPLAY_DELTA_NOT_REQUIRED":raise ValueError("no-replay delta mode mismatch")
    else:raise ValueError(f"unknown remote history mode:{history}")
    if remote.get("all_remote_blobs_match") is not True or int(remote.get("file_count") or 0)!=7 or remote.get("remote_tracking_ref_freshly_updated") is not True or remote.get("numeric_publish_acceptance_for_12_rows") is not True:raise ValueError("remote blob/numeric acceptance failed")
    out=repo/"docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/033_batch133_coordinator_handoff/batch133_post_publish_remote_acceptance.json"; payload={"schema_version":5,"slot_id":"height_difference_3","task_id":TASK_ID,"continuation_key":CONTINUATION,"status":"REMOTE_HISTORY_DELTA_AND_CONTROL_PLANE_SEAL_ACCEPTED_12_ROWS","runtime_python_executable":str(Path(sys.executable).resolve()),"runtime_powershell_executable":ps,"runtime_git_executable":gx,"runtime_identity_match_passed":True,"fresh_host_heartbeat_passed":True,"runtime_preflight_freshness_and_head_binding_passed":True,"control_plane_receipt_validation_seal_passed":True,"coordinator_receipt_sha256":expected_receipt,"coordinator_receipt_validation_sha256":expected_validation,"coordinator_receipt_binding_key_sha256":h.get("coordinator_receipt_binding_key_sha256"),"coordinator_action_id":h.get("coordinator_action_id"),"coordinator_receipt_nonce":h.get("coordinator_receipt_nonce"),"pre_publish_origin_head":pre,"remote_head":remote.get("remote_head"),"history_mode":history,"first_full_blob_materialization_commit":material,"materialization_commit_delta_gate_mode":delta,"materialization_commit_changes_all_manifest_paths":remote.get("materialization_commit_changes_all_manifest_paths"),"publisher_commit_candidate":candidate,"remote_history_binding_passed":True,"remote_history_and_commit_delta_binding_passed":True,"expected_rows":EXPECTED_ROWS,"verified_count":12,"remote_file_count":7,"all_remote_blobs_match":True,"numeric_publish_acceptance_for_12_rows":True,"child_direct_push_performed":False,"numeric_values_changed":0,"new_task_created":False,"new_runner_created":False,"parallel_runner_used":False,"overall_product_final_ready":False,"final_ready":False,"fake_data":False,"remote_readback_stage":rr}; write(out,payload);print(json.dumps({"ok":True,"status":payload["status"],"pre_publish_origin_head":pre,"materialization_commit":material,"receipt_sha256":expected_receipt,"validation_sha256":expected_validation,"output":str(out)}));return 0
if __name__=="__main__":
    try:raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok":False,"error":f"{type(exc).__name__}: {exc}"}),file=sys.stderr);raise
