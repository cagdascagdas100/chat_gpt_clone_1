#!/usr/bin/env python3
"""Combine exact-manifest postcode evidence from Ofcom, ONSPD, Code-Point Open and HMLR."""
from __future__ import annotations
import argparse,json,math,os,re,tempfile
from pathlib import Path
SLOT_ID="internet_access_3";SAMPLE_SIZE=384
def args():
 p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path);p.add_argument("--manifest",default="england_map_web/data/aays_21_slots/internet_access_3/stratified_candidate_manifest_latest.json");p.add_argument("--ofcom",default="england_map_web/data/aays_21_slots/internet_access_3/ofcom_2026_sample_candidates_latest.json");p.add_argument("--onspd",default="england_map_web/data/aays_21_slots/internet_access_3/onspd_2026_postcode_centroid_candidates_latest.json");p.add_argument("--codepoint",default="england_map_web/data/aays_21_slots/internet_access_3/codepoint_open_exact_candidates_latest.json");p.add_argument("--hmlr",default="england_map_web/data/aays_21_slots/internet_access_3/hmlr_exact_stratified_candidates_latest.json");p.add_argument("--minimum-core-ratio",type=float,default=.95);p.add_argument("--minimum-spatial-ratio",type=float,default=.90);p.add_argument("--runner-output",default="docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/048_official_postcode_source_consensus_latest.json");p.add_argument("--web-output",default="england_map_web/data/aays_21_slots/internet_access_3/official_postcode_source_consensus_latest.json");p.add_argument("--preview-output",default="england_map_web/data/aays_21_slots/internet_access_3/official_postcode_source_consensus_preview_latest.json");return p.parse_args()
def root(x):
 if x:return x.expanduser().resolve()
 for p in [Path.cwd(),*Path(__file__).resolve().parents]:
  if (p/"docs").exists() and (p/"england_map_web").exists():return p
 raise FileNotFoundError
def load(p):
 with p.open("r",encoding="utf-8-sig") as h:return json.load(h)
def write(p,o):
 p.parent.mkdir(parents=True,exist_ok=True);fd,t=tempfile.mkstemp(dir=p.parent,prefix=p.name+".")
 try:
  with os.fdopen(fd,"w",encoding="utf-8") as h:json.dump(o,h,ensure_ascii=False,separators=(",",":"));h.write("\n")
  os.replace(t,p)
 except Exception:
  try:os.unlink(t)
  except FileNotFoundError:pass
  raise
def pc(v):
 x=re.sub(r"\s+","",str(v or "")).upper();return x if re.fullmatch(r"[A-Z]{1,2}[0-9][0-9A-Z]?[0-9][A-Z]{2}",x) else None
def index(rows):
 if not isinstance(rows,list):raise ValueError("candidate file must be list")
 out={}
 for row in rows:
  n=int(row["row_no"])
  if n in out:raise ValueError(f"duplicate row_no:{n}")
  out[n]=row
 return out
def evenly_spaced(rows,size):
 if len(rows)<=size:return rows
 return [rows[round(i*(len(rows)-1)/(size-1))] for i in range(size)]
def main():
 o=args()
 if not 0<o.minimum_core_ratio<=1 or not 0<o.minimum_spatial_ratio<=1:raise ValueError("ratio")
 r=root(o.repo_root);manifest=load(r/o.manifest)
 if not isinstance(manifest,list) or len(manifest)!=SAMPLE_SIZE:raise ValueError("manifest")
 ids=[int(x["row_no"]) for x in manifest]
 if len(set(ids))!=SAMPLE_SIZE:raise ValueError("manifest duplicate")
 sources={"ofcom":index(load(r/o.ofcom)),"onspd":index(load(r/o.onspd)),"codepoint":index(load(r/o.codepoint)),"hmlr":index(load(r/o.hmlr))};rows=[];core=spatial=identity=0
 for item in manifest:
  n=int(item["row_no"]);postcode=pc(item.get("postcode"));records={k:v.get(n) for k,v in sources.items()};same=all(rec is not None and pc(rec.get("postcode"))==postcode for rec in records.values());identity+=int(same)
  checks={"ofcom_exact_postcode":bool(records["ofcom"] and records["ofcom"].get("official_postcode_found")),"onspd_exact_postcode":bool(records["onspd"] and records["onspd"].get("onspd_postcode_found")),"codepoint_exact_postcode":bool(records["codepoint"] and records["codepoint"].get("codepoint_postcode_found")),"codepoint_coordinate":bool(records["codepoint"] and records["codepoint"].get("codepoint_coordinate_available")),"hmlr_polygon":bool(records["hmlr"] and records["hmlr"].get("hmlr_polygon_found")),"row_identity":same}
  core_ok=same and checks["ofcom_exact_postcode"] and checks["onspd_exact_postcode"] and checks["codepoint_exact_postcode"];spatial_ok=core_ok and checks["codepoint_coordinate"] and checks["hmlr_polygon"];core+=int(core_ok);spatial+=int(spatial_ok)
  rows.append({"row_no":n,"parcel_id":item.get("parcel_id"),"postcode":postcode,"checks":checks,"core_postcode_quorum_passed":core_ok,"spatial_support_passed":spatial_ok,"source_support_count":sum(bool(v) for k,v in checks.items() if k!="row_identity"),"status":"FOUR_SOURCE_EVIDENCE_NOT_PROMOTED" if spatial_ok else "SOURCE_EVIDENCE_INCOMPLETE","parcel_relation_promoted":False,"confidence_raised":False})
 core_min=math.ceil(SAMPLE_SIZE*o.minimum_core_ratio);spatial_min=math.ceil(SAMPLE_SIZE*o.minimum_spatial_ratio);blockers=[]
 if identity!=SAMPLE_SIZE:blockers.append(f"ROW_IDENTITY:{identity}!={SAMPLE_SIZE}")
 if core<core_min:blockers.append(f"CORE_POSTCODE_QUORUM:{core}<{core_min}")
 if spatial<spatial_min:blockers.append(f"SPATIAL_SUPPORT:{spatial}<{spatial_min}")
 passed=not blockers;now=__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat();summary={"schema_version":1,"task_id":"aays1-internet-access-3-official-postcode-source-consensus-20260722","slot_id":SLOT_ID,"state":"runtime_validation_passed" if passed else "blocked","updated_at":now,"guard":{"sample_size_required":SAMPLE_SIZE,"core_sources":["Ofcom","ONSPD","Code-Point Open"],"spatial_support_source":"HMLR INSPIRE","minimum_core_ratio":o.minimum_core_ratio,"minimum_core_rows":core_min,"minimum_spatial_ratio":o.minimum_spatial_ratio,"minimum_spatial_rows":spatial_min},"result":{"manifest_rows":SAMPLE_SIZE,"row_identity_matches":identity,"core_postcode_quorum_rows":core,"spatial_support_rows":spatial,"parcel_relations_promoted":0,"confidence_uplifts":0,"actual_business_data_rows_written":0},"validation":{"passed":passed,"blockers":blockers},"output_semantics":"MULTI_SOURCE_POSTCODE_AND_INDICATIVE_SPATIAL_SUPPORT_ONLY_NOT_ADDRESS_OR_PARCEL_PROOF","final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False};preview={"schema_version":1,"slot_id":SLOT_ID,"state":"runtime_preview","row_count":40,"rows":evenly_spaced(rows,40),"parcel_relation_promoted":False,"final_ready":False}
 write(r/o.runner_output,summary);write(r/o.web_output,summary);write(r/o.preview_output,preview);print(json.dumps(summary,ensure_ascii=False,indent=2));return 0 if passed else 2
if __name__=="__main__":
 try:raise SystemExit(main())
 except Exception as e:print(json.dumps({"slot_id":SLOT_ID,"state":"exception","error_type":type(e).__name__,"error":str(e),"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False},ensure_ascii=False),file=__import__("sys").stderr);raise
