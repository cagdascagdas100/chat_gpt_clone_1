#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import PurePosixPath, Path
ALLOWED=(
 'docs/chatgpt_status/_shared/slots_21/future_growth_2/',
 'docs/chatgpt_status/aays1/shards/future_growth_2/',
 'england_map_web/data/aays_21_slots/future_growth_2/',
)
REQUIRED={
 'docs/chatgpt_status/_shared/slots_21/future_growth_2/checkpoint_latest.json',
 'docs/chatgpt_status/_shared/slots_21/future_growth_2/status_latest.json',
 'docs/chatgpt_status/aays1/shards/future_growth_2/next_task_contract_latest.json',
 'docs/chatgpt_status/aays1/shards/future_growth_2/port_manifest_latest.json',
 'england_map_web/data/aays_21_slots/future_growth_2/index.html',
}
def validate(payload:dict)->dict:
 if payload.get('slot_id')!='future_growth_2': raise ValueError('wrong slot_id')
 files=payload.get('files')
 if not isinstance(files,list) or not files: raise ValueError('files missing')
 if len(files)!=len(set(files)): raise ValueError('duplicate path')
 for raw in files:
  if not isinstance(raw,str) or not raw: raise ValueError('invalid path')
  p=PurePosixPath(raw)
  if p.is_absolute() or '..' in p.parts or '\\' in raw: raise ValueError(f'unsafe path: {raw}')
  if not raw.startswith(ALLOWED): raise ValueError(f'out of scope: {raw}')
 missing=sorted(REQUIRED-set(files))
 if missing: raise ValueError('missing required: '+','.join(missing))
 counts={root:sum(x.startswith(root) for x in files) for root in ALLOWED}
 return {'schema_version':1,'slot_id':'future_growth_2','executed':True,'changed_files':len(files),'allowed_files':len(files),'out_of_scope_files':0,'duplicate_files':0,'counts_by_root':counts,'all_passed':True,'merge_executed':False,'ref_update_executed':False,'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False}
def main()->int:
 p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=validate(json.loads(a.input.read_text(encoding='utf-8')));a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out));return 0
if __name__=='__main__': raise SystemExit(main())
