#!/usr/bin/env python3
"""Same-task post-publish wrapper that preserves the Batch143 receipt-consumption seal.

Before and after 040 remote readback, this wrapper requires the coordinator receipt,
046 validation and 039 handoff bytes to remain exactly the SHA-256 values sealed by
048. It does not publish or mutate queue state; it only fail-closes numeric acceptance
when the control-plane evidence changed after strict runtime.
"""
from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path
from typing import Any
TASK_ID="height_difference_3-canonical-api-measurement-20260721-01"
CONTINUATION="6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f"
RUN040="docs/chatgpt_status/topography/shards/height_difference_3/automation/040_runner_entry_batch133_post_publish_remote_readback.py"
RECEIPT="docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/047_batch141_coordinator_rewire_receipt/coordinator_runtime_rewire_receipt.json"
VALIDATION="docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/047_batch141_coordinator_rewire_receipt/coordinator_runtime_rewire_receipt_validation.json"
HANDOFF="docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/033_batch133_coordinator_handoff/batch133_prepare_publish_handoff.json"
PRESEAL="docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/050_batch143_receipt_consumption_seal/prepublish_receipt_consumption_seal.json"
ACCEPTANCE="docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/033_batch133_coordinator_handoff/batch133_post_publish_remote_acceptance.json"
POSTSEAL="docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/050_batch143_receipt_consumption_seal/postpublish_receipt_consumption_seal.json"
def root(start:Path)->Path:
    for c in (start,*start.parents):
        if (c/"england_map_web").is_dir() and (c/"docs/chatgpt_status").is_dir(): return c
    raise RuntimeError("REPO_ROOT_NOT_FOUND")
def load(path:Path)->dict[str,Any]:
    v=json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(v,dict): raise ValueError(f"expected JSON object:{path}")
    return v
def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()
def current_hashes(repo:Path)->dict[str,str]:
    paths={"receipt":repo/RECEIPT,"validation":repo/VALIDATION,"handoff":repo/HANDOFF}
    for p in paths.values():
        if not p.is_file(): raise FileNotFoundError(p)
    return {k:sha(v) for k,v in paths.items()}
def main()->int:
    repo=root(Path(__file__).resolve()); pre=repo/PRESEAL; run040=repo/RUN040
    if not pre.is_file(): raise FileNotFoundError(pre)
    if not run040.is_file(): raise FileNotFoundError(run040)
    seal=load(pre)
    if seal.get("status")!="PREPUBLISH_RECEIPT_CONSUMPTION_SEALED": raise ValueError("prepublish receipt seal status mismatch")
    if seal.get("task_id")!=TASK_ID or seal.get("continuation_key")!=CONTINUATION: raise ValueError("prepublish receipt seal identity mismatch")
    expected={"receipt":seal.get("receipt_sha256_after_039"),"validation":seal.get("validation_sha256_after_039"),"handoff":seal.get("handoff_sha256_after_039")}
    before=current_hashes(repo)
    if before!=expected: raise RuntimeError(f"CONTROL_PLANE_SEAL_CHANGED_BEFORE_040:{before}:{expected}")
    p=subprocess.run([sys.executable,str(run040)],cwd=repo,text=True,capture_output=True,check=False)
    if p.returncode!=0: raise RuntimeError(f"040 failed:{p.stderr[-2400:]}")
    after=current_hashes(repo)
    if after!=expected: raise RuntimeError(f"CONTROL_PLANE_SEAL_CHANGED_DURING_040:{after}:{expected}")
    acceptance=repo/ACCEPTANCE
    if not acceptance.is_file(): raise FileNotFoundError(acceptance)
    acc=load(acceptance)
    if acc.get("task_id")!=TASK_ID or acc.get("continuation_key")!=CONTINUATION: raise ValueError("040 acceptance identity mismatch")
    if acc.get("status")!="REMOTE_HISTORY_DELTA_BOUND_READBACK_ACCEPTED_12_ROWS": raise ValueError("040 acceptance status mismatch")
    if acc.get("numeric_publish_acceptance_for_12_rows") is not True: raise ValueError("040 numeric acceptance missing")
    acceptance_sha=sha(acceptance)
    payload={"schema_version":1,"slot_id":"height_difference_3","task_id":TASK_ID,"continuation_key":CONTINUATION,"status":"POSTPUBLISH_RECEIPT_CONSUMPTION_SEALED","receipt_sha256":expected["receipt"],"validation_sha256":expected["validation"],"handoff_sha256":expected["handoff"],"control_plane_hashes_before_040":before,"control_plane_hashes_after_040":after,"control_plane_byte_identity_preserved":True,"coordinator_action_id":seal.get("coordinator_action_id"),"receipt_nonce":seal.get("receipt_nonce"),"binding_key_sha256":seal.get("binding_key_sha256"),"post_publish_acceptance_sha256":acceptance_sha,"040_exit_code":p.returncode,"numeric_publish_acceptance_for_12_rows":True,"child_direct_push_performed":False,"new_task_created":False,"new_runner_created":False,"parallel_runner_used":False,"overall_product_final_ready":False,"final_ready":False,"fake_data":False,"040_stdout_tail":p.stdout[-4000:]}
    out=repo/POSTSEAL; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"ok":True,"status":payload["status"],"acceptance_sha256":acceptance_sha,"output":str(out)})); return 0
if __name__=="__main__":
    try: raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok":False,"error":f"{type(exc).__name__}: {exc}"}),file=sys.stderr); raise
