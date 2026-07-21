#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, json, sys
from pathlib import Path
def load(path:Path):
 s=importlib.util.spec_from_file_location('guard',path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main()->int:
 base=Path(__file__).resolve().parent
 guard=load(base/'035_validate_port_blob_manifest.py')
 wave=json.loads((base/'wave21_fixture.json').read_text())
 checks=[]
 def ok(name,value): checks.append({'check':name,'passed':bool(value)})
 rows=wave['candidates']; eligible=[x for x in rows if x['eligibility'].startswith('eligible')]
 hist=[x for x in rows if x['eligibility'].startswith('excluded')]
 ok('candidate_count_6',len(rows)==6);ok('eligible_count_3',len(eligible)==3);ok('historical_count_3',len(hist)==3)
 ok('unique_ids',len({x['candidate_id'] for x in rows})==6)
 ok('unique_entities',len({x['source_entity'] for x in rows})==6)
 ok('unique_references',len({x['source_reference'] for x in rows})==6)
 ok('repository_no_overlap',wave['repository_search_evidence']['matches_in_existing_repository']==0)
 ok('authoritative_all',all(x['source_quality']=='authoritative' for x in rows))
 ok('eligible_blank_end',all(x['end_date'] is None for x in eligible))
 ok('historical_end_present',all(x['end_date'] for x in hist))
 ok('eligible_point_only',all(x['geometry_role']=='point_only_candidate_locator_not_site_boundary' for x in eligible))
 ok('eligible_cap_65',all(x['parcel_match_confidence_cap']==65 for x in eligible))
 ok('historical_cap_zero',all(x['parcel_match_confidence_cap']==0 for x in hist))
 ok('confidence_ge_90',all(x['source_confidence']>=90 for x in rows))
 ok('product_fields_null',all(x['canonical_row_no'] is None and x['canonical_parcel_id'] is None and x['future_growth_score'] is None and x['future_growth_confidence']==0 for x in rows))
 ok('provider_no_uplift',wave['provider_quality']['parcel_or_score_confidence_uplift'] is False)
 ok('provider_five_errors',wave['provider_quality']['url_access_errors']==5)
 ok('brownfield_not_submitted',wave['provider_quality']['brownfield_status']=='endpoint_not_submitted')
 ok('hmlr_listed_not_downloaded',wave['hmlr']['actual_downloads']==0 and bool(wave['hmlr']['authority_listed']))
 ok('period_current_zero',wave['runtime']['period_current_api_responses']==0)
 files=[
 {'path':'docs/chatgpt_status/_shared/slots_21/future_growth_2/checkpoint_latest.json','blob_sha':'a'*40,'bytes':10,'role':'checkpoint'},
 {'path':'docs/chatgpt_status/_shared/slots_21/future_growth_2/status_latest.json','blob_sha':'b'*40,'bytes':10,'role':'status'},
 {'path':'docs/chatgpt_status/aays1/shards/future_growth_2/next_task_contract_latest.json','blob_sha':'c'*40,'bytes':10,'role':'runner contract'},
 {'path':'docs/chatgpt_status/aays1/shards/future_growth_2/port_manifest_latest.json','blob_sha':'d'*40,'bytes':10,'role':'scope manifest'},
 {'path':'england_map_web/data/aays_21_slots/future_growth_2/index.html','blob_sha':'e'*40,'bytes':10,'role':'website'},
 ]
 manifest={'slot_id':'future_growth_2','source_head_sha':'f'*40,'target_base_sha':'1'*40,'files':files,
 'product_state':{'verified_rows':0,'canonical_parcel_matches':0,'future_growth_scores':0,'actual_business_rows_written':0}}
 observed={x['path']:x['blob_sha'] for x in files}
 result=guard.validate(manifest,observed)
 ok('blob_manifest_good_passes',result['all_passed'] and result['observed_exact_matches']==5)
 for name,mut in [
  ('blob_bad_sha_rejected',lambda p:p['files'][0].update(blob_sha='xyz')),
  ('blob_mismatch_rejected',lambda p:p.update(_observed={**observed,files[0]['path']:'9'*40})),
  ('blob_duplicate_rejected',lambda p:p['files'].append(dict(p['files'][0]))),
  ('blob_outside_rejected',lambda p:p['files'][0].update(path='docs/other/file.json')),
  ('blob_traversal_rejected',lambda p:p['files'][0].update(path='docs/chatgpt_status/aays1/shards/future_growth_2/../x')),
  ('blob_missing_required_rejected',lambda p:p['files'].pop()),
  ('blob_product_nonzero_rejected',lambda p:p['product_state'].update(verified_rows=1)),
 ]:
  p=json.loads(json.dumps(manifest)); obs=observed
  try:
   mut(p);obs=p.pop('_observed',observed);guard.validate(p,obs);passed=False
  except Exception: passed=True
  ok(name,passed)
 ok('all_safety_flags',all(wave[k] is False for k in ('final_ready','fake_data','db_write','migration','production_deploy')))
 passed=sum(x['passed'] for x in checks)
 out={'schema_version':1,'slot_id':'future_growth_2','executed':True,'test_type':'wave21_registry_and_blob_manifest_integrity',
      'checks_passed':passed,'checks_total':len(checks),'all_passed':passed==len(checks),'checks':checks,
      'canonical_parcel_matches':0,'future_growth_scores_produced':0,'actual_business_data_rows_written':0,
      'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False}
 print(json.dumps(out));return 0 if out['all_passed'] else 1
if __name__=='__main__': raise SystemExit(main())
