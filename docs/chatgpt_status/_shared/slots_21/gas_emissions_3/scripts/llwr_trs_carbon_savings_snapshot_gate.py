#!/usr/bin/env python3
"""Validate SHA-locked official LLWR TRS-project carbon-savings records."""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path
from typing import Any

REQUIRED_IDS=("document_identity","llwr_project_context","rail_savings_quote","project_stats","site_identity")
MAX_RECORDS=20

def args_ns():
    p=argparse.ArgumentParser()
    p.add_argument("--contract",type=Path,required=True)
    p.add_argument("--prior",type=Path,required=True)
    p.add_argument("--snapshot",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    return p.parse_args()

def sha_bytes(data:bytes)->str: return hashlib.sha256(data).hexdigest()
def norm(s:Any)->str:
    return " ".join(re.sub(r"[^a-z0-9]+"," ",str(s or "").lower()).split())

def main()->int:
    a=args_ns()
    cb,pb,sb=a.contract.read_bytes(),a.prior.read_bytes(),a.snapshot.read_bytes()
    c,p,s=json.loads(cb),json.loads(pb),json.loads(sb)
    if c.get("schema_version")!=3 or c.get("state")!="READY": raise ValueError("contract is not schema-v3 READY")
    if sha_bytes(pb)!=c["precondition"]["prior_output_sha256"]: raise ValueError("prior SHA mismatch")
    if p.get("task_id")!=c["precondition"]["required_prior_task_id"]: raise ValueError("prior task mismatch")
    if p.get("state")!=c["precondition"]["required_prior_state"]: raise ValueError("prior state mismatch")
    if p.get("next_unverified_step")!=c["precondition"]["required_prior_next_unverified_step"]: raise ValueError("prior step mismatch")
    if sha_bytes(sb)!=c["source_evidence_manifest"]["snapshot_sha256"]: raise ValueError("snapshot SHA mismatch")
    recs=s.get("records",[])
    if len(recs)>MAX_RECORDS: raise ValueError("record limit exceeded")
    by_id={}
    for r in recs:
        if sha_bytes(r["text"].encode("utf-8"))!=r["sha256"]: raise ValueError("record SHA mismatch")
        by_id[r["record_id"]]=r
    records_complete=all(x in by_id for x in REQUIRED_IDS)
    title_ok="collaborative project safely disposing" in norm(s.get("title"))
    site_text=norm(by_id.get("site_identity",{}).get("text",""))
    context_text=norm(by_id.get("llwr_project_context",{}).get("text",""))
    stats_text=norm(by_id.get("project_stats",{}).get("text",""))
    quote_text=norm(by_id.get("rail_savings_quote",{}).get("text",""))
    site_ok="low level waste repository" in site_text and "cumbria" in site_text and "low level waste repository" in context_text
    disposal_ok="final disposal" in context_text and "vault 8" in context_text
    row1_ok=("830 tonnes of co2 avoided" in stats_text and "vault 8 versus vault 9" in stats_text)
    row2_ok=(("7502kg carbon emissions" in quote_text or "7502 kg carbon emissions" in quote_text) and "each rail shipment" in quote_text and "road" in quote_text)
    matches=[]
    if records_complete and title_ok and site_ok and disposal_ok and row1_ok and row2_ok:
        matches=[
          {"row_id":"LLWR_TRS_VAULT8_VAULT9_CO2_AVOIDED","metric_type":"avoided_carbon_emissions","value_source":"830","unit_source":"tonnes CO2","qualifier_source":"avoided","comparison_source":"disposing in Vault 8 versus Vault 9","source_record":by_id["project_stats"]},
          {"row_id":"LLWR_TRS_RAIL_ROAD_CARBON_SAVED_PER_SHIPMENT","metric_type":"saved_carbon_emissions_per_shipment","value_source":"7502","unit_source":"kg carbon emissions per rail shipment","qualifier_source":"saved","comparison_source":"rail compared to road","source_record":by_id["rail_savings_quote"]},
        ]
    state="EXACT_SITE_CARBON_SAVINGS_ROWS_VERIFIED" if len(matches)==2 else "NO_DATA_CONTINUE"
    out={
      "schema_version":3,"architecture_version":3,"workstream_id":"AAYS_21_SLOT_SAFE_PARALLEL_V1","slot_id":"gas_emissions_3",
      "task_id":c["task_id"],"continuation_key":c["continuation_key"],"state":state,"panel_status":"PUBLISHED",
      "execution_mode":"SHA_LOCKED_OFFICIAL_SOURCE_SNAPSHOT","first_unverified_step_completed":c["first_unverified_step"],
      "next_unverified_step":"VALIDATE_AND_PUBLISH_LLWR_TRS_EXACT_CARBON_SAVINGS_ROWS" if matches else "ADVANCE_TO_NEXT_UNVERIFIED_GAS_EMISSIONS_SOURCE_AFTER_LLWR_TRS_NO_DATA",
      "input":{"contract_path":str(a.contract),"contract_sha256":sha_bytes(cb),"prior_output_path":str(a.prior),"prior_output_sha256":sha_bytes(pb),"snapshot_path":str(a.snapshot),"snapshot_sha256":sha_bytes(sb),"source_url":s.get("source_url"),"capture_scope":s.get("capture_scope")},
      "counts":{"completed_count":1,"target_count":1,"records_scanned":len(recs),"matched_targets":1 if matches else 0,"matched_rows":len(matches),"produced_business_rows":len(matches),"produced_source_evidence_records":len(recs)},
      "progress_percent":100.0,
      "targets":[{"target_id":c["runtime_targets"][0]["target_id"],"site_name":c["runtime_targets"][0]["site_name"],"attempt_completed":True,"decision":state,"matched_rows":len(matches),"matches":matches}],
      "decision":{"exact_site_identity_required":True,"exact_avoided_or_saved_wording_required":True,"direct_emissions_not_claimed":True,"totals_not_multiplied_by_shipment_count":True,"units_preserved_without_conversion":True,"partial_candidates_discarded":0 if matches else int(row1_ok)+int(row2_ok),"inferred_values":0,"fake_data":False}
    }
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,ensure_ascii=False,sort_keys=True,separators=(",",":")),encoding="utf-8")
    return 0
if __name__=="__main__": raise SystemExit(main())
