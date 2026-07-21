#!/usr/bin/env python3
"""Fail-closed reproducibility comparison for two validated internet_access_3 runtime receipts.

Review-only: never claims a slot, mutates a queue, writes a heartbeat,
creates a parcel score, or writes business data.
"""
from __future__ import annotations
import argparse
import importlib.util
import json
import os
import tempfile
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID="internet_access_3"
ROW_START=61523
ROW_END=92283
EXPECTED_ROWS=30761
SOURCE_HASHES=("ofcom_zip_sha256","canonical_slice_sha256","legacy_slice_sha256")
OUTPUT_HASHES=("candidates_jsonl_sha256",)
WRAPPER_HASHES=("candidate_manifest_sha256","slice_manifest_sha256")
PASS_EXACT="PASS_EXACT_RUNTIME_REPRODUCIBILITY"
REVIEW_METADATA="REVIEW_METADATA_ONLY_DRIFT"
BLOCK_SOURCE="BLOCKED_SOURCE_INPUT_DRIFT"
BLOCK_OUTPUT="BLOCKED_NONDETERMINISTIC_RUNTIME_OUTPUT"
BLOCK_RECEIPT="BLOCKED_RECEIPT_INCONSISTENCY"

class GateError(RuntimeError):
    pass

def load_json(path:Path,name:str)->dict[str,Any]:
    if not path.is_file() or path.stat().st_size==0:
        raise GateError(f"{name}: missing or empty: {path}")
    try:
        value=json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise GateError(f"{name}: invalid JSON: {exc}") from exc
    if not isinstance(value,dict):
        raise GateError(f"{name}: object required")
    return value

def load_importer(path:Path):
    if not path.is_file():
        raise GateError(f"runtime importer missing: {path}")
    spec=importlib.util.spec_from_file_location("ia3_runtime_importer",path)
    if spec is None or spec.loader is None:
        raise GateError("runtime importer could not be loaded")
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def canonical(value:Any)->str:
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"))

def gate_fingerprint(validated:dict[str,Any])->list[dict[str,Any]]:
    return [{"gate_no":g.get("gate_no"),"name":g.get("name"),"state":g.get("state")} for g in validated["gates"]]

def compare_values(baseline_value:dict[str,Any],candidate_value:dict[str,Any],*,importer_module:Any,start:int=ROW_START,end:int=ROW_END,rows:int=EXPECTED_ROWS)->dict[str,Any]:
    try:
        baseline=importer_module.validate_runtime_gate(baseline_value,start=start,end=end,rows=rows)
        candidate=importer_module.validate_runtime_gate(candidate_value,start=start,end=end,rows=rows)
    except Exception as exc:
        raise GateError(str(exc)) from exc
    bh=baseline["hashes"]; ch=candidate["hashes"]; comparisons=[]
    def add(number:int,name:str,keys:tuple[str,...],metadata:bool=False)->bool:
        left={k:bh[k] for k in keys}; right={k:ch[k] for k in keys}; equal=left==right
        comparisons.append({"gate_no":number,"name":name,"state":"PASS" if equal else ("REVIEW" if metadata else "BLOCKED"),"baseline":left,"candidate":right})
        return equal
    source_equal=add(1,"SOURCE_INPUT_HASHES",SOURCE_HASHES)
    output_equal=add(2,"CANDIDATE_JSONL_HASH",OUTPUT_HASHES)
    wrapper_equal=add(3,"MANIFEST_WRAPPER_HASHES",WRAPPER_HASHES,True)
    counts_equal=baseline["counts"]==candidate["counts"]
    comparisons.append({"gate_no":4,"name":"FOUR_STATE_AND_AUXILIARY_COUNTS","state":"PASS" if counts_equal else "BLOCKED","baseline":baseline["counts"],"candidate":candidate["counts"]})
    bs=canonical(baseline["samples"]); cs=canonical(candidate["samples"]); samples_equal=bs==cs
    comparisons.append({"gate_no":5,"name":"REAL_SAMPLE_RECEIPT","state":"PASS" if samples_equal else "BLOCKED","baseline_sha256":hashlib.sha256(bs.encode()).hexdigest(),"candidate_sha256":hashlib.sha256(cs.encode()).hexdigest()})
    bg=gate_fingerprint(baseline); cg=gate_fingerprint(candidate); gates_equal=bg==cg
    comparisons.append({"gate_no":6,"name":"VALIDATION_GATE_RECEIPT","state":"PASS" if gates_equal else "BLOCKED","baseline":bg,"candidate":cg})
    if not source_equal:
        status=BLOCK_SOURCE; summary="Canonical, legacy or Ofcom ZIP input hash changed; automatic reproducibility acceptance is forbidden."
    elif not output_equal or not counts_equal:
        status=BLOCK_OUTPUT; summary="Inputs are identical but candidate JSONL or count partition changed; nondeterministic output is blocked."
    elif not samples_equal or not gates_equal:
        status=BLOCK_RECEIPT; summary="Data hashes are stable but sample/gate receipt changed; receipt inconsistency is blocked."
    elif not wrapper_equal:
        status=REVIEW_METADATA; summary="Semantic inputs and results are identical but wrapper manifest hashes changed; manual metadata review is required."
    else:
        status=PASS_EXACT; summary="Two validated runtime receipts are equivalent for required source, output, count, sample and gate fields."
    exact=status==PASS_EXACT
    return {
      "schema_version":1,"slot_id":SLOT_ID,"status":status,"summary":summary,
      "compared_at":datetime.now(timezone.utc).isoformat(),
      "row_partition":{"start":start,"end":end,"rows":rows},
      "exact_reproducibility_pass":exact,"manual_review_required":not exact,"automatic_acceptance":False,
      "comparisons":comparisons,
      "baseline":{"counts":baseline["counts"],"hashes":bh},
      "candidate":{"counts":candidate["counts"],"hashes":ch},
      "actual_business_data_rows_written":0,"scores_written":0,"fake_data":False,
      "db_write":False,"migration":False,"production_deploy":False,"final_ready":False
    }

def atomic_write_json(path:Path,value:dict[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=path.name+".",suffix=".tmp",dir=str(path.parent))
    try:
        with os.fdopen(fd,"w",encoding="utf-8",newline="\n") as handle:
            json.dump(value,handle,ensure_ascii=False,indent=2); handle.write("\n"); handle.flush(); os.fsync(handle.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--baseline",required=True,type=Path)
    p.add_argument("--candidate",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    p.add_argument("--runtime-importer",type=Path,default=Path(__file__).with_name("023_import_validated_runtime_bundle_to_web.py"))
    p.add_argument("--start",type=int,default=ROW_START); p.add_argument("--end",type=int,default=ROW_END); p.add_argument("--rows",type=int,default=EXPECTED_ROWS)
    a=p.parse_args()
    result=compare_values(load_json(a.baseline,"baseline"),load_json(a.candidate,"candidate"),importer_module=load_importer(a.runtime_importer),start=a.start,end=a.end,rows=a.rows)
    atomic_write_json(a.output,result)
    print(json.dumps({"status":result["status"],"exact":result["exact_reproducibility_pass"]},sort_keys=True))
    return 0 if result["exact_reproducibility_pass"] else 2

if __name__=="__main__":
    raise SystemExit(main())
