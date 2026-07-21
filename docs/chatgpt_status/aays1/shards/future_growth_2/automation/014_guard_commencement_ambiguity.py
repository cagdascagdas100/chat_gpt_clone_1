#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

def validate(payload:dict)->dict:
    if payload.get('slot_id')!='future_growth_2': raise ValueError('wrong slot_id')
    candidates=payload.get('candidates')
    if not isinstance(candidates,list) or not candidates: raise ValueError('candidate array missing')
    flagged=[]
    for c in candidates:
        if not c.get('commencement_signal'): continue
        cid=str(c.get('candidate_id') or '')
        eligibility=str(c.get('eligibility') or '')
        if not (eligibility.startswith('held') or eligibility.startswith('excluded')):
            raise ValueError(f'{cid}: commencement ambiguity must be held or excluded')
        if c.get('canonical_row_no') is not None or c.get('canonical_parcel_id') is not None:
            raise ValueError(f'{cid}: parcel promotion forbidden for commencement ambiguity')
        if c.get('future_growth_score') is not None or c.get('future_growth_confidence') not in (0,None):
            raise ValueError(f'{cid}: score promotion forbidden for commencement ambiguity')
        if not str(c.get('commencement_evidence') or '').strip():
            raise ValueError(f'{cid}: commencement evidence missing')
        flagged.append(cid)
    return {'slot_id':'future_growth_2','flagged_candidates':flagged,'flagged_count':len(flagged),'parcel_promotions':0,'score_promotions':0,'final_ready':False}

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--wave',type=Path,required=True); p.add_argument('--output',type=Path,required=True); a=p.parse_args()
    result=validate(json.loads(a.wave.read_text(encoding='utf-8'))); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps(result)); return 0
if __name__=='__main__': raise SystemExit(main())
