#!/usr/bin/env python3
from __future__ import annotations
import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(path):
 s=importlib.util.spec_from_file_location('validator',path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
wave=json.loads((ROOT/'source_candidates/021_official_source_candidates_20260722.json').read_text())
c=wave['candidates'];eligible=[x for x in c if x['eligibility'].startswith('eligible')];held=[x for x in c if x['eligibility'].startswith('held')];hist=[x for x in c if x['eligibility'].startswith('excluded_historical')]
validator=load(ROOT/'automation/035_validate_safe_port_content_manifest.py')
good_entries=[
 {'path':'docs/chatgpt_status/_shared/slots_21/future_growth_2/checkpoint_latest.json','blob_sha':'1'*40,'role':'checkpoint'},
 {'path':'docs/chatgpt_status/_shared/slots_21/future_growth_2/status_latest.json','blob_sha':'2'*40,'role':'status'},
 {'path':'docs/chatgpt_status/aays1/shards/future_growth_2/next_task_contract_latest.json','blob_sha':'3'*40,'role':'next_task'},
 {'path':'england_map_web/data/aays_21_slots/future_growth_2/index.html','blob_sha':'4'*40,'role':'website'},
 {'path':'england_map_web/data/aays_21_slots/future_growth_2/progress_wave_21_delta.json','blob_sha':'5'*40,'role':'progress'},
 {'path':'docs/chatgpt_status/aays1/shards/future_growth_2/source_candidates/021_official_source_candidates_20260722.json','blob_sha':'6'*40,'role':'candidate_wave'},
 {'path':'docs/chatgpt_status/aays1/shards/future_growth_2/validation/058_wave_21_registry_and_content_manifest_validation_20260722.json','blob_sha':'7'*40,'role':'validation'},
 {'path':'docs/chatgpt_status/aays1/shards/future_growth_2/automation/035_validate_safe_port_content_manifest.py','blob_sha':'8'*40,'role':'automation'}]
manifest={'slot_id':'future_growth_2','entries':good_entries};observed={e['path']:e['blob_sha'] for e in good_entries}
def rejected(man,obs):
 try: validator.validate(man,obs);return False
 except ValueError:return True
checks=[]
def add(name,passed):checks.append({'check':name,'passed':bool(passed)})
add('candidate_count_6',len(c)==6);add('eligible_count_4',len(eligible)==4);add('held_count_1',len(held)==1);add('historical_count_1',len(hist)==1)
add('unique_ids',len({x['candidate_id'] for x in c})==6);add('unique_entities',len({x['source_entity'] for x in c})==6);add('unique_references',len({x['source_reference'] for x in c})==6)
add('repo_search_no_overlap',wave['repository_search_evidence']['matches_in_existing_repository']==0);add('authoritative_all',all(x['source_quality']=='authoritative' for x in c))
add('four_current_blank_end',sum(x['end_date'] is None and x['eligibility'].startswith('eligible') for x in c)==4);add('capacity_mismatch_48_vs_54',held[0]['maximum_net_dwellings']==48 and held[0]['narrative_net_dwellings']==54)
add('historical_end_2021_12_14',hist[0]['end_date']=='2021-12-14');add('point_only_all',all(x['official_point_wkt'].startswith('POINT') for x in c));add('eligible_caps_65',all(x['parcel_match_confidence_cap']==65 for x in eligible))
add('confidence_ge_90',all(x['source_confidence']>=90 for x in c));add('product_fields_null',all(x['canonical_row_no'] is None and x['canonical_parcel_id'] is None and x['future_growth_score'] is None and x['future_growth_confidence']==0 for x in c))
add('provider_no_uplift',wave['provider_quality']['parcel_or_score_confidence_uplift'] is False);add('hmlr_listed_not_downloaded',wave['hmlr']['authority_listed']=='London Borough of Islington' and wave['hmlr']['actual_downloads']==0)
add('period_current_zero',wave['runtime']['period_current_api_responses']==0);add('source_urls_official',all(x['source_url'].startswith('https://www.planning.data.gov.uk/entity/') for x in c))
add('manifest_good_passes',validator.validate(manifest,observed)['all_passed'])
badobs=dict(observed);badobs[good_entries[0]['path']]='f'*40;add('manifest_blob_mismatch_rejected',rejected(manifest,badobs))
dup={'slot_id':'future_growth_2','entries':good_entries+[dict(good_entries[0])]};add('manifest_duplicate_rejected',rejected(dup,observed))
out={'slot_id':'future_growth_2','entries':[dict(e) for e in good_entries]};out['entries'][0]['path']='README.md';add('manifest_outside_scope_rejected',rejected(out,observed))
miss={'slot_id':'future_growth_2','entries':[e for e in good_entries if e['role']!='automation']};add('manifest_missing_role_rejected',rejected(miss,observed))
badsha={'slot_id':'future_growth_2','entries':[dict(e) for e in good_entries]};badsha['entries'][0]['blob_sha']='abc';add('manifest_invalid_sha_rejected',rejected(badsha,observed))
add('all_safety_flags',all(wave[k] is False for k in ['final_ready','fake_data','db_write','migration','production_deploy']))
add('no_parcel_or_score_promotion',wave['candidate_summary']['canonical_rows_matched']==0 and wave['candidate_summary']['future_growth_scores_produced']==0)
assert len(checks)==28 and all(x['passed'] for x in checks),checks
out={'schema_version':1,'slot_id':'future_growth_2','executed':True,'test_type':'wave21_registry_and_content_manifest','checks_passed':28,'checks_total':28,'all_passed':True,'checks':checks,'canonical_parcel_matches':0,'future_growth_scores_produced':0,'actual_business_data_rows_written':0,'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False}
print(json.dumps(out))
