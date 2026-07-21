#!/usr/bin/env python3
"""Fail-closed validator for official candidate rows derived from exact rows 20-24."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

EXPECTED_ROWS=[20,21,22,23,24]
EXPECTED_SHA='8afd1d2bac414cf0f6b9484014e7878a4ceff877'
ALLOWED={
 'planning_data_api':{'www.planning.data.gov.uk'},
 'planning_brownfield':{'www.planning.data.gov.uk','gis.london.gov.uk'},
 'planning_conservation':{'www.planning.data.gov.uk'},
 'planning_listed_building':{'www.planning.data.gov.uk'},
 'planning_green_belt':{'www.planning.data.gov.uk'},
 'ea_flood_zones_cc':{'environment.data.gov.uk','www.data.gov.uk'},
}
RELATIONS={'intersects','within','covered_by','covers'}
class ContractError(RuntimeError): pass

def read(path:Path)->dict[str,Any]:
 if not path.is_file(): raise ContractError(f'missing file: {path}')
 value=json.loads(path.read_text(encoding='utf-8-sig'))
 if not isinstance(value,dict): raise ContractError(f'not object: {path}')
 return value

def is_sha(v:Any)->bool: return isinstance(v,str) and len(v)==64 and all(c in '0123456789abcdef' for c in v.lower())

def validate(rows_path:Path,candidate_path:Path)->dict[str,Any]:
 source=read(rows_path); candidate=read(candidate_path)
 rows=source.get('rows') or []
 if source.get('canonical_sha256')!=EXPECTED_SHA: raise ContractError('canonical SHA mismatch')
 if [r.get('row_no') for r in rows]!=EXPECTED_ROWS: raise ContractError('exact row sequence mismatch')
 if [r.get('parcel_id') for r in rows]!=[f'parcel_{i}' for i in EXPECTED_ROWS]: raise ContractError('parcel identity mismatch')
 if len({r.get('hmlr_inspire_id') for r in rows})!=5: raise ContractError('HMLR identities not unique')
 if source.get('nearest_row_fallback_used') is not False: raise ContractError('nearest-row fallback forbidden')
 identity={r['row_no']:r for r in rows}
 entries=candidate.get('candidates')
 if not isinstance(entries,list): raise ContractError('candidates must be list')
 seen=set(); by_row={r:0 for r in EXPECTED_ROWS}; source_counts={k:0 for k in ALLOWED}
 for i,e in enumerate(entries,1):
  if not isinstance(e,dict): raise ContractError(f'candidate {i}: not object')
  rn=e.get('row_no')
  if rn not in identity: raise ContractError(f'candidate {i}: row outside exact scope')
  canonical=identity[rn]
  if e.get('parcel_id')!=canonical.get('parcel_id') or str(e.get('hmlr_inspire_id'))!=str(canonical.get('hmlr_inspire_id')): raise ContractError(f'candidate {i}: canonical identity mismatch')
  source_key=e.get('source_key')
  if source_key not in ALLOWED: raise ContractError(f'candidate {i}: source not allowed')
  url=e.get('source_url'); parsed=urlparse(url if isinstance(url,str) else '')
  if parsed.scheme!='https' or parsed.hostname not in ALLOWED[source_key]: raise ContractError(f'candidate {i}: non-official source URL')
  reference=e.get('source_reference')
  if not isinstance(reference,str) or not reference.strip(): raise ContractError(f'candidate {i}: source reference missing')
  key=(rn,source_key,reference.strip())
  if key in seen: raise ContractError(f'candidate {i}: duplicate candidate')
  seen.add(key)
  if e.get('source_current') is not True: raise ContractError(f'candidate {i}: source is not current')
  if e.get('verified_polygon_relation') not in RELATIONS: raise ContractError(f'candidate {i}: relation not verified')
  if not is_sha(e.get('hmlr_polygon_sha256')) or not is_sha(e.get('source_geometry_sha256')): raise ContractError(f'candidate {i}: geometry SHA missing')
  evidence=e.get('relation_evidence_path')
  if not isinstance(evidence,str) or not evidence.strip(): raise ContractError(f'candidate {i}: relation evidence missing')
  if e.get('nearest_or_fuzzy_match_used') is not False: raise ContractError(f'candidate {i}: nearest/fuzzy match forbidden')
  if e.get('point_only_promotion_used') is not False: raise ContractError(f'candidate {i}: point-only promotion forbidden')
  if e.get('promotion_eligible') is not False: raise ContractError(f'candidate {i}: promotion must remain false')
  if e.get('score') is not None: raise ContractError(f'candidate {i}: score must be null')
  by_row[rn]+=1; source_counts[source_key]+=1
 return {'schema_version':1,'slot_id':'future_growth_1','result':'PASS','canonical_rows_validated':5,'candidate_rows_validated':len(entries),'candidate_rows_by_row':by_row,'candidate_rows_by_source':source_counts,'candidate_rows_promoted':0,'scores_emitted':0,'actual_business_data_rows_written':0,'final_ready':False}

def main()->int:
 p=argparse.ArgumentParser(); p.add_argument('rows',type=Path); p.add_argument('candidates',type=Path); p.add_argument('output',type=Path); a=p.parse_args()
 try:r=validate(a.rows,a.candidates)
 except ContractError as e: print(json.dumps({'result':'BLOCKED','error':str(e)})); return 2
 a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(r,indent=2)+'\n'); print(json.dumps({'result':'PASS','candidates':r['candidate_rows_validated']})); return 0
if __name__=='__main__': raise SystemExit(main())
