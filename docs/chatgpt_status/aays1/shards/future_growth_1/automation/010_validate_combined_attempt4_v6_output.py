#!/usr/bin/env python3
"""Fail-closed validator for future_growth_1 attempt-4 revision-6 output."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from typing import Any

EXPECTED_ROWS=[20,21,22,23,24]
EXPECTED_SHA='8afd1d2bac414cf0f6b9484014e7878a4ceff877'
class ContractError(RuntimeError): pass

def read(path:Path)->dict[str,Any]:
 if not path.is_file(): raise ContractError(f'missing file: {path}')
 v=json.loads(path.read_text(encoding='utf-8-sig'))
 if not isinstance(v,dict): raise ContractError(f'not object: {path}')
 return v

def sha(path:Path)->str:
 h=hashlib.sha256()
 with path.open('rb') as f:
  for c in iter(lambda:f.read(1<<20),b''): h.update(c)
 return h.hexdigest()

def validate(status_path:Path,rows_path:Path,relation_path:Path,evidence_path:Path,query_validation_path:Path)->dict[str,Any]:
 s=read(status_path); rows=read(rows_path); rel=read(relation_path); ev=read(evidence_path); qv=read(query_validation_path)
 rr=rows.get('rows') or []; counts=rel.get('counts') or {}; gates=rel.get('quality_gates') or {}
 checks={
 'task_id':s.get('task_id')=='aays1-future-growth-1-official-geometry-pipeline-20260721',
 'attempt_id':s.get('attempt_id')=='future-growth-1-20260721-004',
 'revision':s.get('contract_revision')==6,
 'state':s.get('state')=='COMPLETED_ROWS_20_24_GEOMETRY_AND_PLANNING_QUERY_SAMPLE',
 'rows_count':len(rr)==5,
 'row_numbers':[r.get('row_no') for r in rr]==EXPECTED_ROWS,
 'parcel_ids':[r.get('parcel_id') for r in rr]==[f'parcel_{i}' for i in EXPECTED_ROWS],
 'unique_hmlr':len({r.get('hmlr_inspire_id') for r in rr})==5,
 'canonical_sha':rows.get('canonical_sha256')==EXPECTED_SHA,
 'nearest_row_false':rows.get('nearest_row_fallback_used') is False,
 'gla_polygons':counts.get('current_gla_site_polygons')==4,
 'hmlr_polygons':counts.get('exact_hmlr_parcel_polygons')==6,
 'relations':counts.get('current_polygon_relations_verified')==14,
 'stale_rejection':counts.get('stale_or_completed_rejections')==1,
 'nearest_polygon_false':gates.get('nearest_polygon_fill_used') is False,
 'point_promotion_false':gates.get('point_only_promotion_used') is False,
 'requests':ev.get('network_requests_executed')==19,
 'rows_completed':ev.get('rows_completed')==19,
 'evidence_rows':len(ev.get('rows') or [])==19,
 'response_hashes':all(isinstance(x.get('sha256'),str) and len(x.get('sha256'))==64 for x in (ev.get('rows') or [])),
 'query_validation':qv.get('result')=='PASS' and qv.get('rows_validated')==19,
 'promotion_zero':ev.get('promotion_eligible_rows')==0 and s.get('source_wave_parcel_rows_promoted')==0,
 'scores_zero':ev.get('scores_emitted')==0 and qv.get('scores_emitted')==0 and s.get('scored_business_rows')==0,
 'business_zero':s.get('actual_business_data_rows_written')==0,
 'final_false':s.get('final_ready') is False,
 }
 failed=[k for k,v in checks.items() if v is not True]
 if failed: raise ContractError('failed checks: '+','.join(failed))
 return {'schema_version':1,'slot_id':'future_growth_1','result':'PASS','checks_passed':len(checks),'checks_total':len(checks),'source_sha256':{'status':sha(status_path),'rows':sha(rows_path),'relations':sha(relation_path),'query_evidence':sha(evidence_path),'query_validation':sha(query_validation_path)},'canonical_rows_extracted':5,'official_site_polygons':4,'exact_hmlr_polygons':6,'verified_relations':14,'planning_query_rows':19,'promoted_rows':0,'scores':0,'business_rows':0,'final_ready':False}

def main()->int:
 p=argparse.ArgumentParser(); p.add_argument('status',type=Path); p.add_argument('rows',type=Path); p.add_argument('relations',type=Path); p.add_argument('query_evidence',type=Path); p.add_argument('query_validation',type=Path); p.add_argument('output',type=Path); a=p.parse_args()
 try:r=validate(a.status,a.rows,a.relations,a.query_evidence,a.query_validation)
 except ContractError as e: print(json.dumps({'result':'BLOCKED','error':str(e)})); return 2
 a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(r,indent=2)+'\n'); print(json.dumps({'result':'PASS','checks':r['checks_total']})); return 0
if __name__=='__main__': raise SystemExit(main())
