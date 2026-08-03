#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, tempfile
from collections import Counter
from pathlib import PurePosixPath, Path

MAX_RECORDS=128
MAX_SUFFIXES=8
MAX_CHAIN_LEN=128

def cbytes(x): return (json.dumps(x,sort_keys=True,separators=(",",":"))+"\n").encode()
def sha(x): return hashlib.sha256(x).hexdigest()

def atomic(path,obj):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=p.parent,delete=False) as f:
        f.write(cbytes(obj)); t=f.name
    os.replace(t,p)

def norm(v):
    if not isinstance(v,list) or not v or len(v)>MAX_SUFFIXES: return None
    out=[]
    for s in v:
        if not isinstance(s,str): return None
        s=s.strip()
        if not s.startswith(".") or s in {".",".."} or "/" in s or "\\" in s: return None
        out.append(s)
    return tuple(out) if len("".join(out))<=MAX_CHAIN_LEN else None

def name(rec):
    if not isinstance(rec,dict): return None,None
    v=rec.get("basename")
    if isinstance(v,str) and v.strip():
        n=PurePosixPath(v.strip().replace("\\","/")).name
        if n not in {"",".",".."}: return n,"explicit_basename"
    parts=rec.get("path_parts")
    if isinstance(parts,list) and parts and all(isinstance(x,str) for x in parts):
        n=PurePosixPath(parts[-1].replace("\\","/")).name
        if n not in {"",".",".."}: return n,"path_parts"
    for k in ("member_name","normalized_path","path"):
        v=rec.get(k)
        if isinstance(v,str) and v.strip():
            n=PurePosixPath(v.replace("\\","/")).name
            if n not in {"",".",".."}: return n,k
    return None,None

def chain(rec):
    if not isinstance(rec,dict): return None,None
    for k in ("suffix_chain","suffixes"):
        v=norm(rec.get(k))
        if v: return v,k
    n,p=name(rec)
    v=norm(list(PurePosixPath(n).suffixes)) if n else None
    return (v,f"derived_from_{p}") if v else (None,None)

def assess(prior,source,at):
    if prior.get("slot_id")!="gas_emissions_2" or prior.get("wave")!=373: raise ValueError("PRIOR_WAVE373_SLOT_MISMATCH")
    if source.get("slot_id")!="gas_emissions_2" or source.get("wave")!=368: raise ValueError("SOURCE_WAVE368_SLOT_MISMATCH")
    rows=(source.get("tar_member_path_prefix_records") or [])[:MAX_RECORDS]
    found=[chain(r) for r in rows]; found=[x for x in found if x[0]]
    counts=Counter(x[0] for x in found); prov=Counter(x[1] for x in found)
    freq=[{"suffix_chain":"".join(k),"suffixes":list(k),"record_count":v}
          for k,v in sorted(counts.items(),key=lambda x:(-x[1],"".join(x[0])))]
    blockers=[]
    if not rows: blockers.append("WAVE368_TAR_MEMBER_PATH_PREFIX_COUNT_ZERO")
    if not found: blockers.append("TAR_MEMBER_SUFFIX_CHAINS_NOT_AVAILABLE")
    blockers += ["TAR_MEMBER_SUFFIX_CHAIN_FREQUENCY_ALONE_DOES_NOT_PROVE_FILE_CONTENT",
                 "TAR_MEMBER_SUFFIX_CHAIN_FREQUENCY_ALONE_DOES_NOT_PROVE_OVERTURE_BUILDING_FEATURES",
                 "THREE_OVERTURE_BUILDING_FEATURES_NOT_ACQUIRED","THREE_EXACT_UPRNS_NOT_ACQUIRED",
                 "EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"]
    ps,ss=sha(cbytes(prior)),sha(cbytes(source))
    excerpt=(f"prior_wave373_sha256={ps};source_wave368_sha256={ss};"
             f"source_path_prefix_records={len(rows)};valid_suffix_chain_records={len(found)};"
             f"unique_suffix_chains={len(freq)};business_rows=0;parcel_rows=0")
    ev={"source_url":"repo://england_map_web/data/aays_21_slots/gas_emissions_2/wave368_ghcr_bottle_layer_tar_member_path_prefix_gate_20260803.json",
        "accessed_at":at,"content_sha256":sha(excerpt.encode()),"hash_scope":"normalized_runtime_receipt_utf8",
        "record_scope":"Only explicit suffix-chain values or PurePath.suffixes values from bounded Wave368 metadata were counted; no member body was read.",
        "relevant_record_ids_or_excerpt":excerpt,
        "supports_fields":["suffix_chain_frequencies","valid_suffix_chain_record_count","unique_suffix_chain_count","suffix_chain_provenance_counts","no_member_body_read"],
        "license_or_terms_url":"https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.suffixes"}
    return {"schema_version":1,"architecture_version":3,"workstream_id":"AAYS_21_SLOT_SAFE_PARALLEL_V1",
            "slot_id":"gas_emissions_2","wave":374,"accessed_at":at,"prior_wave":373,
            "prior_state":prior.get("state"),"prior_output_sha256":ps,"source_wave":368,"source_output_sha256":ss,
            "assessments":(source.get("assessments") or [])[:3],"source_tar_member_path_prefix_count":len(rows),
            "valid_suffix_chain_record_count":len(found),"unique_suffix_chain_count":len(freq),
            "suffix_chain_frequencies":freq,
            "suffix_chain_provenance_counts":[{"provenance":k,"record_count":v} for k,v in sorted(prov.items())],
            "member_body_read":False,"archive_extraction_performed":False,"business_rows_produced":0,
            "parcel_rows_bound":0,"completed_count":0,"target_count":30761,"previous_percent":0.0,
            "current_percent":0.0,"percent_increase":0.0,
            "decision":"GHCR_BOTTLE_LAYER_TAR_MEMBER_SUFFIX_CHAIN_FREQUENCIES_ASSESSED",
            "state":"NO_DATA_CONTINUE","blocker":";".join(blockers),
            "first_unverified_step":"ASSESS_GHCR_BOTTLE_LAYER_TAR_MEMBER_SUFFIX_TOKEN_FREQUENCIES_OR_NO_DATA_CONTINUE",
            "source_evidence_manifest":source.get("source_evidence_manifest",[]),"runtime_source_evidence":[ev],
            "fake_data":False,"final_ready":False}

def self_test():
    p={"slot_id":"gas_emissions_2","wave":373,"state":"NO_DATA_CONTINUE"}
    s={"slot_id":"gas_emissions_2","wave":368,"tar_member_path_prefix_records":[
       {"suffix_chain":[".tar",".gz"]},{"suffixes":[".json"]},{"basename":"data.json"},
       {"path_parts":["x","archive.tar.gz"]},{"member_name":"x/buildings.parquet"},
       {"normalized_path":"x/archive.tar.gz"},{"path":r"x\config.yaml"},{"basename":"README"}]}
    o=assess(p,s,"2026-08-03T20:40:00Z")
    assert o["valid_suffix_chain_record_count"]==7 and o["unique_suffix_chain_count"]==4
    assert o["business_rows_produced"]==o["parcel_rows_bound"]==0
    e=dict(s); e["tar_member_path_prefix_records"]=[]
    z=assess(p,e,"2026-08-03T20:40:00Z")
    assert z["suffix_chain_frequencies"]==[] and "WAVE368_TAR_MEMBER_PATH_PREFIX_COUNT_ZERO" in z["blocker"]
    print("SELF_TEST_PASS")

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--prior"); a.add_argument("--source"); a.add_argument("--output"); a.add_argument("--accessed-at"); a.add_argument("--self-test",action="store_true")
    x=a.parse_args()
    if x.self_test: self_test(); return
    if not all((x.prior,x.source,x.output,x.accessed_at)): a.error("required arguments missing")
    with open(x.prior,encoding="utf-8") as f: p=json.load(f)
    with open(x.source,encoding="utf-8") as f: s=json.load(f)
    atomic(x.output,assess(p,s,x.accessed_at))
if __name__=="__main__": main()
