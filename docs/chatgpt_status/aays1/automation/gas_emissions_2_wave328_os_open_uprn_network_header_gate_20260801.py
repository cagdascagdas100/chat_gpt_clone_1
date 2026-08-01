#!/usr/bin/env python3
"""Wave328 OS Open UPRN network/header fail-closed gate."""
import argparse, hashlib, json
from pathlib import Path

SOURCES={"canonical_wave327","canonical_parcel_sample","os_open_uprn_data_hub","os_downloads_api_technical_spec","os_download_open_product_endpoint","os_open_uprn_product_supply","os_arcgis_download_pointer","runtime_network_recovery_probe"}
SAMPLES={"parcel_30762","parcel_30763","parcel_30764"}
HOSTS=["api.os.uk","osdatahub.os.uk","docs.os.uk"]

def h(s): return hashlib.sha256(s.encode()).hexdigest()
def load(p):
    v=json.loads(Path(p).read_text(encoding="utf-8"))
    if not isinstance(v,dict): raise ValueError("object required")
    return v
def build(v):
    if (v.get("slot_id"),v.get("wave"))!=("gas_emissions_2",328): raise ValueError("slot/wave")
    c,s,n,m=v["canonical_context"],v["canonical_samples"],v["network_assessment"],v["source_evidence_manifest"]
    if c.get("wave327_remote_readback")!="PASS" or c.get("slot_partition")!={"start":30762,"end":61522,"count":30761}: raise ValueError("canonical gate")
    if {x.get("parcel_id") for x in s}!=SAMPLES or any(x.get("geometry_type")!="Point" or x.get("uprn") is not None for x in s): raise ValueError("sample gate")
    if n.get("hosts_probed")!=HOSTS or n.get("dns_results")!=["EAI_AGAIN"]*3: raise ValueError("dns gate")
    true_keys=("environment_wide_dns_egress_failure","head_redirect_attempted","ipv4_head_attempted","json_no_redirect_attempted","alternate_download_transport_attempted","endpoint_current_officially_documented","exact_csv_endpoint_reconfirmed")
    false_keys=("redirect_target_resolved","metadata_bytes_acquired","bounded_header_bytes_acquired","archive_bytes_acquired","enfield_subset_acquired","collision_audit_performed")
    if any(n.get(k) is not True for k in true_keys) or any(n.get(k) is not False for k in false_keys): raise ValueError("network gate")
    by={}
    for x in m:
        sid,e=x.get("source_id"),x.get("relevant_excerpt")
        if not sid or not e or x.get("excerpt_sha256")!=h(e): raise ValueError("source hash")
        if any(not x.get(k) for k in ("publisher","source_url","accessed_at","hash_scope","supports_fields","license_or_terms_url")): raise ValueError("source fields")
        by[sid]=x
    if set(by)!=SOURCES: raise ValueError("source set")
    return {"schema_version":1,"slot_id":"gas_emissions_2","wave":328,"state":"NO_DATA_CONTINUE","decision":"OS_OPEN_UPRN_NETWORK_RECOVERY_BOUNDED_HEADER_NO_DATA_CONTINUE","decision_reason":"Official OS sources reconfirm the current June 2026 product and exact no-key CSV redirect endpoint. api.os.uk, osdatahub.os.uk and docs.os.uk all returned EAI_AGAIN; redirect, IPv4 HEAD, IPv4 metadata and alternate download transports acquired zero bytes. Redirect target, archive metadata and bounded CSV header remain unavailable, so no coordinate or parcel binding is promoted.","canonical_context":c,"canonical_samples":s,"network_assessment":n,"source_count":len(m),"source_evidence_manifest":[by[k] for k in sorted(by)],"resolved_blockers":["OS_OPEN_UPRN_DNS_FAILURE_ENDPOINT_SPECIFICITY_UNKNOWN","OS_OPEN_UPRN_IPV4_RETRY_UNTESTED","OS_OPEN_UPRN_NON_REDIRECT_METADATA_RETRY_UNTESTED","OS_OPEN_UPRN_EXACT_CSV_ENDPOINT_RECONFIRMATION_PENDING"],"remaining_blocker":"EXECUTION_ENVIRONMENT_DNS_EGRESS_FAILURE_FOR_API_OS_UK_OSDATAHUB_OS_UK_DOCS_OS_UK;OS_OPEN_UPRN_REDIRECT_TARGET_UNRESOLVED;OS_OPEN_UPRN_METADATA_AND_BOUNDED_HEADER_BYTES_NOT_ACQUIRED;OS_OPEN_UPRN_ARCHIVE_CONTENT_LENGTH_ETAG_LAST_MODIFIED_AND_HASH_UNVERIFIED;OS_OPEN_UPRN_ENFIELD_SUBSET_NOT_ACQUIRED;OS_OPEN_UPRN_COORDINATE_COLLISION_AUDIT_NOT_PERFORMED;CANONICAL_HMLR_POINT_NOT_DECLARED_AS_OS_ADDRESS_POINT;EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE","first_unverified_step":"OS_OPEN_UPRN_OFFICIAL_ARCGIS_REDIRECT_RESOLUTION_OR_EXTERNAL_NETWORK_RUNNER_BOUNDED_HEADER_ACQUISITION_OR_NO_DATA_CONTINUE","business_rows_produced":0,"parcel_rows_bound":0,"completed_count":0,"target_count":30761,"previous_percent":0.0,"current_percent":0.0,"percent_increase":0.0,"fake_data":False,"final_ready":False}
def selftest():
    e="x"; m=[{"source_id":i,"publisher":"x","source_url":"x","accessed_at":"x","hash_scope":"x","relevant_excerpt":e,"excerpt_sha256":h(e),"supports_fields":["x"],"license_or_terms_url":"x"} for i in SOURCES]
    v={"slot_id":"gas_emissions_2","wave":328,"canonical_context":{"wave327_remote_readback":"PASS","slot_partition":{"start":30762,"end":61522,"count":30761}},"canonical_samples":[{"parcel_id":i,"geometry_type":"Point","uprn":None} for i in sorted(SAMPLES)],"network_assessment":{"hosts_probed":HOSTS,"dns_results":["EAI_AGAIN"]*3,"environment_wide_dns_egress_failure":True,"head_redirect_attempted":True,"ipv4_head_attempted":True,"json_no_redirect_attempted":True,"alternate_download_transport_attempted":True,"endpoint_current_officially_documented":True,"exact_csv_endpoint_reconfirmed":True,"redirect_target_resolved":False,"metadata_bytes_acquired":False,"bounded_header_bytes_acquired":False,"archive_bytes_acquired":False,"enfield_subset_acquired":False,"collision_audit_performed":False},"source_evidence_manifest":m}
    assert build(v)["source_count"]==8; print("SELF_TEST_PASS")
def main():
    p=argparse.ArgumentParser(); p.add_argument("--fixture"); p.add_argument("--output"); p.add_argument("--self-test",action="store_true"); a=p.parse_args()
    if a.self_test: selftest(); return
    o=build(load(a.fixture)); Path(a.output).write_text(json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(",",":")),encoding="utf-8"); print("DECISION="+o["decision"]); print("BUSINESS_ROWS_PRODUCED=0"); print("PARCEL_ROWS_BOUND=0")
if __name__=="__main__": main()
