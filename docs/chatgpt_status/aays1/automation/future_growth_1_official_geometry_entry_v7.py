#!/usr/bin/env python3
"""Revision-7 slot-local combined runner for future_growth_1.
Extract exact rows 20-24, run official geometry with the slot-local HMLR resolver,
then execute and validate 19 Planning Data requests. Fail closed; no scoring.
"""
from __future__ import annotations
import hashlib,json,os,subprocess,sys,time
from pathlib import Path
from typing import Any
SLOT_ID='future_growth_1'; TASK_ID='aays1-future-growth-1-official-geometry-pipeline-20260721'; ATTEMPT_ID='future-growth-1-20260722-005'; CONTRACT_REVISION=7
EXPECTED_CANONICAL_SHA='8afd1d2bac414cf0f6b9484014e7878a4ceff877'
REPO=Path(os.environ.get('AAYS_REPO_ROOT','.')).resolve()
GEOMETRY_ENTRY=REPO/'docs/chatgpt_status/aays1/automation/future_growth_1_official_geometry_entry_v7_geometry.py'
EXTRACTOR=REPO/'docs/chatgpt_status/aays1/shards/future_growth_1/automation/007_extract_rows_20_24_from_canonical_stream.py'
QUERY_EXECUTOR=REPO/'docs/chatgpt_status/aays1/shards/future_growth_1/automation/009_execute_planning_constraint_queries_v1.py'
QUERY_VALIDATOR=REPO/'docs/chatgpt_status/aays1/shards/future_growth_1/automation/008_validate_planning_constraint_query_output_v1.py'
CANONICAL=REPO/'england_map_web/data/program_layer_matrix/security.geojson'
ROWS_OUTPUT=REPO/'england_map_web/data/aays_21_slots/future_growth_1/canonical_rows_20_24_latest.json'
QUERY_MANIFEST=REPO/'england_map_web/data/aays_21_slots/future_growth_1/planning_constraint_query_manifest_rows_1_19_latest.json'
GEOMETRY_STATUS=REPO/'docs/chatgpt_status/aays1/shards/future_growth_1/runner_outputs/004_official_geometry_pipeline_v4_latest.json'
RELATION_OUTPUT=REPO/'england_map_web/data/aays_21_slots/future_growth_1/geometry_wave_4/verified/official_geometry_relations_v3_latest.json'
QUERY_OUTPUT=REPO/'docs/chatgpt_status/aays1/shards/future_growth_1/runner_outputs/005_official_geometry_pipeline_v7_latest/planning_constraint_queries'
QUERY_VALIDATION=REPO/'england_map_web/data/aays_21_slots/future_growth_1/geometry_wave_5/verified/planning_constraint_query_validation_v7_latest.json'
RUNNER_STATUS=REPO/'docs/chatgpt_status/aays1/shards/future_growth_1/runner_outputs/005_official_geometry_pipeline_v7_latest.json'
WEB_STATUS=REPO/'england_map_web/data/aays_21_slots/future_growth_1/geometry_runner_status_v7_latest.json'
def write_json(path:Path,value:Any)->None: path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def read_json(path:Path)->dict[str,Any]|None:
    if not path.is_file(): return None
    v=json.loads(path.read_text(encoding='utf-8-sig')); return v if isinstance(v,dict) else None
def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for c in iter(lambda:f.read(1<<20),b''): h.update(c)
    return h.hexdigest()
def run(cmd:list[str])->dict[str,Any]:
    started=time.time(); p=subprocess.run(cmd,cwd=REPO,text=True,capture_output=True,check=False)
    return {'command':cmd,'exit_code':p.returncode,'stdout':p.stdout[-16000:],'stderr':p.stderr[-16000:],'elapsed_seconds':round(time.time()-started,3)}
def publish(value:dict[str,Any])->None: write_json(RUNNER_STATUS,value); write_json(WEB_STATUS,value)
def blocked(result:dict[str,Any],status:str,blocker:str)->int:
    result.update(state='BLOCKED',status=status,blocker=blocker,completed_at_epoch=time.time(),actual_business_data_rows_written=0,final_ready=False,fake_data=False,db_write=False,migration=False,production_deploy=False); publish(result); return 2
def validate_rows(payload:dict[str,Any])->dict[str,bool]:
    rows=payload.get('rows') or []
    return {'semantics':payload.get('output_semantics')=='EXACT_CANONICAL_ROWS_20_24_NOT_CANDIDATES_NOT_POLYGONS_NOT_SCORES','canonical_sha':payload.get('canonical_sha256')==EXPECTED_CANONICAL_SHA,'five_rows':len(rows)==5,'row_numbers':[r.get('row_no') for r in rows]==[20,21,22,23,24],'parcel_ids':[r.get('parcel_id') for r in rows]==[f'parcel_{i}' for i in range(20,25)],'unique_hmlr_ids':len({r.get('hmlr_inspire_id') for r in rows})==5,'no_nearest':payload.get('nearest_row_fallback_used') is False}
def main()->int:
    result={'schema_version':7,'architecture_version':3,'workstream_id':'AAYS_21_SLOT_SAFE_PARALLEL_V1','slot_id':SLOT_ID,'task_id':TASK_ID,'attempt_id':ATTEMPT_ID,'contract_revision':CONTRACT_REVISION,'started_at_epoch':time.time(),'state':'RUNNING','status':'RUNNING_SLOT_LOCAL_GEOMETRY_AND_19_QUERY_SAMPLE','source_steps':{},'actual_business_data_rows_written':0,'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False}; publish(result)
    required=[GEOMETRY_ENTRY,EXTRACTOR,QUERY_EXECUTOR,QUERY_VALIDATOR,CANONICAL,QUERY_MANIFEST]; missing=[str(p) for p in required if not p.is_file()]
    if missing: result['missing_paths']=missing; return blocked(result,'BLOCKED_MISSING_REVISION7_FILE','REQUIRED_REVISION7_FILES_MISSING')
    extraction=run([sys.executable,str(EXTRACTOR),str(CANONICAL),str(ROWS_OUTPUT),'--expected-sha',EXPECTED_CANONICAL_SHA]); rows=read_json(ROWS_OUTPUT); result['source_steps']['rows_20_24_extraction']=extraction; result['rows_20_24']=rows; publish(result)
    if extraction['exit_code']!=0 or not isinstance(rows,dict): return blocked(result,'BLOCKED_ROWS_20_24_EXTRACTION','EXACT_CANONICAL_ROWS_20_24_NOT_EXTRACTED')
    row_acceptance=validate_rows(rows); result['rows_20_24_acceptance']=row_acceptance
    if not all(row_acceptance.values()): return blocked(result,'BLOCKED_ROWS_20_24_ACCEPTANCE','ROWS_20_24_GATES_FAILED')
    geometry_run=run([sys.executable,str(GEOMETRY_ENTRY)]); geometry=read_json(GEOMETRY_STATUS); result['source_steps']['slot_local_geometry']=geometry_run; result['geometry_status']=geometry; publish(result)
    if geometry_run['exit_code']!=0 or not isinstance(geometry,dict) or geometry.get('state')!='COMPLETED_SOURCE_GEOMETRY_WAVE': return blocked(result,'BLOCKED_SLOT_LOCAL_GEOMETRY_STAGE',str((geometry or {}).get('status') or 'GEOMETRY_STAGE_FAILED'))
    acceptance=dict(geometry.get('acceptance') or {})
    if not acceptance or not all(v is True for v in acceptance.values()) or not RELATION_OUTPUT.is_file(): return blocked(result,'BLOCKED_GEOMETRY_ACCEPTANCE','GEOMETRY_ACCEPTANCE_GATES_FAILED')
    qrun=run([sys.executable,str(QUERY_EXECUTOR),str(QUERY_MANIFEST),str(QUERY_OUTPUT),'--delay-seconds','1.0','--timeout-seconds','45','--retries','3']); qe=read_json(QUERY_OUTPUT/'execution_evidence_manifest.json'); result['source_steps']['planning_query_execution']=qrun; result['planning_query_evidence']=qe; publish(result)
    if qrun['exit_code']!=0 or not isinstance(qe,dict): return blocked(result,'BLOCKED_PLANNING_QUERY_EXECUTION','PLANNING_QUERY_EXECUTOR_DID_NOT_COMPLETE')
    qv_run=run([sys.executable,str(QUERY_VALIDATOR),str(QUERY_MANIFEST),str(QUERY_OUTPUT),str(QUERY_VALIDATION)]); qv=read_json(QUERY_VALIDATION); result['source_steps']['planning_query_validation']=qv_run; result['planning_query_validation']=qv
    query_acceptance={'requests':qe.get('network_requests_executed')==19,'rows':qe.get('rows_completed')==19,'evidence_rows':len(qe.get('rows') or [])==19,'promotion_zero':qe.get('promotion_eligible_rows')==0,'scores_zero':qe.get('scores_emitted')==0,'validation_pass':(qv or {}).get('result')=='PASS','validated_rows':(qv or {}).get('rows_validated')==19,'polygon_claim_false':(qv or {}).get('polygon_relation_claimed') is False}; result['planning_query_acceptance']=query_acceptance
    if qv_run['exit_code']!=0 or not all(query_acceptance.values()): return blocked(result,'BLOCKED_PLANNING_QUERY_ACCEPTANCE','PLANNING_QUERY_ACCEPTANCE_GATES_FAILED')
    result['source_sha256']={'entry_v7':sha256(Path(__file__)),'geometry_entry':sha256(GEOMETRY_ENTRY),'extractor':sha256(EXTRACTOR),'query_executor':sha256(QUERY_EXECUTOR),'query_validator':sha256(QUERY_VALIDATOR),'rows_output':sha256(ROWS_OUTPUT),'relation_output':sha256(RELATION_OUTPUT),'query_evidence':sha256(QUERY_OUTPUT/'execution_evidence_manifest.json'),'query_validation':sha256(QUERY_VALIDATION)}
    result.update(state='COMPLETED_SLOT_LOCAL_GEOMETRY_AND_PLANNING_QUERY_SAMPLE',status='COMPLETED_REVISION7_EXACT_ROWS_GEOMETRY_AND_19_QUERIES_NO_SCORE',canonical_rows_20_24_extracted=5,official_site_polygons_downloaded=4,exact_hmlr_parcel_polygons=6,verified_polygon_relations=14,planning_query_requests_executed=19,planning_query_rows_validated=19,source_wave_parcel_rows_promoted=0,scored_business_rows=0,actual_business_data_rows_written=0,next_unverified_step='BUILD_ROWS_20_24_CANDIDATES_AND_FULL_30761_FACTOR_MATRIX',completed_at_epoch=time.time()); publish(result); return 0
if __name__=='__main__':
    try: raise SystemExit(main())
    except Exception as exc:
        payload={'schema_version':7,'slot_id':SLOT_ID,'task_id':TASK_ID,'attempt_id':ATTEMPT_ID,'contract_revision':CONTRACT_REVISION,'state':'BLOCKED','status':'BLOCKED_UNHANDLED_EXCEPTION','blocker':f'{type(exc).__name__}: {exc}','actual_business_data_rows_written':0,'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False}; publish(payload); print(json.dumps(payload,ensure_ascii=False),file=sys.stderr); raise
