#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path
HEX64=re.compile(r'^[0-9a-f]{64}$')
EXPECTED=['030','007','001','003','004','005','006']
def _sha(v):
    s=str(v or '').lower()
    if not HEX64.fullmatch(s): raise ValueError(f'invalid sha256: {v!r}')
    return s
def validate(payload:dict)->dict:
    if payload.get('slot_id')!='future_growth_2': raise ValueError('wrong slot_id')
    stages=payload.get('stages')
    if not isinstance(stages,list) or [str(x.get('stage')) for x in stages]!=EXPECTED: raise ValueError('stage order mismatch')
    seen=set();prev=None;live_ready=bool(payload.get('live_dependency_preflight_ready'));product_rows=0
    for i,s in enumerate(stages):
        stage=str(s.get('stage'));artifact=str(s.get('artifact_path') or '')
        if not artifact or artifact in seen or '..' in Path(artifact).parts or artifact.startswith('/'): raise ValueError(f'{stage}: unsafe or duplicate artifact')
        seen.add(artifact);execution_class=str(s.get('execution_class') or '')
        if execution_class not in {'LIVE_PRODUCT','OFFLINE_FIXTURE','APPROVAL_ONLY'}: raise ValueError(f'{stage}: invalid execution class')
        inp=_sha(s.get('input_sha256'));out=_sha(s.get('output_sha256'))
        if i and inp!=prev: raise ValueError(f'{stage}: broken input/output hash chain')
        prev=out;rows=int(s.get('product_rows_written') or 0);matches=int(s.get('actual_parcel_matches') or 0);scores=int(s.get('future_growth_scores_written') or 0)
        if execution_class!='LIVE_PRODUCT' and (rows or matches or scores): raise ValueError(f'{stage}: non-live stage cannot write product data')
        if execution_class=='LIVE_PRODUCT' and not live_ready and (rows or matches or scores): raise ValueError(f'{stage}: live dependency preflight not ready')
        if stage=='006':
            approved=s.get('approved_score_contract_sha256')
            if execution_class=='LIVE_PRODUCT' and not approved: raise ValueError('006: approved score contract required')
            if approved is not None: _sha(approved)
        product_rows+=rows
    claimed=int(payload.get('claimed_product_rows') or 0)
    if claimed!=product_rows: raise ValueError('claimed product rows mismatch')
    if claimed>0 and not live_ready: raise ValueError('product claim without live preflight')
    return {'schema_version':1,'slot_id':'future_growth_2','executed':True,'stage_count':len(stages),'hash_chain_valid':True,'live_dependency_preflight_ready':live_ready,'claimed_product_rows':claimed,'actual_parcel_matches':sum(int(s.get('actual_parcel_matches') or 0) for s in stages),'future_growth_scores_written':sum(int(s.get('future_growth_scores_written') or 0) for s in stages),'all_passed':True,'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();o=validate(json.loads(a.input.read_text(encoding='utf-8')));a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(o,indent=2)+'\n',encoding='utf-8');print(json.dumps(o));return 0
if __name__=='__main__': raise SystemExit(main())
