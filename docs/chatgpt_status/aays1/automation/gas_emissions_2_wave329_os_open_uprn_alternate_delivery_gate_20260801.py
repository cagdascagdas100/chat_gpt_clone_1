#!/usr/bin/env python3
"""Wave329 official alternate delivery and sanctioned runner discovery gate."""
import argparse, hashlib, json
from pathlib import Path
SOURCES={"canonical_wave328","canonical_parcel_sample","os_arcgis_item","data_gov_uk_ndl","data_gov_uk_ckan_dataset","data_gov_uk_ckan_api_resource","api_gov_uk_catalog","os_product_page","runtime_delivery_and_runner_probe"}
SAMPLES={"parcel_30762","parcel_30763","parcel_30764"}
SURFACES=["os_arcgis_item","data_gov_uk_ndl","data_gov_uk_ckan_dataset","api_gov_uk_catalog","os_product_page"]
HOSTS=["api.os.uk","www.arcgis.com","ckan.publishing.service.gov.uk","osdatahub.os.uk"]
def h(s): return hashlib.sha256(s.encode("utf-8")).hexdigest()
def load(p):
    v=json.loads(Path(p).read_text(encoding="utf-8"))
    if not isinstance(v,dict): raise ValueError("object required")
    return v
def build(v):
    if (v.get("slot_id"),v.get("wave"))!=("gas_emissions_2",329): raise ValueError("slot/wave")
    c,s,d,m=v["canonical_context"],v["canonical_samples"],v["delivery_assessment"],v["source_evidence_manifest"]
    if c.get("wave328_remote_readback")!="PASS" or c.get("slot_partition")!={"start":30762,"end":61522,"count":30761}: raise ValueError("canonical gate")
    if {x.get("parcel_id") for x in s}!=SAMPLES or any(x.get("geometry_type")!="Point" or x.get("uprn") is not None for x in s): raise ValueError("sample gate")
    if d.get("official_surfaces_assessed")!=SURFACES or d.get("official_surface_count")!=5: raise ValueError("surface gate")
    false_keys=("arcgis_independent_archive_found","data_gov_byte_bearing_resource_found","api_catalog_alternate_host_found","os_product_alternate_direct_archive_found","independent_byte_bearing_mirror_found","redirect_headers_acquired","metadata_bytes_acquired","bounded_header_bytes_acquired","archive_bytes_acquired","sanctioned_existing_external_network_runner_found","enfield_subset_acquired","collision_audit_performed")
    if any(d.get(k) is not False for k in false_keys): raise ValueError("fail closed gate")
    if d.get("runtime_hosts_probed")!=HOSTS or d.get("runtime_dns_results")!=["EAI_AGAIN"]*4 or d.get("repository_runner_search_queries")!=3 or d.get("external_catalog_metadata_rendered") is not True: raise ValueError("runtime gate")
    by={}
    for x in m:
        sid,e=x.get("source_id"),x.get("relevant_excerpt")
        if not sid or not e or x.get("excerpt_sha256")!=h(e): raise ValueError("source hash")
        if any(not x.get(k) for k in ("publisher","source_url","accessed_at","hash_scope","supports_fields","license_or_terms_url")): raise ValueError("source fields")
        by[sid]=x
    if set(by)!=SOURCES: raise ValueError("source set")
    return {"schema_version":1,"slot_id":"gas_emissions_2","wave":329,"state":"NO_DATA_CONTINUE","decision":"OS_OPEN_UPRN_OFFICIAL_ALTERNATE_DELIVERY_SURFACE_NO_DATA_CONTINUE","decision_reason":"Five official delivery surfaces were audited. ArcGIS, data.gov.uk, the government API catalogue and the OS product page expose link metadata that returns to api.os.uk or OS Data Hub; none supplies an independent byte-bearing archive. Local DNS also fails for OS, ArcGIS and CKAN hosts, and no sanctioned existing external network workflow was found in the repository. No redirect headers, metadata, bounded CSV header or archive bytes were acquired, so no subset, collision audit or parcel binding is promoted.","canonical_context":c,"canonical_samples":s,"delivery_assessment":d,"source_count":len(m),"source_evidence_manifest":[by[k] for k in sorted(by)],"resolved_blockers":["OFFICIAL_ARCGIS_INDEPENDENT_ARCHIVE_EXISTENCE_UNKNOWN","DATA_GOV_UK_DIRECT_BYTE_MIRROR_EXISTENCE_UNKNOWN","API_GOV_UK_ALTERNATE_DOWNLOAD_HOST_EXISTENCE_UNKNOWN","SANCTIONED_EXISTING_EXTERNAL_NETWORK_RUNNER_EXISTENCE_UNKNOWN"],"remaining_blocker":"OFFICIAL_ARCGIS_AND_DATA_GOV_CATALOGS_ARE_LINK_ONLY_TO_API_OS_UK_OR_OSDATAHUB;INDEPENDENT_BYTE_BEARING_MIRROR_NOT_FOUND;EXECUTION_ENVIRONMENT_DNS_EGRESS_FAILURE_FOR_API_OS_UK_ARCGIS_CKAN_OSDATAHUB;SANCTIONED_EXISTING_EXTERNAL_NETWORK_RUNNER_NOT_DISCOVERED_IN_REPOSITORY;OS_OPEN_UPRN_REDIRECT_TARGET_METADATA_HEADER_ARCHIVE_BYTES_NOT_ACQUIRED;OS_OPEN_UPRN_ENFIELD_SUBSET_NOT_ACQUIRED;OS_OPEN_UPRN_COORDINATE_COLLISION_AUDIT_NOT_PERFORMED;CANONICAL_HMLR_POINT_NOT_DECLARED_AS_OS_ADDRESS_POINT;EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE","first_unverified_step":"OS_OPEN_UPRN_OFFICIAL_OS_SUPPORT_FILE_METADATA_RECEIPT_OR_EXISTING_SERIAL_RUNNER_EGRESS_RETRY_OR_NO_DATA_CONTINUE","business_rows_produced":0,"parcel_rows_bound":0,"completed_count":0,"target_count":30761,"previous_percent":0.0,"current_percent":0.0,"percent_increase":0.0,"fake_data":False,"final_ready":False}
def selftest():
    e="x"; m=[{"source_id":i,"publisher":"x","source_url":"x","accessed_at":"x","hash_scope":"x","relevant_excerpt":e,"excerpt_sha256":h(e),"supports_fields":["x"],"license_or_terms_url":"x"} for i in SOURCES]
    v={"slot_id":"gas_emissions_2","wave":329,"canonical_context":{"wave328_remote_readback":"PASS","slot_partition":{"start":30762,"end":61522,"count":30761}},"canonical_samples":[{"parcel_id":i,"geometry_type":"Point","uprn":None} for i in sorted(SAMPLES)],"delivery_assessment":{"official_surfaces_assessed":SURFACES,"official_surface_count":5,"arcgis_independent_archive_found":False,"data_gov_byte_bearing_resource_found":False,"api_catalog_alternate_host_found":False,"os_product_alternate_direct_archive_found":False,"independent_byte_bearing_mirror_found":False,"runtime_hosts_probed":HOSTS,"runtime_dns_results":["EAI_AGAIN"]*4,"external_catalog_metadata_rendered":True,"redirect_headers_acquired":False,"metadata_bytes_acquired":False,"bounded_header_bytes_acquired":False,"archive_bytes_acquired":False,"repository_runner_search_queries":3,"sanctioned_existing_external_network_runner_found":False,"enfield_subset_acquired":False,"collision_audit_performed":False},"source_evidence_manifest":m}
    assert build(v)["source_count"]==9; print("SELF_TEST_PASS")
def main():
    p=argparse.ArgumentParser(); p.add_argument("--fixture"); p.add_argument("--output"); p.add_argument("--self-test",action="store_true"); a=p.parse_args()
    if a.self_test: selftest(); return
    o=build(load(a.fixture)); Path(a.output).write_text(json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(",",":")),encoding="utf-8"); print("DECISION="+o["decision"]); print("BUSINESS_ROWS_PRODUCED=0"); print("PARCEL_ROWS_BOUND=0")
if __name__=="__main__": main()
