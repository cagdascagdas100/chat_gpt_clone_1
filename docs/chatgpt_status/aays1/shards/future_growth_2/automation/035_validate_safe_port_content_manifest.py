#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import PurePosixPath, Path
ALLOWED=(
 'docs/chatgpt_status/_shared/slots_21/future_growth_2/',
 'docs/chatgpt_status/aays1/shards/future_growth_2/',
 'england_map_web/data/aays_21_slots/future_growth_2/',
)
HEX40=re.compile(r'^[0-9a-f]{40}$')
REQUIRED_ROLES={'checkpoint','status','next_task','website','progress','candidate_wave','validation','automation'}
def validate(manifest:dict, observed:dict[str,str])->dict:
 if manifest.get('slot_id')!='future_growth_2': raise ValueError('wrong slot_id')
 entries=manifest.get('entries')
 if not isinstance(entries,list) or not entries: raise ValueError('entries missing')
 paths=[]; roles=[]
 for entry in entries:
  if not isinstance(entry,dict): raise ValueError('entry must be object')
  path=entry.get('path'); sha=entry.get('blob_sha'); role=entry.get('role')
  if not isinstance(path,str) or not path: raise ValueError('path missing')
  p=PurePosixPath(path)
  if p.is_absolute() or '..' in p.parts or '\\' in path or not path.startswith(ALLOWED): raise ValueError(f'unsafe path: {path}')
  if not isinstance(sha,str) or not HEX40.fullmatch(sha): raise ValueError(f'invalid sha: {path}')
  if observed.get(path)!=sha: raise ValueError(f'blob mismatch: {path}')
  if not isinstance(role,str) or not role: raise ValueError(f'role missing: {path}')
  paths.append(path);roles.append(role)
 if len(paths)!=len(set(paths)): raise ValueError('duplicate path')
 missing=sorted(REQUIRED_ROLES-set(roles))
 if missing: raise ValueError('missing roles: '+','.join(missing))
 return {'schema_version':1,'slot_id':'future_growth_2','executed':True,'entries_verified':len(entries),'required_roles_verified':len(REQUIRED_ROLES),'mismatches':0,'out_of_scope':0,'duplicates':0,'all_passed':True,'merge_executed':False,'ref_update_executed':False,'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False}
def main()->int:
 p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True);p.add_argument('--observed',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=validate(json.loads(a.manifest.read_text()),json.loads(a.observed.read_text()));a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out));return 0
if __name__=='__main__': raise SystemExit(main())
