#!/usr/bin/env python3
from __future__ import annotations
import importlib.util,json
from pathlib import Path
def load(path):
 s=importlib.util.spec_from_file_location("guard",path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 base=Path(__file__).resolve().parent
 guard=load(base/"035_validate_port_blob_manifest.py")
 wave_path=base.parent/"source_candidates/022_official_source_candidates_20260722.json"
 wave=json.loads(wave_path.read_text(encoding="utf-8"));rows=wave["candidates"]
 eligible=[x for x in rows if x["eligibility"].startswith("eligible")]
 excluded=[x for x in rows if x["eligibility"].startswith("excluded")]
 checks=[]
 def ck(name,value): checks.append({"check":name,"passed":bool(value)})
 ck("candidate_count_6",len(rows)==6);ck("eligible_count_3",len(eligible)==3);ck("excluded_count_3",len(excluded)==3)
 ck("unique_candidate_ids",len({x["candidate_id"] for x in rows})==6);ck("unique_entities",len({x["source_entity"] for x in rows})==6);ck("unique_references",len({x["source_reference"] for x in rows})==6)
 ck("repo_search_no_overlap",wave["repository_search_evidence"]["matches_in_existing_repository"]==0)
 ck("authoritative_all",all(x["source_quality"]=="authoritative" for x in rows));ck("confidence_ge_90",all(x["source_confidence"]>=90 for x in rows))
 ck("eligible_blank_end",all(x["end_date"] is None for x in eligible));ck("excluded_end_present",all(x["end_date"] for x in excluded))
 ck("eligible_point_only",all(x["geometry_role"]=="point_only_candidate_locator_not_site_boundary" for x in eligible))
 ck("eligible_cap_65",all(x["parcel_match_confidence_cap"]==65 for x in eligible));ck("excluded_cap_zero",all(x["parcel_match_confidence_cap"]==0 for x in excluded))
 ck("omega_lapsed_excluded",any(x["source_entity"]==1710197 and x.get("official_notes_state_lapsed") and x["eligibility"].startswith("excluded") for x in rows))
 ck("product_fields_null",all(x["canonical_row_no"] is None and x["canonical_parcel_id"] is None and x["future_growth_score"] is None and x["future_growth_confidence"]==0 for x in rows))
 ck("provider_five_errors",wave["provider_quality"]["url_access_errors"]==5);ck("brownfield_not_submitted",wave["provider_quality"]["brownfield_status"]=="endpoint_not_submitted")
 ck("provider_no_uplift",wave["provider_quality"]["parcel_or_score_confidence_uplift"] is False)
 ck("hmlr_listed_not_downloaded",wave["hmlr"]["actual_downloads"]==0 and bool(wave["hmlr"]["authority_listed"]));ck("period_current_zero",wave["runtime"]["period_current_api_responses"]==0)
 files=[{"path":"docs/chatgpt_status/_shared/slots_21/future_growth_2/checkpoint_latest.json","blob_sha":"a"*40,"bytes":1,"role":"checkpoint"},{"path":"docs/chatgpt_status/_shared/slots_21/future_growth_2/status_latest.json","blob_sha":"b"*40,"bytes":1,"role":"status"},{"path":"docs/chatgpt_status/aays1/shards/future_growth_2/next_task_contract_latest.json","blob_sha":"c"*40,"bytes":1,"role":"runner"},{"path":"docs/chatgpt_status/aays1/shards/future_growth_2/port_manifest_latest.json","blob_sha":"d"*40,"bytes":1,"role":"scope"},{"path":"england_map_web/data/aays_21_slots/future_growth_2/index.html","blob_sha":"e"*40,"bytes":1,"role":"web"}]
 manifest={"slot_id":"future_growth_2","source_head_sha":"f"*40,"target_base_sha":"1"*40,"files":files,"product_state":{"verified_rows":0,"canonical_parcel_matches":0,"future_growth_scores":0,"actual_business_rows_written":0}}
 observed={x["path"]:x["blob_sha"] for x in files};ck("manifest_valid",guard.validate(manifest,observed)["observed_exact_matches"]==5)
 mutations=[("bad_sha",lambda p,o:p["files"][0].update(blob_sha="bad")),("mismatch",lambda p,o:o.update({p["files"][0]["path"]:"9"*40})),("duplicate",lambda p,o:p["files"].append(dict(p["files"][0]))),("outside",lambda p,o:p["files"][0].update(path="other/file")),("traversal",lambda p,o:p["files"][0].update(path="docs/chatgpt_status/aays1/shards/future_growth_2/../x")),("missing_required",lambda p,o:p["files"].pop()),("nonzero_product",lambda p,o:p["product_state"].update(verified_rows=1))]
 for name,mut in mutations:
  p=json.loads(json.dumps(manifest));o=dict(observed)
  try: mut(p,o);guard.validate(p,o);rejected=False
  except Exception: rejected=True
  ck(name+"_rejected",rejected)
 passed=sum(x["passed"] for x in checks)
 out={"schema_version":1,"slot_id":"future_growth_2","executed":True,"test_type":"wave22_registry_and_blob_manifest_integrity","checks_passed":passed,"checks_total":len(checks),"all_passed":passed==len(checks),"checks":checks,"canonical_parcel_matches":0,"future_growth_scores_produced":0,"actual_business_data_rows_written":0,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
 print(json.dumps(out));return 0 if out["all_passed"] else 1
if __name__=="__main__": raise SystemExit(main())
