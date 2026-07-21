#!/usr/bin/env python3
from __future__ import annotations
import argparse, importlib.util, json
from copy import deepcopy
from pathlib import Path

def load(path):
 spec=importlib.util.spec_from_file_location('scope',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def main():
 p=argparse.ArgumentParser();p.add_argument('--wave',type=Path,required=True);p.add_argument('--scope-validator',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 w=json.loads(a.wave.read_text());m=load(a.scope_validator);cs=w['candidates'];checks=[]
 def ck(name,cond): checks.append({'check':name,'passed':bool(cond)})
 ck('candidate_count_6',len(cs)==6);ck('eligible_count_6',sum(str(c['eligibility']).startswith('eligible') for c in cs)==6)
 ck('unique_ids',len({c['candidate_id'] for c in cs})==6);ck('unique_entities',len({c['source_entity'] for c in cs})==6);ck('unique_references',len({c['source_reference'] for c in cs})==6)
 ck('repo_search_no_overlap',w['repository_search_evidence']['matches_in_existing_repository']==0);ck('authoritative_all',all(c['source_quality']=='authoritative' for c in cs));ck('blank_end_all',all(not c.get('end_date') for c in cs));ck('permissioned_all',all(c.get('planning_permission_status')=='permissioned' for c in cs));ck('point_only_all',all(str(c.get('official_point_wkt') or '').startswith('POINT') for c in cs));ck('caps_65_all',all(c.get('parcel_match_confidence_cap')==65 for c in cs));ck('confidence_ge_90',all(90<=c.get('source_confidence',0)<=100 for c in cs));ck('product_fields_null',all(c.get('canonical_row_no') is None and c.get('canonical_parcel_id') is None and c.get('future_growth_score') is None and c.get('future_growth_confidence') in (0,None) for c in cs));ck('provider_no_uplift',w['provider_quality']['parcel_or_score_confidence_uplift'] is False);ck('hmlr_listed_not_downloaded',w['hmlr']['authority_listed']=='London Borough of Hackney' and w['hmlr']['actual_downloads']==0);ck('period_current_zero',w['runtime']['period_current_api_responses']==0)
 good={'slot_id':'future_growth_2','files':['docs/chatgpt_status/_shared/slots_21/future_growth_2/checkpoint_latest.json','docs/chatgpt_status/_shared/slots_21/future_growth_2/status_latest.json','docs/chatgpt_status/aays1/shards/future_growth_2/next_task_contract_latest.json','docs/chatgpt_status/aays1/shards/future_growth_2/port_manifest_latest.json','england_map_web/data/aays_21_slots/future_growth_2/index.html']}
 ck('scope_good_passes',m.validate(good)['all_passed'])
 def rejects(mut,needle):
  try:m.validate(mut);return False
  except Exception as e:return needle in str(e)
 x=deepcopy(good);x['files'].append('README.md');ck('scope_outside_rejected',rejects(x,'out of scope'))
 x=deepcopy(good);x['files'].append('../evil');ck('scope_traversal_rejected',rejects(x,'unsafe path'))
 x=deepcopy(good);x['files'].append(x['files'][0]);ck('scope_duplicate_rejected',rejects(x,'duplicate path'))
 x=deepcopy(good);x['files'].remove('england_map_web/data/aays_21_slots/future_growth_2/index.html');ck('scope_missing_required_rejected',rejects(x,'missing required'))
 x=deepcopy(good);x['slot_id']='other';ck('scope_wrong_slot_rejected',rejects(x,'wrong slot_id'))
 ck('source_urls_official',all(c['source_url'].startswith('https://www.planning.data.gov.uk/entity/') for c in cs));ck('all_safety_flags',all(w[k] is False for k in ['final_ready','fake_data','db_write','migration','production_deploy']))
 out={'schema_version':1,'slot_id':'future_growth_2','executed':True,'test_type':'wave20_registry_and_safe_port_scope','checks_passed':sum(c['passed'] for c in checks),'checks_total':len(checks),'all_passed':all(c['passed'] for c in checks),'checks':checks,'canonical_parcel_matches':0,'future_growth_scores_produced':0,'actual_business_data_rows_written':0,'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False}
 a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out));return 0 if out['all_passed'] else 1
if __name__=='__main__': raise SystemExit(main())
