#!/usr/bin/env python3
"""Validate SHA-locked official LLWR ESC 2026 air-release records."""
from __future__ import annotations
import argparse, hashlib, json, re, unicodedata
from pathlib import Path
from typing import Any

def norm(v: Any) -> str:
    s = unicodedata.normalize("NFKD", str(v or "")).encode("ascii","ignore").decode("ascii")
    return " ".join(re.sub(r"[^a-z0-9.+-]+"," ",s.lower()).split())

def args() -> argparse.Namespace:
    p=argparse.ArgumentParser()
    p.add_argument("--contract",required=True,type=Path)
    p.add_argument("--prior",required=True,type=Path)
    p.add_argument("--snapshot",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    return p.parse_args()

def main() -> int:
    a=args()
    cb,pb,sb=a.contract.read_bytes(),a.prior.read_bytes(),a.snapshot.read_bytes()
    c,p,s=json.loads(cb),json.loads(pb),json.loads(sb)
    if c.get("schema_version")!=3 or c.get("state")!="READY" or c.get("slot_id")!="gas_emissions_3":
        raise ValueError("contract identity/state mismatch")
    pre=c["precondition"]
    if hashlib.sha256(pb).hexdigest()!=pre["prior_output_sha256"]: raise ValueError("prior sha mismatch")
    if p.get("task_id")!=pre["required_prior_task_id"] or p.get("state")!=pre["required_prior_state"]:
        raise ValueError("prior identity/state mismatch")
    if p.get("next_unverified_step")!=pre["required_prior_next_unverified_step"]:
        raise ValueError("prior next step mismatch")
    m=c["source_evidence_manifest"]
    if hashlib.sha256(sb).hexdigest()!=m["snapshot_sha256"]: raise ValueError("snapshot sha mismatch")
    if s.get("source_url")!=m["source_url"] or s.get("accessed_at")!=m["accessed_at"]:
        raise ValueError("snapshot source metadata mismatch")
    recs=s.get("records")
    if not isinstance(recs,list) or len(recs)>c["snapshot_policy"]["maximum_records"]:
        raise ValueError("snapshot record limit/schema")
    for r in recs:
        if hashlib.sha256(str(r.get("text","")).encode("utf-8")).hexdigest()!=r.get("sha256"):
            raise ValueError("record sha mismatch")
    if norm(s.get("site_identity")) not in ("low level waste repository llwr","low level waste repository"):
        raise ValueError("site identity mismatch")
    if norm(s.get("section_identity"))!="4.1 discharges to air":
        raise ValueError("section identity mismatch")

    rows=[]
    for r in recs:
        rid=r.get("record_id")
        txt=str(r.get("text",""))
        n=norm(txt)
        if rid=="tritium_peak_flux" and "peak annual total flux of tritium calculated is 1.7 tbq" in n and "2047" in n:
            rows.append({"row_id":"LLWR_TRITIUM_PEAK_FLUX_2047","substance":"tritium-bearing water vapour","metric":"modelled_peak_annual_total_flux","value_source":"1.7","unit_source":"TBq","year_source":"2047","source_record":r})
        if rid=="radon_release_rate" and "rate of release is around 3 tbq y-1" in n:
            rows.append({"row_id":"LLWR_RADON_TYPICAL_RELEASE_RATE","substance":"Rn-222 radon","metric":"modelled_release_rate_majority_of_period","value_source":"3","qualifier_source":"around","unit_source":"TBq y-1","year_source":None,"source_record":r})
        if rid=="radon_release_rate" and "peak release of 3.4 tbq y-1" in n and "2047" in n:
            rows.append({"row_id":"LLWR_RADON_PEAK_RELEASE_2047","substance":"Rn-222 radon","metric":"modelled_peak_release_rate","value_source":"3.4","unit_source":"TBq y-1","year_source":"2047","source_record":r})
    complete_rows = rows if len(rows) == 3 else []
    state="EXACT_SITE_GAS_RELEASE_ROWS_VERIFIED" if len(rows)==3 else "NO_DATA_CONTINUE"
    out={
      "schema_version":3,"architecture_version":3,"workstream_id":"AAYS_21_SLOT_SAFE_PARALLEL_V1",
      "slot_id":"gas_emissions_3","task_id":c["task_id"],"continuation_key":c["continuation_key"],
      "state":state,"panel_status":"PUBLISHED","execution_mode":"SHA_LOCKED_OFFICIAL_SOURCE_SNAPSHOT",
      "first_unverified_step_completed":c["first_unverified_step"],
      "next_unverified_step":("VALIDATE_AND_PUBLISH_LLWR_ESC2026_EXACT_AIR_RELEASE_ROWS" if state.startswith("EXACT") else "ADVANCE_TO_NEXT_UNVERIFIED_GAS_EMISSIONS_SOURCE_AFTER_LLWR_ESC2026_NO_DATA"),
      "input":{"contract_path":str(a.contract),"contract_sha256":hashlib.sha256(cb).hexdigest(),
               "prior_output_path":str(a.prior),"prior_output_sha256":hashlib.sha256(pb).hexdigest(),
               "snapshot_path":str(a.snapshot),"snapshot_sha256":hashlib.sha256(sb).hexdigest(),
               "source_url":s["source_url"],"capture_scope":s["capture_scope"]},
      "counts":{"completed_count":1,"target_count":1,"records_scanned":len(recs),
                "matched_rows":len(complete_rows),"produced_business_rows":len(complete_rows),
                "produced_source_evidence_records":len(recs)},
      "progress_percent":100.0,
      "targets":[{"target_id":"LLWR_ESC2026_AIR_RELEASES","site_name":"Low Level Waste Repository",
                  "attempt_completed":True,"matched_rows":len(complete_rows),"matches":complete_rows,"decision":state}],
      "decision":{"document_site_identity_required":True,"air_discharge_section_required":True,
                  "graph_values_not_digitised":True,"source_values_preserved_without_conversion":True,
                  "inferred_values":0,"fake_data":False}
    }
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,ensure_ascii=False,sort_keys=True,separators=(",",":")),encoding="utf-8")
    return 0
if __name__=="__main__": raise SystemExit(main())
