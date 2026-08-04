#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
SLOT="future_growth_2"; ROWS=(30762,46142,61522); PARCELS={f"parcel_{n}" for n in ROWS}
BLOCK="TRACKED_SAMPLE_CANDIDATES_LACK_EXACT_UPRN_TITLE_NUMBER_OR_GEOMETRY_VALUES"
NEXT="LOCATE_TRACKED_OFFICIAL_ADDRESS_OR_UPRN_VALUES_FOR_SAMPLE_CANDIDATES"
UK={"uprn","unique_property_reference_number"}; TK={"title_no","title_number","title"}
GK={"geometry_sha256","geometry_hash","polygon_sha256","polygon_hash","exact_geometry_sha256"}
def load(p):
 v=json.loads(Path(p).read_text(encoding="utf-8"))
 if not isinstance(v,dict): raise ValueError(f"{p} must contain a JSON object")
 return v
def nz(v): return v not in (None,"",[],{})
def inspect(r):
 d={str(k).strip().lower():v for k,v in r.items()}; row=d.get("row_no"); parcel=d.get("parcel_id")
 u=any(nz(d.get(k)) for k in UK); t=any(nz(d.get(k)) for k in TK); g=any(nz(d.get(k)) for k in GK)
 return {"row_no":row,"parcel_id":parcel,"row_expected":row in ROWS,"parcel_expected":parcel in PARCELS,
 "uprn":u,"title":t,"geometry_digest":g,"title_uprn":u and t,"geometry_binding":g and (row in ROWS or parcel in PARCELS)}
def mchecks(m):
 src=[x for x in m.get("sources",[]) if isinstance(x,dict)]; roles={x.get("evidence_role") for x in src}
 h=next((x for x in src if x.get("evidence_role")=="official_hmlr_binding_contract"),{}).get("proven",{})
 return {"candidate_input":"tracked_candidate_input" in roles,"candidate_validation":"tracked_candidate_validation" in roles,
 "prior_gate":"tracked_linkage_gate" in roles,"hmlr_contract":"official_hmlr_binding_contract" in roles,
 "hmlr_title_no":h.get("title_no_field") is True,"hmlr_uprn":h.get("uprn_field") is True,
 "hmlr_relationship":h.get("relationship_required") is True}
def evaluate(c,v,p,m,key):
 rows=c.get("sample_candidates",[]); items=[inspect(x) for x in rows if isinstance(x,dict)]
 mc=mchecks(m); checks={"slot":c.get("slot_id")==SLOT,"pending":c.get("state")=="UPRN_ADDRESS_IDENTITY_COMPLETE_EXACT_BINDING_PENDING",
 "rows":tuple(x.get("row_no") for x in items)==ROWS,"parcels":{x.get("parcel_id") for x in items}==PARCELS,
 "bound_zero":c.get("exact_parcel_bound_rows")==0,"fake_false":c.get("fake_data") is False,
 "validation_state":v.get("state")=="NO_DATA_CONTINUE","validation_absent":v.get("exact_uprn_title_or_geometry_binding_available") is False,
 "validation_rows":tuple(v.get("validated_candidate_row_numbers",[]))==ROWS,
 "prior_state":p.get("state")=="NO_DATA_CONTINUE","prior_verified":p.get("linkage_prerequisites_verified") is True,
 "manifest":all(mc.values())}
 ok=all(checks.values()); tu=sum(x["title_uprn"] for x in items); gg=sum(x["geometry_binding"] for x in items); exact=tu+gg
 found=ok and exact>0; state="PUBLISHED" if found else ("NO_DATA_CONTINUE" if ok else "BLOCKED")
 summaries=[{"row_no":x["row_no"],"parcel_id_matches_expected":x["parcel_expected"],"structured_uprn_present":x["uprn"],
 "structured_title_number_present":x["title"],"structured_geometry_digest_present":x["geometry_digest"],
 "exact_binding_present":x["title_uprn"] or x["geometry_binding"]} for x in items]
 return {"schema_version":3,"architecture_version":3,"workstream_id":"AAYS_21_SLOT_SAFE_PARALLEL_V1","slot_id":SLOT,
 "task_continuation_key":key,"state":state,"panel_status":"PUBLISHED" if ok else "BLOCKED",
 "completed_count":1 if ok else 0,"target_count":1,"progress_percent":100.0 if ok else 0.0,
 "global_business_completed_count":0,"global_business_target_count":30761,"global_progress_percent":0.0,
 "produced_business_rows":0,"validated_candidate_count":len(items) if ok else 0,
 "structured_uprn_candidate_count":sum(x["uprn"] for x in items),"structured_title_number_candidate_count":sum(x["title"] for x in items),
 "structured_geometry_digest_candidate_count":sum(x["geometry_digest"] for x in items),"exact_title_uprn_binding_count":tu,
 "exact_geometry_binding_count":gg,"exact_binding_count":exact,"exact_binding_available":found,"candidate_summaries":summaries,
 "checks":checks,"manifest_checks":mc,"blocker":None if found else (BLOCK if ok else "TRACKED_EXACT_BINDING_PRESENCE_GATE_INPUT_VALIDATION_FAILED"),
 "next_unverified_step":"VALIDATE_EXACT_BINDING_PROVENANCE_AND_LINK_TITLE_BOUNDARY" if found else (NEXT if ok else "REPAIR_TRACKED_EXACT_BINDING_PRESENCE_GATE_INPUTS"),
 "source_rows_persisted":False,"identifier_values_persisted":False,"response_body_persisted":False,
 "geometry_persisted":False,"coordinates_persisted":False,"point_persisted":False,"inferred_linkage_persisted":False,"fake_data":False}
def fixture():
 c={"slot_id":SLOT,"state":"UPRN_ADDRESS_IDENTITY_COMPLETE_EXACT_BINDING_PENDING","exact_parcel_bound_rows":0,"fake_data":False,
 "sample_candidates":[{"row_no":n,"parcel_id":f"parcel_{n}","source_codes":["HMLR_TITLE_UPRN_LOOKUP"]} for n in ROWS]}
 v={"state":"NO_DATA_CONTINUE","exact_uprn_title_or_geometry_binding_available":False,"validated_candidate_row_numbers":list(ROWS)}
 p={"state":"NO_DATA_CONTINUE","linkage_prerequisites_verified":True}
 m={"sources":[{"evidence_role":"tracked_candidate_input"},{"evidence_role":"tracked_candidate_validation"},{"evidence_role":"tracked_linkage_gate"},
 {"evidence_role":"official_hmlr_binding_contract","proven":{"title_no_field":True,"uprn_field":True,"relationship_required":True}}]}
 return c,v,p,m
def selftest():
 c,v,p,m=fixture(); a=evaluate(c,v,p,m,"x"); tests=[a["state"]=="NO_DATA_CONTINUE",a["completed_count"]==1 and a["progress_percent"]==100.0,
 a["exact_binding_count"]==0,a["identifier_values_persisted"] is False]
 c2=json.loads(json.dumps(c)); c2["sample_candidates"][0].update({"uprn":1,"title_no":"NGL1"}); b=evaluate(c2,v,p,m,"x")
 tests += [b["state"]=="PUBLISHED" and b["exact_title_uprn_binding_count"]==1]
 c3=json.loads(json.dumps(c)); c3["sample_candidates"][1]["geometry_sha256"]="a"*64; d=evaluate(c3,v,p,m,"x")
 tests += [d["state"]=="PUBLISHED" and d["exact_geometry_binding_count"]==1]
 c4=json.loads(json.dumps(c)); c4["sample_candidates"][0]["row_no"]=1; tests += [evaluate(c4,v,p,m,"x")["state"]=="BLOCKED"]
 tests += [evaluate(c,v,p,{"sources":[]},"x")["state"]=="BLOCKED"]
 n=sum(tests); return {"passed":n,"target":len(tests),"result":f"PASS_{n}_OF_{len(tests)}"}
def main():
 a=argparse.ArgumentParser(); a.add_argument("--candidate-input"); a.add_argument("--candidate-validation"); a.add_argument("--prior-gate")
 a.add_argument("--manifest"); a.add_argument("--output"); a.add_argument("--task-continuation-key"); a.add_argument("--self-test",action="store_true"); x=a.parse_args()
 if x.self_test: print(json.dumps(selftest(),sort_keys=True,separators=(",",":"))); return 0
 if not all((x.candidate_input,x.candidate_validation,x.prior_gate,x.manifest,x.output,x.task_continuation_key)): a.error("all inputs are required")
 r=evaluate(load(x.candidate_input),load(x.candidate_validation),load(x.prior_gate),load(x.manifest),x.task_continuation_key)
 out=Path(x.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(r,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8"); return 0
if __name__=="__main__": sys.exit(main())
