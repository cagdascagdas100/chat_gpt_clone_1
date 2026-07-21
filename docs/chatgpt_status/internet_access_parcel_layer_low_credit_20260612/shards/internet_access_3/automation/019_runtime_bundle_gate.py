#!/usr/bin/env python3
"""Fail-closed validator for real internet_access_3 runner outputs; review-only."""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
SLOT="internet_access_3"; START=61523; END=92283; ROWS=30761; OFCOM=1741096; MEMBERS=121
STAT=("CURRENT_R2_POSTCODE_PROXY_READY_FOR_REVIEW","IDENTITY_CONFLICT_NO_DATA","POSTCODE_NOT_FOUND_IN_CURRENT_R2_NO_DATA","NO_VERIFIED_POSTCODE_NO_DATA")
PCTS=("sfbb_30mbps_available_pct","ufbb_100mbps_available_pct","ufbb_300mbps_available_pct","gigabit_available_pct","unable_30mbps_pct","unable_decent_fixed_or_fwa_pct")
H=re.compile(r"^[0-9a-f]{64}$"); C=re.compile(r"^[0-9a-f]{8}$"); M=re.compile(r"^202601_fixed_postcode_coverage_r2_([A-Za-z]+)\.csv$"); PC=re.compile(r"^[A-Z]{1,2}[0-9][0-9A-Z]?[0-9][A-Z]{2}$")
class GateError(RuntimeError): pass
def req(v,m):
    if not v: raise GateError(m)
def integer(v,n):
    req(not isinstance(v,bool),f"{n}: integer required")
    try:z=int(v)
    except Exception as e: raise GateError(f"{n}: integer required") from e
    req(isinstance(v,int) or str(z)==str(v),f"{n}: exact integer required"); return z
def digest(p):
    d=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""): d.update(b)
    return d.hexdigest()
def hashv(v,n):
    s=str(v or "").lower(); req(H.fullmatch(s) is not None,f"{n}: SHA256 invalid"); return s
def load(p,n):
    req(p.is_file() and p.stat().st_size>0,f"{n}: missing/empty")
    try:x=json.loads(p.read_text(encoding="utf-8"))
    except Exception as e: raise GateError(f"{n}: invalid JSON: {e}") from e
    req(isinstance(x,dict),f"{n}: object required"); return x
def truth(x,n):
    for k in ("fake_data","db_write","migration","production_deploy","final_ready"): req(x.get(k) is False,f"{n}.{k} must be false")
    req(integer(x.get("actual_business_data_rows_written"),n+".business")==0,n+": business write")
    req(integer(x.get("scores_written"),n+".scores")==0,n+": score write")
def slice_gate(x,start,end,rows):
    req(x.get("slot_id")==SLOT,"slice slot"); p=x.get("row_partition") or {}; req((integer(p.get("start"),"slice start"),integer(p.get("end"),"slice end"),integer(p.get("expected"),"slice expected"))==(start,end,rows),"slice partition")
    c=x.get("canonical") or {}; l=x.get("legacy_internet") or {}; req((integer(c.get("rows"),"canonical rows"),integer(c.get("unique_row_numbers"),"canonical unique rows"),integer(c.get("unique_parcel_ids"),"canonical unique parcels"))==(rows,rows,rows),"canonical count/uniqueness")
    lr=integer(l.get("rows"),"legacy rows"); req(0<=lr<=rows,"legacy rows")
    first=c.get("first_rows"); req(isinstance(first,list) and 1<=len(first)<=3,"first_rows")
    for n,r in enumerate(first): req(integer(r.get("row_no"),"first row")==start+n and r.get("parcel_id")==f"parcel_{start+n}","first row identity")
    req(x.get("output_semantics")=="BOUNDED_INPUT_SLICE_ONLY_NO_BUSINESS_VALUES","slice semantics"); truth(x,"slice")
    return {"c":hashv(c.get("output_sha256"),"canonical output"),"l":hashv(l.get("output_sha256"),"legacy output"),"first":first,"legacy_rows":lr}
def member_gate(v,members,rows):
    req(isinstance(v,list) and len(v)==members,"member count"); names=set(); areas=set(); total=ret=0
    for n,x in enumerate(v,1):
        req(isinstance(x,dict),f"member {n}"); name=str(x.get("file") or ""); q=M.fullmatch(name); req(q is not None,f"member {n} name"); area=str(x.get("postcode_area") or "").upper(); req(area==q.group(1).upper(),f"member {n} area"); req(name not in names and area not in areas,"duplicate member/area"); names.add(name); areas.add(area)
        z=integer(x.get("rows"),f"member {n} rows"); r=integer(x.get("retained_needed_rows",0),f"member {n} retained"); req(z>0 and 0<=r<=z,f"member {n} counts"); total+=z; ret+=r; hashv(x.get("sha256"),f"member {n}"); req(C.fullmatch(str(x.get("crc32") or "").lower()) is not None,f"member {n} CRC")
    req(total==rows,"member row total"); return {"members":len(names),"areas":len(areas),"rows":total,"retained":ret}
def manifest_gate(x,start,end,rows,ofcom,members):
    req(x.get("slot_id")==SLOT and integer(x.get("parcel_start"),"start")==start and integer(x.get("parcel_end"),"end")==end and integer(x.get("canonical_rows"),"rows")==rows,"manifest slot/partition")
    counts={STAT[0]:integer(x.get("current_r2_postcode_proxy_rows"),"proxy"),STAT[1]:integer(x.get("identity_conflict_rows"),"conflict"),STAT[2]:integer(x.get("postcode_not_found_in_current_r2_rows"),"not found"),STAT[3]:integer(x.get("no_verified_postcode_rows"),"no postcode")}; req(min(counts.values())>=0 and sum(counts.values())==rows,"four-state partition")
    nd=sum(counts[s] for s in STAT[1:]); req(integer(x.get("no_data_rows"),"no data")==nd,"no data")
    req(x.get("ofcom_source_mode")=="DIRECT_ZIP_STREAM_NO_CSV_EXTRACTION" and x.get("ofcom_csv_extracted_to_disk") is False,"direct ZIP/no extraction")
    req(x.get("postcode_uniqueness_strategy")=="AREA_PARTITIONED_EXACT_PER_MEMBER_SET","uniqueness strategy")
    label=x.get("memory_strategy"); req(label in ("AREA_PARTITIONED_EXACT_UNIQUENESS_PLUS_NEEDED_POSTCODE_ROWS_ONLY","GLOBAL_POSTCODE_UNIQUENESS_SET_PLUS_NEEDED_POSTCODE_ROWS_ONLY"),"memory label")
    req(integer(x.get("ofcom_postcodes_scanned"),"scanned")==ofcom and integer(x.get("ofcom_unique_postcodes"),"unique")==ofcom,"Ofcom rows/unique")
    req(integer(x.get("postcode_area_member_count"),"area members")==members and integer(x.get("zip_member_stream_sha256_count"),"member hashes")==members and x.get("zip_member_crc_verified_by_complete_stream_read") is True,"member hash/CRC")
    needed=integer(x.get("needed_postcodes"),"needed"); retained=integer(x.get("ofcom_postcodes_retained"),"retained"); missing=integer(x.get("needed_postcodes_not_found"),"missing"); req(needed==retained+missing and 0<=retained<=needed<=rows,"needed partition")
    src=member_gate(x.get("ofcom_source_files"),members,ofcom); req(src["retained"]==retained,"retained member sum"); truth(x,"manifest")
    return {"counts":counts,"no_data":nd,"needed":needed,"retained":retained,"sources":src,"zip":hashv(x.get("ofcom_zip_sha256"),"ZIP"),"c":hashv(x.get("canonical_source_sha256"),"canonical source"),"l":hashv(x.get("legacy_internet_source_sha256"),"legacy source"),"label":label}
def row_gate(path,m,start,rows):
    req(path.is_file() and path.stat().st_size>0,"candidate JSONL"); counts=Counter(); samples=[]; sampled=set(); n=0
    with path.open(encoding="utf-8") as f:
        for raw in f:
            req(raw.strip(),f"blank line {n+1}"); n+=1; req(n<=rows,"too many rows")
            try:r=json.loads(raw)
            except Exception as e: raise GateError(f"invalid row {n}: {e}") from e
            expected=start+n-1; req(isinstance(r,dict) and r.get("slot_id")==SLOT and integer(r.get("canonical_row_no"),"row_no")==expected and r.get("canonical_program_parcel_id")==f"parcel_{expected}",f"row {n} identity")
            s=r.get("status"); req(s in STAT,f"row {n} status"); counts[s]+=1; req(r.get("business_row_written") is False and r.get("internet_availability_quality_percent") is None and r.get("internet_quality_band") is None and r.get("calculation_version") is None,f"row {n} score/write")
            conf=float(r.get("internet_match_confidence",-1))
            if s==STAT[0]:
                req(conf==.9 and r.get("source_level")=="POSTCODE_PROXY",f"row {n} proxy confidence/source"); pc=str(r.get("postcode") or "").replace(" ","").upper(); req(PC.fullmatch(pc) is not None,f"row {n} postcode"); req(r.get("source_revision")=="r2" and r.get("source_snapshot_date")=="2026-01",f"row {n} source revision")
                for k in PCTS:
                    try:v=float(r.get(k))
                    except Exception as e: raise GateError(f"row {n} {k} numeric") from e
                    req(0<=v<=100,f"row {n} {k} range")
            else:
                req(conf==0 and r.get("source_level")=="NO_DATA",f"row {n} NO_DATA confidence/source")
                for k in PCTS:req(r.get(k) is None,f"row {n} NO_DATA {k}")
            if s not in sampled: sampled.add(s); samples.append(r)
            elif len(samples)<8 and n<=8:samples.append(r)
    req(n==rows,"row count"); actual={s:counts[s] for s in STAT}; req(actual==m["counts"],"JSONL/manifest counts"); return {"rows":n,"sha":digest(path),"samples":samples[:8]}
def validate(manifest_path,jsonl_path,slice_path,output,start=START,end=END,rows=ROWS,ofcom=OFCOM,members=MEMBERS):
    m=manifest_gate(load(manifest_path,"manifest"),start,end,rows,ofcom,members); s=slice_gate(load(slice_path,"slice"),start,end,rows); r=row_gate(jsonl_path,m,start,rows); req(m["c"]==s["c"] and m["l"]==s["l"],"slice hash binding")
    out={"schema_version":1,"slot_id":SLOT,"state":"PASS_VALIDATED_RUNTIME_BUNDLE_REVIEW_ONLY","validated_at":datetime.now(timezone.utc).isoformat(),"row_partition":{"start":start,"end":end,"rows":rows},"gates":[{"gate_no":1,"name":"INPUT_FILES_PRESENT_NONEMPTY","state":"PASS"},{"gate_no":2,"name":"EXACT_SLOT_IDENTITY_SEQUENCE","state":"PASS"},{"gate_no":3,"name":"FOUR_STATE_PARTITION","state":"PASS"},{"gate_no":4,"name":"DIRECT_ZIP_OFFICIAL_SOURCE","state":"PASS"},{"gate_no":5,"name":"AREA_PARTITIONED_EXACT_UNIQUENESS","state":"PASS"},{"gate_no":6,"name":"HASH_AND_CRC_EVIDENCE","state":"PASS"},{"gate_no":7,"name":"BOUND_SLICE_HASH_BINDING","state":"PASS"},{"gate_no":8,"name":"NO_SCORE_NO_WRITE","state":"PASS"}],"counts":{"canonical_rows":rows,"current_r2_postcode_proxy_rows":m["counts"][STAT[0]],"identity_conflict_rows":m["counts"][STAT[1]],"postcode_not_found_in_current_r2_rows":m["counts"][STAT[2]],"no_verified_postcode_rows":m["counts"][STAT[3]],"no_data_rows":m["no_data"],"needed_postcodes":m["needed"],"ofcom_postcodes_retained":m["retained"],"ofcom_postcodes_scanned":ofcom,"postcode_area_members":members},"hashes":{"candidate_manifest_sha256":digest(manifest_path),"candidates_jsonl_sha256":r["sha"],"slice_manifest_sha256":digest(slice_path),"ofcom_zip_sha256":m["zip"],"canonical_slice_sha256":s["c"],"legacy_slice_sha256":s["l"]},"memory_strategy":{"effective":"AREA_PARTITIONED_EXACT_UNIQUENESS_PLUS_NEEDED_POSTCODE_ROWS_ONLY","manifest_label":m["label"],"legacy_label_normalized":m["label"].startswith("GLOBAL_")},"samples":r["samples"],"sample_truth_boundary":"REAL_RUNTIME_ROWS_ONLY; REVIEW_ONLY; NOT_BUSINESS_DATA; NO_PARCEL_SCORE","actual_business_data_rows_written":0,"scores_written":0,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False,"final_ready":False}
    output.parent.mkdir(parents=True,exist_ok=True); output.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf-8"); return out
def validate_bundle(manifest_path,jsonl_path,slice_path,output,start=START,end=END,rows=ROWS,ofcom_rows=OFCOM,members=MEMBERS):
    return validate(manifest_path,jsonl_path,slice_path,output,start=start,end=end,rows=rows,ofcom=ofcom_rows,members=members)
def main():
    p=argparse.ArgumentParser(); p.add_argument("--candidate-manifest",required=True,type=Path); p.add_argument("--candidates-jsonl",required=True,type=Path); p.add_argument("--slice-manifest",required=True,type=Path); p.add_argument("--output",required=True,type=Path); a=p.parse_args(); x=validate(a.candidate_manifest,a.candidates_jsonl,a.slice_manifest,a.output); print(json.dumps({"state":x["state"],"counts":x["counts"],"hashes":x["hashes"]},sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
