#!/usr/bin/env python3
"""Same-task pre-publish wrapper that seals coordinator receipt consumption around 039.

The wrapper never mutates queue state or pushes. It snapshots the coordinator receipt
before 039, lets 039 perform its normal 046 validation + strict/local acceptance +
manifest handoff, then requires the receipt to be byte-identical and binds the final
046 validation file plus 039 handoff with SHA-256. A failed seal returns nonzero so the
serial publisher cannot be accepted from this entrypoint.
"""
from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path
from typing import Any
TASK_ID="height_difference_3-canonical-api-measurement-20260721-01"
CONTINUATION="6e8e709b6bad7b9807055e2b8b5de98cd4945ee3dee57825e72ba1b824eadd0f"
RUN039="docs/chatgpt_status/topography/shards/height_difference_3/automation/039_runner_entry_batch133_prepare_publish_handoff.py"
RECEIPT="docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/047_batch141_coordinator_rewire_receipt/coordinator_runtime_rewire_receipt.json"
VALIDATION="docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/047_batch141_coordinator_rewire_receipt/coordinator_runtime_rewire_receipt_validation.json"
HANDOFF="docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/033_batch133_coordinator_handoff/batch133_prepare_publish_handoff.json"
SEAL="docs/chatgpt_status/topography/shards/height_difference_3/runner_outputs/050_batch143_receipt_consumption_seal/prepublish_receipt_consumption_seal.json"
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
def main()->int:
    repo=root(Path(__file__).resolve())
    receipt=repo/RECEIPT; validation=repo/VALIDATION; handoff=repo/HANDOFF; run039=repo/RUN039
    if not receipt.is_file(): raise FileNotFoundError(receipt)
    if not run039.is_file(): raise FileNotFoundError(run039)
    receipt_sha_before=sha(receipt)
    p=subprocess.run([sys.executable,str(run039)],cwd=repo,text=True,capture_output=True,check=False)
    if p.returncode!=0: raise RuntimeError(f"039 failed:{p.stderr[-2400:]}")
    for path in (receipt,validation,handoff):
        if not path.is_file(): raise FileNotFoundError(path)
    receipt_sha_after=sha(receipt); validation_sha=sha(validation); handoff_sha=sha(handoff)
    if receipt_sha_before!=receipt_sha_after: raise RuntimeError("COORDINATOR_RECEIPT_CHANGED_DURING_039")
    val=load(validation); ho=load(handoff)
    if val.get("status")!="COORDINATOR_REWIRE_RECEIPT_VALIDATED": raise ValueError("046 validation status mismatch")
    if val.get("task_id")!=TASK_ID or val.get("continuation_key")!=CONTINUATION: raise ValueError("046 validation identity mismatch")
    if val.get("receipt_sha256")!=receipt_sha_after: raise ValueError("046 receipt SHA-256 does not match current receipt")
    if ho.get("task_id")!=TASK_ID or ho.get("continuation_key")!=CONTINUATION: raise ValueError("039 handoff identity mismatch")
    if ho.get("status")!="PUBLISH_PENDING_SERIAL_PUBLISHER_REQUIRED": raise ValueError("039 handoff status mismatch")
    if ho.get("coordinator_receipt_binding_key_sha256")!=val.get("binding_key_sha256"): raise ValueError("handoff/validation binding key mismatch")
    payload={"schema_version":1,"slot_id":"height_difference_3","task_id":TASK_ID,"continuation_key":CONTINUATION,"status":"PREPUBLISH_RECEIPT_CONSUMPTION_SEALED","receipt_sha256_before_039":receipt_sha_before,"receipt_sha256_after_039":receipt_sha_after,"receipt_byte_identity_preserved":True,"validation_sha256_after_039":validation_sha,"handoff_sha256_after_039":handoff_sha,"coordinator_action_id":val.get("coordinator_action_id"),"receipt_nonce":val.get("receipt_nonce"),"binding_key_sha256":val.get("binding_key_sha256"),"runtime_override_applied":val.get("runtime_override_applied") is True,"matching_queue_record_count":val.get("matching_queue_record_count"),"039_exit_code":p.returncode,"serial_publisher_required":True,"child_direct_push_performed":False,"new_task_created":False,"new_runner_created":False,"parallel_runner_used":False,"final_ready":False,"fake_data":False,"039_stdout_tail":p.stdout[-4000:]}
    out=repo/SEAL; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"ok":True,"status":payload["status"],"receipt_sha256":receipt_sha_after,"validation_sha256":validation_sha,"handoff_sha256":handoff_sha,"output":str(out)})); return 0
if __name__=="__main__":
    try: raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok":False,"error":f"{type(exc).__name__}: {exc}"}),file=sys.stderr); raise
