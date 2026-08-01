#!/usr/bin/env python3
"""Wave321 fail-closed authorised NPS/EPC input inventory."""
import argparse, hashlib, json
from pathlib import Path

SOURCES={"canonical_wave320","canonical_current_task","github_inventory_probes","hmlr_nps_service","hmlr_nps_sample_licence","hmlr_api_documentation","epc_service"}
QUERIES={"nps_sample","HMLR_API_KEY","NPS_API_KEY","Title_No","EPC_BEARER_TOKEN","EPC_API_TOKEN"}
FLAGS={"declared_authorised_nps_input_present","declared_nps_sample_input_present","declared_exact_title_uprn_input_present","declared_exact_polygon_input_present","declared_epc_bulk_input_present","declared_epc_token_receipt_present"}

def sha(s): return hashlib.sha256(s.encode()).hexdigest()
def load(p):
    v=json.loads(Path(p).read_text())
    if not isinstance(v,dict): raise ValueError("fixture object required")
    return v
def validate(v):
    if (v.get("slot_id"),v.get("wave"))!=("gas_emissions_2",321): raise ValueError("slot/wave")
    c=v.get("canonical_context"); i=v.get("repository_inventory"); m=v.get("source_evidence_manifest")
    if not all(isinstance(x,t) for x,t in ((c,dict),(i,dict),(m,list))): raise ValueError("sections")
    if c.get("slot_partition")!={"start":30762,"end":61522,"count":30761} or c.get("wave320_remote_readback")!="PASS": raise ValueError("context")
    if any(c.get(k) is not False for k in FLAGS): raise ValueError("authorised input unexpectedly declared")
    q={x.get("query"):x.get("indexed_results") for x in i.get("queries",[]) if isinstance(x,dict)}
    if set(q)!=QUERIES or any(q[x]!=0 for x in q): raise ValueError("search receipt")
    if i.get("full_tree_proof") is not False or i.get("authorised_input_artifact_found") is not False: raise ValueError("inventory overclaim")
    by={}
    for x in m:
        sid=x.get("source_id"); e=x.get("relevant_excerpt")
        if not sid or not e or x.get("excerpt_sha256")!=sha(e): raise ValueError("source sha")
        if any(not x.get(k) for k in ("publisher","source_url","accessed_at","hash_scope","supports_fields","license_or_terms_url")): raise ValueError("source fields")
        by[sid]=x
    if set(by)!=SOURCES: raise ValueError("source set")
    return [by[x] for x in sorted(by)],c,i
def build(v):
    m,c,i=validate(v)
    return {"schema_version":1,"slot_id":"gas_emissions_2","wave":321,"state":"NO_DATA_CONTINUE","decision":"AUTHORISED_NPS_EPC_INPUT_INVENTORY_NO_DATA_CONTINUE","decision_reason":"Canonical task inputs contain no authorised NPS/NPS-sample archive, title-number/UPRN file, exact polygon file, EPC bulk file, or access-token receipt. Indexed probes also returned zero but are not a full-tree proof. The free NPS sample requires account and licence acceptance and covers Bristol 5km2, not the current Enfield sample rows. Full NPS remains chargeable and EPC bulk access requires GOV.UK One Login.","canonical_context":c,"repository_inventory":i,"source_count":len(m),"source_evidence_manifest":m,"resolved_blockers":["FREE_NPS_SAMPLE_EXISTENCE_UNVERIFIED","AUTHORISED_INPUT_INVENTORY_NOT_EXECUTED"],"remaining_blocker":"CANONICAL_AUTHORISED_NPS_OR_NPS_SAMPLE_INPUT_NOT_DECLARED;FREE_NPS_SAMPLE_ACCOUNT_AND_LICENCE_ACCEPTANCE_REQUIRED;FREE_NPS_SAMPLE_BRISTOL_5KM2_NOT_PROVEN_TO_COVER_CURRENT_ENFIELD_SAMPLE_ROWS;FULL_NPS_LICENSE_AND_PAYMENT_REQUIRED_FOR_NATIONWIDE_COVERAGE;CANONICAL_EXACT_POLYGON_INPUT_NOT_DECLARED;CANONICAL_EPC_BULK_OR_TOKEN_RECEIPT_NOT_DECLARED;PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE","first_unverified_step":"OFFICIAL_PARCEL_LEVEL_GAS_OR_CO2_ALTERNATIVE_SOURCE_DISCOVERY_OR_NO_DATA_CONTINUE","business_rows_produced":0,"parcel_rows_bound":0,"completed_count":0,"target_count":30761,"previous_percent":0.0,"current_percent":0.0,"percent_increase":0.0,"fake_data":False,"final_ready":False}
def self_test():
    e="x"; m=[{"source_id":s,"publisher":"x","source_url":"https://x","accessed_at":"x","hash_scope":"x","relevant_excerpt":e,"excerpt_sha256":sha(e),"supports_fields":["x"],"license_or_terms_url":"https://x"} for s in SOURCES]
    v={"slot_id":"gas_emissions_2","wave":321,"canonical_context":{"slot_partition":{"start":30762,"end":61522,"count":30761},"wave320_remote_readback":"PASS",**{k:False for k in FLAGS}},"repository_inventory":{"queries":[{"query":q,"indexed_results":0} for q in QUERIES],"full_tree_proof":False,"authorised_input_artifact_found":False},"source_evidence_manifest":m}
    assert build(v)["source_count"]==7; print("SELF_TEST_PASS")
def main():
    p=argparse.ArgumentParser(); p.add_argument("--fixture"); p.add_argument("--output"); p.add_argument("--self-test",action="store_true"); a=p.parse_args()
    if a.self_test: self_test(); return
    if not a.fixture or not a.output: p.error("--fixture and --output required")
    o=build(load(a.fixture)); Path(a.output).write_text(json.dumps(o,sort_keys=True,separators=(",",":")))
    print("DECISION="+o["decision"]); print("BUSINESS_ROWS_PRODUCED=0"); print("PARCEL_ROWS_BOUND=0")
if __name__=="__main__": main()
