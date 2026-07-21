#!/usr/bin/env python3
from __future__ import annotations
import copy, hashlib, importlib.util, json, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
checks=[]
def record(name,passed,detail=''):
    checks.append({'check':name,'passed':bool(passed),'detail':detail})
    if not passed: raise AssertionError(f'{name}: {detail}')
def expect_raises(name,fn,contains=None):
    try: fn()
    except Exception as e:
        ok=contains is None or contains in str(e); record(name,ok,f'{type(e).__name__}: {e}')
    else: record(name,False,'no exception')
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
m7=load('m7',ROOT/'007_validate_current_period_candidate_wave.py')
m5=load('m5',ROOT/'005_build_verified_evidence_matrix.py')
m6=load('m6',ROOT/'006_apply_approved_score_decisions.py')
base_candidate={'candidate_id':'T-1','source_entity':1001,'source_reference':'REF1','eligibility':'eligible_current','canonical_row_no':None,'canonical_parcel_id':None,'future_growth_score':None,'future_growth_confidence':0}
valid_row={'entity':1001,'dataset':'brownfield-land','reference':'REF1','quality':'authoritative','end-date':'','point':'POINT (-0.1 51.5)'}
def set_fetch(payload): m7.fetch_current=lambda entity_id,timeout: copy.deepcopy(payload)
set_fetch({'entities':[valid_row]}); r=m7.validate_candidate(copy.deepcopy(base_candidate),1); record('007_valid_current_entity',r['state']=='CURRENT_AUTHORITATIVE_ENTITY_VALIDATED')
set_fetch({'data':[valid_row]}); r=m7.validate_candidate(copy.deepcopy(base_candidate),1); record('007_data_array_supported',r['point_present'] is True)
set_fetch({'entities':[dict(valid_row,**{'end-date':'2025-01-01'})]}); expect_raises('007_historical_end_date_rejected',lambda:m7.validate_candidate(copy.deepcopy(base_candidate),1),'end_date')
set_fetch({'entities':[valid_row,valid_row]}); expect_raises('007_duplicate_current_entity_rejected',lambda:m7.validate_candidate(copy.deepcopy(base_candidate),1),'got 2')
set_fetch({'entities':[dict(valid_row,reference='OTHER')]}); expect_raises('007_reference_mismatch_rejected',lambda:m7.validate_candidate(copy.deepcopy(base_candidate),1),'reference')
set_fetch({'entities':[dict(valid_row,quality='experimental')]}); expect_raises('007_non_authoritative_rejected',lambda:m7.validate_candidate(copy.deepcopy(base_candidate),1),'quality')
set_fetch({'entities':[dict(valid_row,point='')]}); expect_raises('007_missing_point_rejected',lambda:m7.validate_candidate(copy.deepcopy(base_candidate),1),'point_missing')
set_fetch({'entities':[dict(valid_row,dataset='other')]}); expect_raises('007_wrong_dataset_rejected',lambda:m7.validate_candidate(copy.deepcopy(base_candidate),1),'dataset')
c=copy.deepcopy(base_candidate); c['canonical_parcel_id']='parcel_x'; expect_raises('007_prepopulated_parcel_rejected',lambda:m7.validate_candidate(c,1),'parcel assignment')
c=copy.deepcopy(base_candidate); c['future_growth_score']=44; expect_raises('007_prepopulated_score_rejected',lambda:m7.validate_candidate(c,1),'score/confidence')
called={'n':0}; m7.fetch_current=lambda *a,**k: called.__setitem__('n',called['n']+1); c=copy.deepcopy(base_candidate); c['eligibility']='held_conflict'; r=m7.validate_candidate(c,1); record('007_held_candidate_skipped_without_network',r['state']=='SKIPPED_NOT_ELIGIBLE' and called['n']==0)
set_fetch({'entities':[dict(valid_row,entity=9999)]}); expect_raises('007_entity_mismatch_rejected',lambda:m7.validate_candidate(copy.deepcopy(base_candidate),1),'got 0')

with tempfile.TemporaryDirectory(prefix='fg2-gates-') as td:
    td=Path(td); canonical=td/'canonical.jsonl'; candidate_file=td/'candidates.json'; crosswalk=td/'crosswalk.json'; matrix=td/'matrix.jsonl'; matrix_manifest=td/'matrix_manifest.json'
    rows=[{'row_no':n,'parcel_id':f'parcel_{n}','hmlr_inspire_id':f'inspire_{n}','local_authority_name':'Test Authority'} for n in range(m5.ROW_START,m5.ROW_END+1)]
    with canonical.open('w',encoding='utf-8') as h:
        for row in rows: h.write(json.dumps(row,separators=(',',':'))+'\n')
    candidates={'slot_id':'future_growth_2','candidates':[{'candidate_id':'C1','source_entity':2001,'source_reference':'R1','source_url':'https://www.planning.data.gov.uk/entity/2001','source_confidence':98,'eligibility':'eligible_current','canonical_row_no':None,'canonical_parcel_id':None,'future_growth_score':None,'future_growth_confidence':0},{'candidate_id':'C2','source_entity':2002,'source_reference':'R2','source_url':'https://www.planning.data.gov.uk/entity/2002','source_confidence':97,'eligibility':'held_conflict','canonical_row_no':None,'canonical_parcel_id':None,'future_growth_score':None,'future_growth_confidence':0}]}
    candidate_file.write_text(json.dumps(candidates),encoding='utf-8')
    cw_result={'state':'EXACT_IDENTITY_CROSSWALK_READY_FOR_EVIDENCE_MATRIX','candidate_id':'C1','canonical_row_no':30762,'canonical_parcel_id':'parcel_30762','hmlr_inspire_id':'inspire_30762','relation_type':'polygon_intersection','parcel_match_confidence_cap':92,'official_geojson_url':'https://www.planning.data.gov.uk/entity/2001.geojson'}
    crosswalk.write_text(json.dumps({'nearest_point_promotion_used':False,'results':[cw_result]}),encoding='utf-8')
    cmd=[sys.executable,str(ROOT/'005_build_verified_evidence_matrix.py'),'--canonical-shard-jsonl',str(canonical),'--exact-crosswalk-json',str(crosswalk),'--candidate-json',str(candidate_file),'--output-jsonl',str(matrix),'--manifest-json',str(matrix_manifest)]
    cp=subprocess.run(cmd,text=True,capture_output=True); record('005_full_30761_cli_exit_zero',cp.returncode==0,cp.stderr)
    manifest=json.loads(matrix_manifest.read_text()); record('005_manifest_row_count',manifest['matrix_rows']==30761); record('005_manifest_one_match',manifest['matched_rows']==1 and manifest['evidence_links']==1); record('005_scores_remain_null',manifest['scores_written']==0)
    with matrix.open(encoding='utf-8') as h: first=json.loads(next(h)); count=1; last=first
    with matrix.open(encoding='utf-8') as h:
        count=0
        for line in h: count+=1; last=json.loads(line)
    record('005_output_exact_row_count',count==30761); record('005_first_last_identity_preserved',first['row_no']==30762 and last['row_no']==61522); record('005_matched_row_evidence_attached',first['evidence_state'].startswith('EXACT_') and len(first['evidence'])==1); record('005_output_scores_null_zero',first['future_growth_score'] is None and first['future_growth_confidence']==0 and last['future_growth_score'] is None)
    expect_raises('005_wrong_canonical_count_rejected',lambda:m5.validate_canonical(rows[:-1]),'expected 30761')
    bad=copy.deepcopy(rows); bad[-1]['parcel_id']=bad[0]['parcel_id']; expect_raises('005_duplicate_parcel_identity_rejected',lambda:m5.validate_canonical(bad),'duplicate canonical identity')
    held_cw=td/'held_crosswalk.json'; held=dict(cw_result,candidate_id='C2'); held_cw.write_text(json.dumps({'nearest_point_promotion_used':False,'results':[held]}),encoding='utf-8')
    cp=subprocess.run([sys.executable,str(ROOT/'005_build_verified_evidence_matrix.py'),'--canonical-shard-jsonl',str(canonical),'--exact-crosswalk-json',str(held_cw),'--candidate-json',str(candidate_file),'--output-jsonl',str(td/'held_matrix'),'--manifest-json',str(td/'held_manifest')],text=True,capture_output=True); record('005_noneligible_crosswalk_rejected',cp.returncode!=0 and 'non-eligible' in cp.stderr,cp.stderr[-300:])
    dup_cw=td/'dup_crosswalk.json'; dup_cw.write_text(json.dumps({'nearest_point_promotion_used':False,'results':[cw_result,cw_result]}),encoding='utf-8')
    cp=subprocess.run([sys.executable,str(ROOT/'005_build_verified_evidence_matrix.py'),'--canonical-shard-jsonl',str(canonical),'--exact-crosswalk-json',str(dup_cw),'--candidate-json',str(candidate_file),'--output-jsonl',str(td/'dup_matrix'),'--manifest-json',str(td/'dup_manifest')],text=True,capture_output=True); record('005_duplicate_crosswalk_pair_rejected',cp.returncode!=0 and 'duplicate exact crosswalk pair' in cp.stderr,cp.stderr[-300:])
    badcap_cw=td/'badcap_crosswalk.json'; badcap=dict(cw_result,parcel_match_confidence_cap=0); badcap_cw.write_text(json.dumps({'nearest_point_promotion_used':False,'results':[badcap]}),encoding='utf-8')
    cp=subprocess.run([sys.executable,str(ROOT/'005_build_verified_evidence_matrix.py'),'--canonical-shard-jsonl',str(canonical),'--exact-crosswalk-json',str(badcap_cw),'--candidate-json',str(candidate_file),'--output-jsonl',str(td/'badcap_matrix'),'--manifest-json',str(td/'badcap_manifest')],text=True,capture_output=True); record('005_invalid_confidence_cap_rejected',cp.returncode!=0 and 'invalid parcel match confidence cap' in cp.stderr,cp.stderr[-300:])
    bad_candidate=copy.deepcopy(candidates); bad_candidate['candidates'][0]['future_growth_score']=12; bad_candidate_file=td/'bad_candidates.json'; bad_candidate_file.write_text(json.dumps(bad_candidate),encoding='utf-8')
    cp=subprocess.run([sys.executable,str(ROOT/'005_build_verified_evidence_matrix.py'),'--canonical-shard-jsonl',str(canonical),'--exact-crosswalk-json',str(crosswalk),'--candidate-json',str(bad_candidate_file),'--output-jsonl',str(td/'badcandidate_matrix'),'--manifest-json',str(td/'badcandidate_manifest')],text=True,capture_output=True); record('005_prepopulated_candidate_score_rejected',cp.returncode!=0 and 'score/confidence' in cp.stderr,cp.stderr[-300:])

    def run_score(payload,name,matrix_path=matrix):
        dec=td/f'{name}.json'; out=td/f'{name}.jsonl'; man=td/f'{name}_manifest.json'; dec.write_text(json.dumps(payload),encoding='utf-8')
        cp=subprocess.run([sys.executable,str(ROOT/'006_apply_approved_score_decisions.py'),'--verified-matrix-jsonl',str(matrix_path),'--approved-score-decisions-json',str(dec),'--output-jsonl',str(out),'--manifest-json',str(man)],text=True,capture_output=True)
        return cp,out,man
    digest=m6.evidence_digest(first)
    valid_payload={'approved':True,'contract_id':'FG-APPROVED-TEST-1','approved_by':'test-approver','approved_at':'2026-07-21T13:30:00+03:00','rows':[{'row_no':30762,'evidence_sha256':digest,'future_growth_score':72.5,'future_growth_confidence':90,'rationale':'Explicit fixture decision within exact evidence confidence cap.'}]}
    cp,out,man=run_score(valid_payload,'valid'); record('006_valid_decision_exit_zero',cp.returncode==0,cp.stderr); sm=json.loads(man.read_text()); record('006_valid_decision_applied_once',sm['score_decisions_applied']==1)
    with out.open(encoding='utf-8') as h: scored_first=json.loads(next(h))
    record('006_valid_score_and_contract_written',scored_first['future_growth_score']==72.5 and scored_first['future_growth_confidence']==90 and scored_first['scoring_contract_id']=='FG-APPROVED-TEST-1')
    p=copy.deepcopy(valid_payload); p['approved']=False; cp,_,_=run_score(p,'noapproval'); record('006_missing_approval_rejected',cp.returncode!=0 and 'approval metadata' in cp.stderr,cp.stderr[-300:])
    p=copy.deepcopy(valid_payload); p['rows'][0]['evidence_sha256']='0'*64; cp,_,_=run_score(p,'digest'); record('006_digest_mismatch_rejected',cp.returncode!=0 and 'digest mismatch' in cp.stderr,cp.stderr[-300:])
    p=copy.deepcopy(valid_payload); p['rows'][0]['future_growth_confidence']=93; cp,_,_=run_score(p,'cap'); record('006_confidence_above_cap_rejected',cp.returncode!=0 and 'exceeds evidence cap' in cp.stderr,cp.stderr[-300:])
    p=copy.deepcopy(valid_payload); p['rows'][0]['future_growth_score']=101; cp,_,_=run_score(p,'score101'); record('006_score_outside_range_rejected',cp.returncode!=0 and 'score outside' in cp.stderr,cp.stderr[-300:])
    p=copy.deepcopy(valid_payload); p['rows'][0]['row_no']=30763; p['rows'][0]['evidence_sha256']=hashlib.sha256(b'[]').hexdigest(); cp,_,_=run_score(p,'noevidence'); record('006_no_evidence_row_rejected',cp.returncode!=0 and 'no verified evidence' in cp.stderr,cp.stderr[-300:])
    p=copy.deepcopy(valid_payload); p['rows'].append(copy.deepcopy(p['rows'][0])); cp,_,_=run_score(p,'duplicate'); record('006_duplicate_decision_rejected',cp.returncode!=0 and 'duplicate score decision' in cp.stderr,cp.stderr[-300:])
    p=copy.deepcopy(valid_payload); p['rows'][0]['rationale']=''; cp,_,_=run_score(p,'norationale'); record('006_missing_rationale_rejected',cp.returncode!=0 and 'lacks rationale' in cp.stderr,cp.stderr[-300:])
    bad_matrix=td/'bad_range_matrix.jsonl'
    with matrix.open(encoding='utf-8') as src,bad_matrix.open('w',encoding='utf-8') as dst:
        for i,line in enumerate(src):
            row=json.loads(line)
            if i==0: row['row_no']=1
            dst.write(json.dumps(row,separators=(',',':'))+'\n')
    cp,_,_=run_score(valid_payload,'badrange',bad_matrix); record('006_noncontiguous_matrix_rejected',cp.returncode!=0 and ('outside shard' in cp.stderr or 'contiguous' in cp.stderr),cp.stderr[-300:])
    bad_state=td/'bad_state_matrix.jsonl'
    with matrix.open(encoding='utf-8') as src,bad_state.open('w',encoding='utf-8') as dst:
        for i,line in enumerate(src):
            row=json.loads(line)
            if i==0: row['evidence_state']='NO_VERIFIED_FUTURE_GROWTH_EVIDENCE'
            dst.write(json.dumps(row,separators=(',',':'))+'\n')
    cp,_,_=run_score(valid_payload,'badstate',bad_state); record('006_evidence_state_mismatch_rejected',cp.returncode!=0 and 'evidence state mismatch' in cp.stderr,cp.stderr[-300:])
    prescored=td/'prescored_matrix.jsonl'
    with matrix.open(encoding='utf-8') as src,prescored.open('w',encoding='utf-8') as dst:
        for i,line in enumerate(src):
            row=json.loads(line)
            if i==0: row['future_growth_score']=1
            dst.write(json.dumps(row,separators=(',',':'))+'\n')
    cp,_,_=run_score(valid_payload,'prescored',prescored); record('006_prescored_matrix_rejected',cp.returncode!=0 and 'already scored' in cp.stderr,cp.stderr[-300:])

result={'schema_version':1,'slot_id':'future_growth_2','executed':True,'test_type':'offline_actual_30761_row_current_period_matrix_and_score_gate_integration','checks_passed':sum(c['passed'] for c in checks),'checks_total':len(checks),'all_passed':all(c['passed'] for c in checks),'checks':checks,'full_matrix_rows_exercised':30761,'actual_live_period_current_responses':0,'canonical_parcel_matches':0,'future_growth_scores_produced_for_product':0,'fixture_scores_written_only':1,'actual_business_data_rows_written':0,'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False}
out=ROOT/'020_current_matrix_score_gate_integration_validation_20260721.json'; out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'ok':result['all_passed'],'passed':result['checks_passed'],'total':result['checks_total'],'output':str(out)}))
