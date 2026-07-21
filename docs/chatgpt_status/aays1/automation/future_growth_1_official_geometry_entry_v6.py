#!/usr/bin/env python3
"""Single-runner wrapper for future_growth_1 attempt 4, contract revision 6.

Extracts exact canonical rows 20-24 first, then runs the revision-5 exact geometry
and 19-query sample. Fail closed; never emits scores or writes business/database rows.
"""
from __future__ import annotations
import hashlib, json, os, subprocess, sys, time
from pathlib import Path
from typing import Any

SLOT_ID='future_growth_1'
TASK_ID='aays1-future-growth-1-official-geometry-pipeline-20260721'
ATTEMPT_ID='future-growth-1-20260721-004'
CONTRACT_REVISION=6
EXPECTED_CANONICAL_SHA='8afd1d2bac414cf0f6b9484014e7878a4ceff877'
REPO=Path(os.environ.get('AAYS_REPO_ROOT','.')).resolve()
V5_ENTRY=REPO/'docs/chatgpt_status/aays1/automation/future_growth_1_official_geometry_entry_v5.py'
EXTRACTOR=REPO/'docs/chatgpt_status/aays1/shards/future_growth_1/automation/007_extract_rows_20_24_from_canonical_stream.py'
CANONICAL=REPO/'england_map_web/data/program_layer_matrix/security.geojson'
ROWS_OUTPUT=REPO/'england_map_web/data/aays_21_slots/future_growth_1/canonical_rows_20_24_latest.json'
V5_RUNNER_STATUS=REPO/'docs/chatgpt_status/aays1/shards/future_growth_1/runner_outputs/004_official_geometry_pipeline_v4_latest.json'
RUNNER_STATUS=REPO/'docs/chatgpt_status/aays1/shards/future_growth_1/runner_outputs/004_official_geometry_pipeline_v6_latest.json'
WEB_STATUS=REPO/'england_map_web/data/aays_21_slots/future_growth_1/geometry_runner_status_v6_latest.json'
RELATION_OUTPUT=REPO/'england_map_web/data/aays_21_slots/future_growth_1/geometry_wave_4/verified/official_geometry_relations_v3_latest.json'
QUERY_EVIDENCE=REPO/'docs/chatgpt_status/aays1/shards/future_growth_1/runner_outputs/004_official_geometry_pipeline_v4_latest/planning_constraint_queries/execution_evidence_manifest.json'
QUERY_VALIDATION=REPO/'england_map_web/data/aays_21_slots/future_growth_1/geometry_wave_4/verified/planning_constraint_query_validation_latest.json'

def write_json(path:Path,value:Any)->None:
 path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def read_json(path:Path)->dict[str,Any]|None:
 if not path.is_file(): return None
 value=json.loads(path.read_text(encoding='utf-8-sig')); return value if isinstance(value,dict) else None
def sha256(path:Path)->str:
 h=hashlib.sha256();
 with path.open('rb') as f:
  for c in iter(lambda:f.read(1<<20),b''): h.update(c)
 return h.hexdigest()
def run(command:list[str])->dict[str,Any]:
 started=time.time(); p=subprocess.run(command,cwd=REPO,text=True,capture_output=True,check=False)
 return {'command':command,'exit_code':p.returncode,'stdout':p.stdout[-16000:],'stderr':p.stderr[-16000:],'elapsed_seconds':round(time.time()-started,3)}
def publish(payload:dict[str,Any])->None:
 write_json(RUNNER_STATUS,payload); write_json(WEB_STATUS,payload)
def blocked(result:dict[str,Any],status:str,blocker:str)->int:
 result.update(state='BLOCKED',status=status,blocker=blocker,completed_at_epoch=time.time(),final_ready=False,actual_business_data_rows_written=0,fake_data=False,db_write=False,migration=False,production_deploy=False); publish(result); return 2

def validate_rows(payload:dict[str,Any])->dict[str,bool]:
 rows=payload.get('rows') or []
 return {
  'row_extraction_semantics':payload.get('output_semantics')=='EXACT_CANONICAL_ROWS_20_24_NOT_CANDIDATES_NOT_POLYGONS_NOT_SCORES',
  'canonical_sha':payload.get('canonical_sha256')==EXPECTED_CANONICAL_SHA,
  'five_rows':len(rows)==5,
  'exact_row_numbers':[r.get('row_no') for r in rows]==[20,21,22,23,24],
  'exact_parcel_ids':[r.get('parcel_id') for r in rows]==[f'parcel_{i}' for i in range(20,25)],
  'unique_hmlr_ids':len({r.get('hmlr_inspire_id') for r in rows})==5,
  'no_nearest_fallback':payload.get('nearest_row_fallback_used') is False,
  'final_ready_false':payload.get('final_ready') is False,
 }

def validate_v5(status:dict[str,Any])->dict[str,bool]:
 return {
  'v5_completed':status.get('state')=='COMPLETED_SOURCE_GEOMETRY_AND_PLANNING_QUERY_SAMPLE',
  'v5_contract_revision':status.get('contract_revision')==5,
  'site_polygons':status.get('official_site_polygons_downloaded')==4,
  'parcel_polygons':status.get('exact_hmlr_parcel_polygons')==6,
  'relations':status.get('verified_polygon_relations')==14,
  'query_requests':status.get('planning_query_requests_executed')==19,
  'query_rows':status.get('planning_query_rows_validated')==19,
  'promotions_zero':status.get('source_wave_parcel_rows_promoted')==0,
  'scores_zero':status.get('scored_business_rows')==0,
  'business_rows_zero':status.get('actual_business_data_rows_written')==0,
  'final_ready_false':status.get('final_ready') is False,
 }

def main()->int:
 result={'schema_version':5,'architecture_version':3,'workstream_id':'AAYS_21_SLOT_SAFE_PARALLEL_V1','slot_id':SLOT_ID,'task_id':TASK_ID,'attempt_id':ATTEMPT_ID,'contract_revision':CONTRACT_REVISION,'started_at_epoch':time.time(),'state':'RUNNING','status':'RUNNING_ROWS_20_24_THEN_GEOMETRY_AND_19_QUERY_SAMPLE','source_steps':{},'actual_business_data_rows_written':0,'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False}
 publish(result)
 required=[V5_ENTRY,EXTRACTOR,CANONICAL]
 missing=[str(p) for p in required if not p.is_file()]
 if missing: result['missing_paths']=missing; return blocked(result,'BLOCKED_MISSING_REVISION6_PIPELINE_FILE','REQUIRED_REVISION6_PIPELINE_FILES_MISSING')
 extraction=run([sys.executable,str(EXTRACTOR),str(CANONICAL),str(ROWS_OUTPUT),'--expected-sha',EXPECTED_CANONICAL_SHA])
 rows_payload=read_json(ROWS_OUTPUT)
 result['source_steps']['rows_20_24_extraction']=extraction; result['rows_20_24']=rows_payload; publish(result)
 if extraction['exit_code']!=0 or not isinstance(rows_payload,dict): return blocked(result,'BLOCKED_ROWS_20_24_EXACT_EXTRACTION','EXACT_CANONICAL_ROWS_20_24_NOT_EXTRACTED')
 row_acceptance=validate_rows(rows_payload); result['rows_20_24_acceptance']=row_acceptance
 if not all(row_acceptance.values()): return blocked(result,'BLOCKED_ROWS_20_24_ACCEPTANCE','ONE_OR_MORE_ROWS_20_24_GATES_FAILED')
 v5_execution=run([sys.executable,str(V5_ENTRY)])
 v5_status=read_json(V5_RUNNER_STATUS)
 result['source_steps']['combined_v5_execution']=v5_execution; result['combined_v5_status']=v5_status; publish(result)
 if v5_execution['exit_code']!=0 or not isinstance(v5_status,dict): return blocked(result,'BLOCKED_COMBINED_V5_STAGE','REVISION5_COMBINED_STAGE_DID_NOT_COMPLETE')
 v5_acceptance=validate_v5(v5_status); result['combined_v5_acceptance']=v5_acceptance
 expected_outputs=[RELATION_OUTPUT,QUERY_EVIDENCE,QUERY_VALIDATION]
 missing_outputs=[str(p) for p in expected_outputs if not p.is_file()]
 if missing_outputs: result['missing_outputs']=missing_outputs; return blocked(result,'BLOCKED_REVISION6_EXPECTED_OUTPUT','REVISION6_EXPECTED_OUTPUTS_MISSING')
 if not all(v5_acceptance.values()): return blocked(result,'BLOCKED_REVISION6_COMBINED_ACCEPTANCE','ONE_OR_MORE_REVISION5_ACCEPTANCE_GATES_FAILED')
 result['source_sha256']={'canonical':sha256(CANONICAL),'extractor':sha256(EXTRACTOR),'v5_entry':sha256(V5_ENTRY),'rows_output':sha256(ROWS_OUTPUT),'relation_output':sha256(RELATION_OUTPUT),'query_evidence':sha256(QUERY_EVIDENCE),'query_validation':sha256(QUERY_VALIDATION)}
 result.update(state='COMPLETED_ROWS_20_24_GEOMETRY_AND_PLANNING_QUERY_SAMPLE',status='COMPLETED_EXACT_ROWS_20_24_PLUS_GEOMETRY_AND_19_PLANNING_DATA_QUERIES_NO_SCORE',canonical_rows_20_24_extracted=5,new_candidate_rows_created=0,official_site_polygons_downloaded=4,exact_hmlr_parcel_polygons=6,verified_polygon_relations=14,planning_query_requests_executed=19,planning_query_rows_validated=19,source_wave_parcel_rows_promoted=0,scored_business_rows=0,actual_business_data_rows_written=0,next_unverified_step='BUILD_ROWS_20_24_OFFICIAL_CANDIDATE_WAVE_AND_FULL_30761_FACTOR_MATRIX',completed_at_epoch=time.time())
 publish(result); return 0
if __name__=='__main__':
 try: raise SystemExit(main())
 except Exception as exc:
  payload={'schema_version':5,'slot_id':SLOT_ID,'task_id':TASK_ID,'attempt_id':ATTEMPT_ID,'contract_revision':CONTRACT_REVISION,'state':'BLOCKED','status':'BLOCKED_UNHANDLED_EXCEPTION','blocker':f'{type(exc).__name__}: {exc}','actual_business_data_rows_written':0,'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False}; publish(payload); print(json.dumps(payload,ensure_ascii=False),file=sys.stderr); raise
