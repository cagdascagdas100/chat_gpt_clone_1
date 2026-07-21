#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path, PurePosixPath

ALLOWED=(
 'docs/chatgpt_status/_shared/slots_21/future_growth_2/',
 'docs/chatgpt_status/aays1/shards/future_growth_2/',
 'england_map_web/data/aays_21_slots/future_growth_2/',
)
HEX40=re.compile(r'^[0-9a-f]{40}$')
REQUIRED={
 'docs/chatgpt_status/_shared/slots_21/future_growth_2/checkpoint_latest.json',
 'docs/chatgpt_status/_shared/slots_21/future_growth_2/status_latest.json',
 'docs/chatgpt_status/aays1/shards/future_growth_2/next_task_contract_latest.json',
 'docs/chatgpt_status/aays1/shards/future_growth_2/port_manifest_latest.json',
 'england_map_web/data/aays_21_slots/future_growth_2/index.html',
}
def _safe_path(raw:str)->None:
 p=PurePosixPath(raw)
 if p.is_absolute() or '..' in p.parts or '\\' in raw: raise ValueError(f'unsafe path: {raw}')
 if not raw.startswith(ALLOWED): raise ValueError(f'out of scope: {raw}')
def validate(payload:dict, observed:dict|None=None)->dict:
 if payload.get('slot_id')!='future_growth_2': raise ValueError('wrong slot_id')
 if not HEX40.fullmatch(str(payload.get('source_head_sha') or '')): raise ValueError('invalid source head sha')
 if not HEX40.fullmatch(str(payload.get('target_base_sha') or '')): raise ValueError('invalid target base sha')
 rows=payload.get('files')
 if not isinstance(rows,list) or not rows: raise ValueError('files missing')
 paths=[]
 for row in rows:
  if not isinstance(row,dict): raise ValueError('file row not object')
  raw=str(row.get('path') or ''); sha=str(row.get('blob_sha') or '')
  _safe_path(raw)
  if not HEX40.fullmatch(sha): raise ValueError(f'invalid blob sha: {raw}')
  if int(row.get('bytes') or 0)<=0: raise ValueError(f'invalid byte count: {raw}')
  if not str(row.get('role') or '').strip(): raise ValueError(f'missing role: {raw}')
  paths.append(raw)
 if len(paths)!=len(set(paths)): raise ValueError('duplicate path')
 missing=sorted(REQUIRED-set(paths))
 if missing: raise ValueError('missing required: '+','.join(missing))
 checked=0
 if observed is not None:
  if not isinstance(observed,dict): raise ValueError('observed map not object')
  for row in rows:
   path=row['path']
   if path not in observed: raise ValueError(f'observed sha missing: {path}')
   if observed[path]!=row['blob_sha']: raise ValueError(f'blob mismatch: {path}')
   checked+=1
 product=payload.get('product_state') or {}
 for field in ('verified_rows','canonical_parcel_matches','future_growth_scores','actual_business_rows_written'):
  if int(product.get(field) or 0)!=0: raise ValueError(f'product state must remain zero: {field}')
 return {'schema_version':1,'slot_id':'future_growth_2','executed':True,
         'manifest_files':len(rows),'observed_exact_matches':checked,
         'all_passed':True,'port_executed':False,'merge_executed':False,
         'ref_update_executed':False,'final_ready':False,'fake_data':False,
         'db_write':False,'migration':False,'production_deploy':False}
def main()->int:
 p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True)
 p.add_argument('--observed',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 payload=json.loads(a.manifest.read_text(encoding='utf-8'))
 observed=json.loads(a.observed.read_text(encoding='utf-8')) if a.observed else None
 out=validate(payload,observed);a.output.parent.mkdir(parents=True,exist_ok=True)
 a.output.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out));return 0
if __name__=='__main__': raise SystemExit(main())
