#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
SLOT='future_growth_2'; PART={'start':30762,'end':61522,'count':30761}; ROWS=(30762,46142,61522)
PRIOR='TRACKED_PARCEL_CANDIDATE_IDENTITY_OR_GEOMETRY_INPUT_REQUIRED_FOR_TITLE_BOUNDARY_LINKAGE'
BLOCK='EXACT_UPRN_TITLE_NUMBER_OR_GEOMETRY_BINDING_REQUIRED_FOR_TITLE_BOUNDARY_LINKAGE'
NEXT='LOCATE_TRACKED_EXACT_UPRN_TITLE_NUMBER_OR_GEOMETRY_BINDING_FOR_SAMPLE_CANDIDATES'
def load(p:Path):
 v=json.loads(p.read_text(encoding='utf-8'))
 if not isinstance(v,dict): raise ValueError(f'{p} must contain a JSON object')
 return v
def evaluate(c,p,o,key):
 part=o.get('parcel_partition',{}); rows=c.get('sample_candidates',[])
 rc=[]
 if isinstance(rows,list):
  for x in rows:
   if isinstance(x,dict):
    n=x.get('row_no'); pid=x.get('parcel_id'); rc.append({'row_no':n,'parcel_id':pid,'row_within_partition':isinstance(n,int) and PART['start']<=n<=PART['end'],'parcel_id_matches_row':isinstance(n,int) and pid==f'parcel_{n}'})
 rownos=tuple(x.get('row_no') for x in rows) if isinstance(rows,list) and all(isinstance(x,dict) for x in rows) else ()
 checks={
  'candidate_slot_matches':c.get('slot_id')==SLOT,
  'candidate_state_identity_complete':c.get('state')=='UPRN_ADDRESS_IDENTITY_COMPLETE_EXACT_BINDING_PENDING',
  'candidate_rows_cumulative_three':c.get('candidate_rows_cumulative')==3,
  'sample_candidate_count_three':isinstance(rows,list) and len(rows)==3,
  'sample_rows_match_partition_sentinels':rownos==ROWS,
  'sample_rows_valid':len(rc)==3 and all(x['row_within_partition'] and x['parcel_id_matches_row'] for x in rc),
  'exact_parcel_bound_rows_zero':c.get('exact_parcel_bound_rows')==0,
  'uprn_not_title_boundary_guard':c.get('quality_policy',{}).get('uprn_point_not_title_boundary') is True,
  'no_score_without_exact_intersection':c.get('quality_policy',{}).get('score_without_hashed_exact_intersection') is False,
  'candidate_fake_data_false':c.get('fake_data') is False,
  'prior_gate_no_data_continue':p.get('state')=='NO_DATA_CONTINUE',
  'prior_gate_blocker_matches':p.get('blocker')==PRIOR,
  'prior_gate_prerequisites_verified':p.get('linkage_prerequisites_verified') is True,
  'ownership_slot_matches':o.get('slot_id')==SLOT,
  'ownership_unclaimed':o.get('owner') is None,
  'partition_matches':{k:part.get(k) for k in ('start','end','count')}==PART,
 }
 ok=all(checks.values())
 return {'schema_version':3,'architecture_version':3,'workstream_id':'AAYS_21_SLOT_SAFE_PARALLEL_V1','slot_id':SLOT,'task_continuation_key':key,'state':'NO_DATA_CONTINUE' if ok else 'BLOCKED','panel_status':'PUBLISHED' if ok else 'BLOCKED','completed_count':1 if ok else 0,'target_count':1,'progress_percent':100.0 if ok else 0.0,'global_business_completed_count':0,'global_business_target_count':PART['count'],'global_progress_percent':0.0,'produced_business_rows':0,'linkage_rows':0,'parcel_candidate_identity_input_available':ok,'exact_uprn_title_or_geometry_binding_available':False,'validated_candidate_count':len(rc) if ok else 0,'validated_candidate_row_numbers':list(ROWS) if ok else [],'row_checks':rc,'checks':checks,'blocker':BLOCK if ok else 'SLOT_BOUNDED_PARCEL_CANDIDATE_IDENTITY_VALIDATION_FAILED','next_unverified_step':NEXT if ok else 'REPAIR_SLOT_BOUNDED_PARCEL_CANDIDATE_IDENTITY_INPUT','source_rows_persisted':False,'response_body_persisted':False,'geometry_persisted':False,'coordinates_persisted':False,'point_persisted':False,'inferred_linkage_persisted':False,'fake_data':False}
def self_test():
 c={'slot_id':SLOT,'state':'UPRN_ADDRESS_IDENTITY_COMPLETE_EXACT_BINDING_PENDING','candidate_rows_cumulative':3,'exact_parcel_bound_rows':0,'sample_candidates':[{'row_no':n,'parcel_id':f'parcel_{n}'} for n in ROWS],'quality_policy':{'uprn_point_not_title_boundary':True,'score_without_hashed_exact_intersection':False},'fake_data':False}; p={'state':'NO_DATA_CONTINUE','blocker':PRIOR,'linkage_prerequisites_verified':True}; o={'slot_id':SLOT,'owner':None,'parcel_partition':dict(PART)}
 good=evaluate(c,p,o,'x'); tests=[('identity_input_verified',good['parcel_candidate_identity_input_available'] is True),('completed_one_of_one',good['completed_count']==1 and good['progress_percent']==100.0),('three_rows_validated',good['validated_candidate_count']==3 and good['validated_candidate_row_numbers']==list(ROWS)),('exact_binding_absent',good['exact_uprn_title_or_geometry_binding_available'] is False),('exact_blocker',good['blocker']==BLOCK),('no_payload_persistence',all(good[k] is False for k in ('source_rows_persisted','response_body_persisted','geometry_persisted','coordinates_persisted','point_persisted','inferred_linkage_persisted')))]
 bad=dict(c); bad['sample_candidates']=[{'row_no':1,'parcel_id':'parcel_1'}]; tests.append(('wrong_partition_rejected',evaluate(bad,p,o,'x')['state']=='BLOCKED'))
 bp=dict(p); bp['linkage_prerequisites_verified']=False; tests.append(('bad_prior_gate_rejected',evaluate(c,bp,o,'x')['state']=='BLOCKED'))
 n=sum(bool(v) for _,v in tests); return {'tests':[{'name':k,'passed':bool(v)} for k,v in tests],'passed':n,'target':len(tests),'result':f'PASS_{n}_OF_{len(tests)}'}
def main():
 a=argparse.ArgumentParser(); a.add_argument('--candidate-input',type=Path); a.add_argument('--prior-gate',type=Path); a.add_argument('--ownership',type=Path); a.add_argument('--output',type=Path); a.add_argument('--task-continuation-key'); a.add_argument('--self-test',action='store_true'); x=a.parse_args()
 if x.self_test: print(json.dumps(self_test(),sort_keys=True,separators=(',',':'))); return 0
 req=[x.candidate_input,x.prior_gate,x.ownership,x.output,x.task_continuation_key]
 if any(v is None for v in req): a.error('candidate, prior, ownership, output and continuation key are required')
 r=evaluate(load(x.candidate_input),load(x.prior_gate),load(x.ownership),x.task_continuation_key); x.output.parent.mkdir(parents=True,exist_ok=True); x.output.write_text(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n',encoding='utf-8'); return 0
if __name__=='__main__': sys.exit(main())
