#!/usr/bin/env python3
"""Fail-closed validator for future_growth_1 attempt-4 evidence; no network or scoring."""
from __future__ import annotations
import argparse, copy, hashlib, json, tempfile
from pathlib import Path

SLOT="future_growth_1"
TASK="aays1-future-growth-1-official-geometry-pipeline-20260721"
ATTEMPT="future-growth-1-20260721-004"
REFS={"LBBD49/XJ","LBBD64/XE","LBBD72/ZZ","LBBD91/DI"}
IDS={"39729785","39724273","60116682","39721628","63561067","39747087"}
RUN_REL=Path("docs/chatgpt_status/aays1/shards/future_growth_1/runner_outputs/004_official_geometry_pipeline_v4_latest.json")
REL_REL=Path("england_map_web/data/aays_21_slots/future_growth_1/geometry_wave_4/verified/official_geometry_relations_v3_latest.json")
GLA_REL=Path("docs/chatgpt_status/aays1/shards/future_growth_1/runner_outputs/004_official_geometry_pipeline_v4_latest/sources/gla_brownfield_target_sites.geojson")
BUILDER_REL=Path("docs/chatgpt_status/aays1/shards/future_growth_1/automation/004_build_official_geometry_relations_v3.py")
CAND_REL=Path("england_map_web/data/aays_21_slots/future_growth_1/candidates_combined_rows_1_6_latest.json")

def load(p): return json.loads(p.read_text(encoding="utf-8-sig"))
def digest(p):
 d=hashlib.sha256()
 with p.open("rb") as f:
  for c in iter(lambda:f.read(1048576),b""): d.update(c)
 return d.hexdigest()
def add(ok,code,fail):
 if not ok: fail.append(code)
def rpath(repo,v):
 if not isinstance(v,str) or not v.strip(): return None
 p=Path(v)
 if p.is_absolute():
  try: p.relative_to(repo)
  except ValueError: return None
  return p
 return (repo/p).resolve()
def result(fail,checks):
 fail=sorted(set(fail))
 return {"schema_version":1,"slot_id":SLOT,"task_id":TASK,"attempt_id":ATTEMPT,"result":"PASS" if not fail else "FAIL","failure_count":len(fail),"failures":fail,"checks":checks,"actual_business_data_rows_written":0,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}

def validate(repo,runner_path,relation_path):
 repo,runner_path,relation_path=map(Path,(repo,runner_path,relation_path)); repo=repo.resolve(); runner_path=runner_path.resolve(); relation_path=relation_path.resolve(); fail=[]; checks={}
 add(runner_path.is_file(),"RUNNER_OUTPUT_MISSING",fail); add(relation_path.is_file(),"RELATION_OUTPUT_MISSING",fail)
 if fail:return result(fail,checks)
 try:r=load(runner_path); g=load(relation_path)
 except Exception:return result(["INVALID_JSON"],checks)
 for k,v in {"slot_id":SLOT,"task_id":TASK,"attempt_id":ATTEMPT,"state":"COMPLETED_SOURCE_GEOMETRY_WAVE","status":"COMPLETED_EXACT_OFFICIAL_GEOMETRY_WAVE_SIX_PARCELS_NO_SCORE"}.items(): add(r.get(k)==v,f"RUNNER_{k.upper()}_MISMATCH",fail)
 for k in ("final_ready","fake_data","db_write","migration","production_deploy"): add(r.get(k) is False,f"RUNNER_{k.upper()}_NOT_FALSE",fail)
 add(r.get("actual_business_data_rows_written")==0,"RUNNER_BUSINESS_ROWS_NONZERO",fail)
 steps=r.get("source_steps") or {}; gla=steps.get("gla_brownfield") or {}; hm=steps.get("hmlr_source_manifest") or {}
 add(gla.get("ok") is True,"GLA_FETCH_NOT_OK",fail); add(gla.get("feature_count") in (4,5),"GLA_FEATURE_COUNT_INVALID",fail); add(set(gla.get("current_references_present") or [])==REFS,"GLA_REFS_MISMATCH",fail); add(hm.get("status")=="READY_HMLR_GML_DOWNLOADED","HMLR_NOT_READY",fail)
 add(rpath(repo,r.get("output_path"))==relation_path,"OUTPUT_PATH_MISMATCH",fail); add(r.get("next_unverified_step")=="BUILD_30761_ROW_FULL_FACTOR_MATRIX_THEN_SCORE_WITH_CONFIDENCE","NEXT_STEP_MISMATCH",fail); add(r.get("relation_result")==g,"RELATION_EMBED_DIFFERS",fail)
 c=g.get("counts") or {}; q=g.get("quality_gates") or {}; rows=g.get("rows") or []; checks={"counts":c,"quality_gates":q}
 add(g.get("slot_id")==SLOT,"RELATION_SLOT_MISMATCH",fail); add(g.get("matching_method")=="EXACT_HMLR_INSPIRE_ID_AND_POINT_INSIDE_THEN_GLA_POLYGON_RELATION","MATCH_METHOD_MISMATCH",fail); add(g.get("processing_crs")=="EPSG:27700","CRS_MISMATCH",fail)
 expected={"canonical_parcels_sampled":6,"exact_hmlr_parcel_polygons":6,"current_gla_site_polygons":4,"candidate_rows":15,"current_polygon_relations_verified":14,"stale_or_completed_rejections":1,"scored_business_rows":0,"actual_business_data_rows_written":0}
 for k,v in expected.items(): add(c.get(k)==v,f"COUNT_{k.upper()}_MISMATCH",fail)
 gates={"exact_hmlr_id_match":"6/6","candidate_point_inside_exact_hmlr_polygon":"6/6","current_gla_polygon_readback":"4/4","current_candidate_polygon_relations":"14/14","stale_false_positive_rejected":"1/1","future_growth_score_emitted":"0/30761"}
 for k,v in gates.items(): add(q.get(k)==v,f"GATE_{k.upper()}_MISMATCH",fail)
 add(q.get("nearest_polygon_fill_used") is False,"NEAREST_FILL_USED",fail); add(q.get("point_only_promotion_used") is False,"POINT_ONLY_PROMOTION_USED",fail)
 cur=[x for x in rows if isinstance(x,dict) and x.get("source_current") is True]; stale=[x for x in rows if isinstance(x,dict) and x.get("source_current") is not True]
 add(len(rows)==15,"ROWS_NOT_15",fail); add(len(cur)==14,"CURRENT_ROWS_NOT_14",fail); add(len(stale)==1,"STALE_ROWS_NOT_1",fail); add({str(x.get("hmlr_inspire_id")) for x in rows}==IDS,"HMLR_IDS_MISMATCH",fail); add({str(x.get("source_reference")) for x in cur}==REFS,"CURRENT_REFS_MISMATCH",fail)
 for i,x in enumerate(cur): add(x.get("site_polygon_verified") is True,f"ROW_{i}_SITE_POLYGON_FALSE",fail); add(x.get("parcel_polygon_verified") is True,f"ROW_{i}_PARCEL_POLYGON_FALSE",fail); add(x.get("official_entity_state")=="CURRENT_AUTHORITATIVE",f"ROW_{i}_STATE_INVALID",fail); add(x.get("future_growth_score") is None and x.get("scorable") is False,f"ROW_{i}_SCORE_OR_SCORABLE",fail)
 if stale: add(stale[0].get("official_entity_state")=="STALE_COMPLETED_REJECTED" and stale[0].get("relation_type")=="STALE_COMPLETED_NOT_ACTIVE_GROWTH" and stale[0].get("future_growth_score") is None and stale[0].get("scorable") is False,"STALE_ROW_INVALID",fail)
 sh=r.get("source_sha256") or {}; files={"relation_builder":repo/BUILDER_REL,"candidate_json":repo/CAND_REL,"gla_geojson":repo/GLA_REL}
 for k,p in files.items(): add(p.is_file(),f"SOURCE_{k.upper()}_MISSING",fail); add((not p.is_file()) or sh.get(k)==digest(p),f"SOURCE_{k.upper()}_SHA_MISMATCH",fail)
 if files["gla_geojson"].is_file(): add(gla.get("sha256")==digest(files["gla_geojson"]),"GLA_STEP_SHA_MISMATCH",fail); add((g.get("gla_source") or {}).get("sha256")==digest(files["gla_geojson"]),"GLA_RELATION_SHA_MISMATCH",fail)
 hs=g.get("hmlr_sources") or []; add(bool(hs),"HMLR_SOURCES_EMPTY",fail)
 for i,s in enumerate(hs):
  p=rpath(repo,(s or {}).get("path")); add(p is not None and p.is_file(),f"HMLR_SOURCE_{i}_MISSING",fail); add(p is None or not p.is_file() or (s or {}).get("sha256")==digest(p),f"HMLR_SOURCE_{i}_SHA_MISMATCH",fail)
 return result(fail,checks)

def fixtures(repo):
 h=repo/"tmp/hmlr.gml"; h.parent.mkdir(parents=True); h.write_text("hmlr")
 ids=sorted(IDS); refs=sorted(REFS); rows=[]
 for i in range(14): rows.append({"row_no":i%6+1,"parcel_id":f"parcel_{i%6+1}","hmlr_inspire_id":ids[i%6],"source_reference":refs[i%4],"source_current":True,"site_polygon_verified":True,"parcel_polygon_verified":True,"official_entity_state":"CURRENT_AUTHORITATIVE","relation_type":"WITHIN_2000M","future_growth_score":None,"scorable":False})
 rows.append({"row_no":1,"parcel_id":"parcel_1","hmlr_inspire_id":ids[0],"source_reference":"LBBD23","source_current":False,"site_polygon_verified":False,"parcel_polygon_verified":True,"official_entity_state":"STALE_COMPLETED_REJECTED","relation_type":"STALE_COMPLETED_NOT_ACTIVE_GROWTH","future_growth_score":None,"scorable":False})
 g={"slot_id":SLOT,"matching_method":"EXACT_HMLR_INSPIRE_ID_AND_POINT_INSIDE_THEN_GLA_POLYGON_RELATION","processing_crs":"EPSG:27700","hmlr_sources":[{"path":str(h),"sha256":digest(h)}],"gla_source":{},"counts":{"canonical_parcels_sampled":6,"exact_hmlr_parcel_polygons":6,"current_gla_site_polygons":4,"candidate_rows":15,"current_polygon_relations_verified":14,"stale_or_completed_rejections":1,"scored_business_rows":0,"actual_business_data_rows_written":0},"quality_gates":{"exact_hmlr_id_match":"6/6","candidate_point_inside_exact_hmlr_polygon":"6/6","current_gla_polygon_readback":"4/4","current_candidate_polygon_relations":"14/14","stale_false_positive_rejected":"1/1","nearest_polygon_fill_used":False,"point_only_promotion_used":False,"future_growth_score_emitted":"0/30761"},"rows":rows,"final_ready":False,"fake_data":False,"db_write":False}
 for p,t in ((repo/BUILDER_REL,"builder"),(repo/CAND_REL,"candidate"),(repo/GLA_REL,"gla")):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(t)
 g["gla_source"]={"sha256":digest(repo/GLA_REL)}; rel=repo/REL_REL; rel.parent.mkdir(parents=True,exist_ok=True)
 r={"slot_id":SLOT,"task_id":TASK,"attempt_id":ATTEMPT,"state":"COMPLETED_SOURCE_GEOMETRY_WAVE","status":"COMPLETED_EXACT_OFFICIAL_GEOMETRY_WAVE_SIX_PARCELS_NO_SCORE","source_steps":{"gla_brownfield":{"ok":True,"feature_count":4,"current_references_present":sorted(REFS),"sha256":digest(repo/GLA_REL)},"hmlr_source_manifest":{"status":"READY_HMLR_GML_DOWNLOADED"}},"relation_result":g,"source_sha256":{"relation_builder":digest(repo/BUILDER_REL),"candidate_json":digest(repo/CAND_REL),"gla_geojson":digest(repo/GLA_REL)},"output_path":str(rel),"next_unverified_step":"BUILD_30761_ROW_FULL_FACTOR_MATRIX_THEN_SCORE_WITH_CONFIDENCE","actual_business_data_rows_written":0,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}; run=repo/RUN_REL; run.parent.mkdir(parents=True,exist_ok=True); return r,g,run,rel

def selftest():
 cases=[]
 with tempfile.TemporaryDirectory() as td:
  repo=Path(td).resolve(); base_r,base_g,run,rel=fixtures(repo)
  tests=[("valid",lambda r,g:None,"PASS"),("task",lambda r,g:r.__setitem__("task_id","x"),"FAIL"),("attempt",lambda r,g:r.__setitem__("attempt_id","x"),"FAIL"),("running",lambda r,g:r.__setitem__("state","RUNNING"),"FAIL"),("final",lambda r,g:r.__setitem__("final_ready",True),"FAIL"),("gla",lambda r,g:g["counts"].__setitem__("current_gla_site_polygons",3),"FAIL"),("hmlr",lambda r,g:g["counts"].__setitem__("exact_hmlr_parcel_polygons",5),"FAIL"),("relation",lambda r,g:g["counts"].__setitem__("current_polygon_relations_verified",13),"FAIL"),("nearest",lambda r,g:g["quality_gates"].__setitem__("nearest_polygon_fill_used",True),"FAIL"),("score",lambda r,g:g["rows"][0].update({"future_growth_score":9,"scorable":True}),"FAIL"),("sha",lambda r,g:r["source_sha256"].__setitem__("candidate_json","0"*64),"FAIL"),("stale",lambda r,g:g["counts"].__setitem__("stale_or_completed_rejections",0),"FAIL")]
  for name,mut,exp in tests:
   r,g=copy.deepcopy(base_r),copy.deepcopy(base_g);mut(r,g);r["relation_result"]=g;rel.write_text(json.dumps(g));run.write_text(json.dumps(r));out=validate(repo,run,rel);cases.append({"case":name,"expected":exp,"actual":out["result"],"pass":out["result"]==exp,"failures":out["failures"][:4]})
 passed=sum(x["pass"] for x in cases);return {"schema_version":1,"slot_id":SLOT,"validation_semantics":"SYNTHETIC_VALIDATOR_SELFTEST_NOT_BUSINESS_EVIDENCE","result":"PASS" if passed==len(cases) else "FAIL","checks_passed":passed,"checks_total":len(cases),"cases":cases,"actual_business_data_rows_written":0,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}

def main():
 p=argparse.ArgumentParser();p.add_argument("--repo-root",type=Path,default=Path("."));p.add_argument("--runner-output",type=Path);p.add_argument("--relation-output",type=Path);p.add_argument("--report",type=Path);p.add_argument("--self-test",action="store_true");a=p.parse_args();repo=a.repo_root.resolve();out=selftest() if a.self_test else validate(repo,a.runner_output or repo/RUN_REL,a.relation_output or repo/REL_REL);text=json.dumps(out,ensure_ascii=False,indent=2)+"\n";print(text,end="");
 if a.report:a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(text,encoding="utf-8")
 return 0 if out["result"]=="PASS" else 2
if __name__=="__main__":raise SystemExit(main())
