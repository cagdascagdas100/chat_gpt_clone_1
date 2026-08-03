#!/usr/bin/env python3
"""Validate whether NDA 2025/26 records contain an LLWR-specific GHG row."""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path
from typing import Any
MAX_RECORDS=30
BASE_IDS=("document_identity","llwr_logistics","nda_emissions_scope","nda_scope1_row","nda_scope2_scope3_rows")

def parse_args():
    p=argparse.ArgumentParser()
    p.add_argument("--contract",type=Path,required=True)
    p.add_argument("--prior",type=Path,required=True)
    p.add_argument("--snapshot",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    return p.parse_args()
def shab(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def norm(v:Any)->str:return " ".join(re.sub(r"[^a-z0-9]+"," ",str(v or "").lower()).split())

def main()->int:
    a=parse_args(); cb=a.contract.read_bytes(); pb=a.prior.read_bytes(); sb=a.snapshot.read_bytes()
    c,p,s=json.loads(cb),json.loads(pb),json.loads(sb)
    if c.get("schema_version")!=3 or c.get("state")!="READY": raise ValueError("contract is not schema-v3 READY")
    pre=c["precondition"]
    if shab(pb)!=pre["prior_output_sha256"]: raise ValueError("prior SHA mismatch")
    if p.get("task_id")!=pre["required_prior_task_id"] or p.get("state")!=pre["required_prior_state"] or p.get("next_unverified_step")!=pre["required_prior_next_unverified_step"]: raise ValueError("prior precondition mismatch")
    if shab(sb)!=c["source_evidence_manifest"]["snapshot_sha256"]: raise ValueError("snapshot SHA mismatch")
    records=s.get("records",[])
    if len(records)>MAX_RECORDS: raise ValueError("record limit exceeded")
    by={}
    for r in records:
        if shab(r["text"].encode("utf-8"))!=r["sha256"]: raise ValueError("record SHA mismatch")
        by[r["record_id"]]=r
    base_complete=all(x in by for x in BASE_IDS)
    doc=norm(by.get("document_identity",{}).get("text","")); llwr=norm(by.get("llwr_logistics",{}).get("text","")); scope=norm(by.get("nda_emissions_scope",{}).get("text","")); s1=norm(by.get("nda_scope1_row",{}).get("text","")); s23=norm(by.get("nda_scope2_scope3_rows",{}).get("text",""))
    document_ok="nuclear decommissioning authority annual report and accounts 2025 26" in doc
    llwr_context_ok=("low level waste repository llwr" in llwr and "around 200 nts trains" in llwr and "more than 175 000 tonnes" in llwr)
    group_scope_ok=("emissions from nda operations and staff" in scope and "offices under nda operational control" in scope)
    group_rows_ok=("total gross scope 1 direct ghg emissions 84 5 2 73" in s1 and "total gross scope 2 energy indirect ghg emissions 92 117 125 129" in s23 and "total gross scope 3 ghg emissions 214 466 428 584" in s23)
    site_record=by.get("llwr_site_ghg_row")
    site_text=norm(site_record.get("text","")) if site_record else ""
    site_ok=("low level waste repository llwr" in site_text and "total gross scope 1 direct ghg emissions" in site_text and "73 tco2e" in site_text and "2025 26" in site_text)
    matches=[]
    if base_complete and document_ok and llwr_context_ok and group_scope_ok and group_rows_ok and site_ok:
        matches=[{"row_id":"LLWR_SCOPE1_GHG_2025_26","metric_type":"site_specific_scope1_ghg_emissions","value_source":"73","unit_source":"tCO2e","period_source":"2025/26","source_record":site_record}]
    state="EXACT_SITE_GHG_ROW_VERIFIED" if matches else "NO_DATA_CONTINUE"
    output={
      "schema_version":3,"architecture_version":3,"workstream_id":"AAYS_21_SLOT_SAFE_PARALLEL_V1","slot_id":"gas_emissions_3","task_id":c["task_id"],"continuation_key":c["continuation_key"],"state":state,"panel_status":"PUBLISHED","execution_mode":"SHA_LOCKED_OFFICIAL_PDF_TEXT_SNAPSHOT","first_unverified_step_completed":c["first_unverified_step"],
      "next_unverified_step":"VALIDATE_AND_PUBLISH_LLWR_2025_26_EXACT_SITE_GHG_ROW" if matches else "ADVANCE_TO_NEXT_UNVERIFIED_GAS_EMISSIONS_SOURCE_AFTER_NDA_2025_26_NO_SITE_GHG_DATA",
      "input":{"contract_path":str(a.contract),"contract_sha256":shab(cb),"prior_output_path":str(a.prior),"prior_output_sha256":shab(pb),"snapshot_path":str(a.snapshot),"snapshot_sha256":shab(sb),"source_page_url":s.get("source_page_url"),"source_pdf_url":s.get("source_pdf_url"),"capture_scope":s.get("capture_scope")},
      "counts":{"completed_count":1,"target_count":1,"records_scanned":len(records),"llwr_context_records":1 if llwr_context_ok else 0,"group_emissions_rows_reviewed":3 if group_rows_ok else 0,"site_specific_ghg_rows":len(matches),"matched_targets":1 if matches else 0,"matched_rows":len(matches),"produced_business_rows":len(matches),"produced_source_evidence_records":len(records)},"progress_percent":100.0,
      "targets":[{"target_id":c["runtime_targets"][0]["target_id"],"site_name":"Low Level Waste Repository","attempt_completed":True,"decision":state,"matched_rows":len(matches),"matches":matches}],
      "excluded_evidence":[{"reason":"NDA_GROUP_OR_OFFICE_SCOPE_NOT_EXPLICITLY_ATTRIBUTED_TO_LLWR","record_ids":["nda_emissions_scope","nda_scope1_row","nda_scope2_scope3_rows"],"values_preserved":["Scope 1: 84, 5, 2, 73 tCO2e","Scope 2: 92, 117, 125, 129 tCO2e","Scope 3: 214, 466, 428, 584 tCO2e"]}],
      "decision":{"official_report_identity_required":True,"llwr_operational_context_required":True,"explicit_site_to_ghg_link_required":True,"group_values_not_attributed_to_llwr":True,"llwr_logistics_not_converted_to_emissions":True,"screenshot_cache_miss_recorded":True,"units_preserved_without_conversion":True,"inferred_values":0,"fake_data":False}
    }
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(output,ensure_ascii=False,sort_keys=True,separators=(",",":")),encoding="utf-8"); return 0
if __name__=="__main__": raise SystemExit(main())
