#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from typing import Any
ROW_START=30762; ROW_END=61522; ROW_COUNT=30761

def load_jsonl(path:Path)->list[dict[str,Any]]:
    rows=[]
    with path.open('r',encoding='utf-8') as h:
        for line_no,line in enumerate(h,1):
            if not line.strip(): continue
            row=json.loads(line)
            if not isinstance(row,dict): raise ValueError(f'matrix line {line_no} is not an object')
            rows.append(row)
    return rows

def evidence_digest(row:dict[str,Any])->str:
    encoded=json.dumps(row.get('evidence'),ensure_ascii=False,sort_keys=True,separators=(',',':'))
    return hashlib.sha256(encoded.encode()).hexdigest()

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--verified-matrix-jsonl',type=Path,required=True); p.add_argument('--approved-score-decisions-json',type=Path,required=True); p.add_argument('--output-jsonl',type=Path,required=True); p.add_argument('--manifest-json',type=Path,required=True); a=p.parse_args()
    matrix_rows=load_jsonl(a.verified_matrix_jsonl.resolve())
    if len(matrix_rows)!=ROW_COUNT: raise ValueError(f'expected {ROW_COUNT} matrix rows, received {len(matrix_rows)}')
    by_row={}; parcel_ids=set(); inspire_ids=set()
    for row in matrix_rows:
        row_no=int(row.get('row_no')); parcel_id=str(row.get('parcel_id') or '').strip(); inspire_id=str(row.get('hmlr_inspire_id') or '').strip()
        if not (ROW_START<=row_no<=ROW_END): raise ValueError(f'matrix row outside shard: {row_no}')
        if row_no in by_row or parcel_id in parcel_ids or inspire_id in inspire_ids: raise ValueError(f'duplicate matrix identity at row {row_no}')
        if not parcel_id or not inspire_id: raise ValueError(f'matrix row {row_no} lacks explicit identity')
        if row.get('future_growth_score') is not None or row.get('future_growth_confidence') not in (0,None): raise ValueError(f'matrix row {row_no} is already scored')
        if row.get('nearest_point_promotion_used') is not False: raise ValueError(f'matrix row {row_no} does not prove nearest matching disabled')
        evidence=row.get('evidence')
        if not isinstance(evidence,list): raise ValueError(f'matrix row {row_no} evidence is not a list')
        expected_state='EXACT_CROSSWALK_EVIDENCE_READY_FOR_APPROVED_SCORER' if evidence else 'NO_VERIFIED_FUTURE_GROWTH_EVIDENCE'
        if row.get('evidence_state')!=expected_state: raise ValueError(f'matrix row {row_no} evidence state mismatch')
        by_row[row_no]=row; parcel_ids.add(parcel_id); inspire_ids.add(inspire_id)
    if sorted(by_row)!=list(range(ROW_START,ROW_END+1)): raise ValueError('matrix rows are not exactly contiguous 30762..61522')
    decisions_payload=json.loads(a.approved_score_decisions_json.resolve().read_text(encoding='utf-8')); contract_id=str(decisions_payload.get('contract_id') or '').strip(); approved_by=str(decisions_payload.get('approved_by') or '').strip(); approved_at=str(decisions_payload.get('approved_at') or '').strip()
    if decisions_payload.get('approved') is not True or not contract_id or not approved_by or not approved_at: raise ValueError('score decisions lack explicit approval metadata')
    decisions=decisions_payload.get('rows')
    if not isinstance(decisions,list): raise ValueError('score decisions lack rows array')
    seen=set(); applied=0
    for decision in decisions:
        row_no=int(decision.get('row_no'))
        if row_no in seen: raise ValueError(f'duplicate score decision for row {row_no}')
        seen.add(row_no); row=by_row.get(row_no)
        if row is None: raise ValueError(f'score decision outside matrix row {row_no}')
        evidence=row.get('evidence')
        if row.get('evidence_state')!='EXACT_CROSSWALK_EVIDENCE_READY_FOR_APPROVED_SCORER' or not evidence: raise ValueError(f'score decision for row {row_no} has no verified evidence')
        expected=evidence_digest(row)
        if str(decision.get('evidence_sha256') or '')!=expected: raise ValueError(f'evidence digest mismatch for row {row_no}')
        score=float(decision.get('future_growth_score')); confidence=float(decision.get('future_growth_confidence'))
        if not (0.0<=score<=100.0): raise ValueError(f'score outside 0..100 for row {row_no}')
        if not (0.0<confidence<=100.0): raise ValueError(f'confidence outside 0..100 for row {row_no}')
        caps=[float(item.get('parcel_match_confidence_cap') or 0) for item in evidence]; allowed=min(caps) if caps else 0
        if confidence>allowed: raise ValueError(f'confidence {confidence} exceeds evidence cap {allowed} for row {row_no}')
        rationale=str(decision.get('rationale') or '').strip()
        if not rationale: raise ValueError(f'score decision lacks rationale for row {row_no}')
        row['future_growth_score']=round(score,3); row['future_growth_confidence']=round(confidence,3); row['scoring_contract_id']=contract_id; row['score_decision_approved_by']=approved_by; row['score_decision_approved_at']=approved_at; row['score_rationale']=rationale; applied+=1
    out=a.output_jsonl.resolve(); out.parent.mkdir(parents=True,exist_ok=True); digest=hashlib.sha256()
    with out.open('w',encoding='utf-8') as h:
        for row_no in sorted(by_row):
            encoded=json.dumps(by_row[row_no],ensure_ascii=False,separators=(',',':'))+'\n'; h.write(encoded); digest.update(encoded.encode())
    manifest={'schema_version':1,'slot_id':'future_growth_2','contract_id':contract_id,'approved_by':approved_by,'approved_at':approved_at,'matrix_rows':len(by_row),'score_decisions_applied':applied,'output_jsonl':str(out),'output_sha256':digest.hexdigest(),'nearest_point_promotion_used':False,'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False}
    mp=a.manifest_json.resolve(); mp.parent.mkdir(parents=True,exist_ok=True); mp.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'ok':True,'applied':applied,'contract_id':contract_id})); return 0
if __name__=='__main__': raise SystemExit(main())
