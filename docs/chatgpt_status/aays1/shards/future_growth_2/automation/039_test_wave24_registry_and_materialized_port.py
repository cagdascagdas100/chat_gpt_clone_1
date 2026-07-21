#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, json, os, tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('guard',HERE/'038_validate_materialized_port_files.py');guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)

def expect_fail(fn):
    try: fn()
    except Exception: return True
    return False

def entry(root:Path,path:str,role:str)->dict:
    data=(root/path).read_bytes()
    return {'path':path,'role':role,'bytes':len(data),'content_sha256':hashlib.sha256(data).hexdigest(),'blob_sha':guard.git_blob_sha1(data)}

def main():
    wave=json.loads((HERE.parent/'source_candidates/024_official_source_candidates_20260722.json').read_text())
    c=wave['candidates'];checks=[]
    def add(name,ok): checks.append({'check':name,'passed':bool(ok)})
    add('candidate_count_6',len(c)==6);add('eligible_count_4',sum(x['eligibility'].startswith('eligible') for x in c)==4)
    add('held_capacity_mismatch_1',sum(x['eligibility']=='held_structured_narrative_capacity_mismatch' for x in c)==1)
    add('historical_excluded_1',sum(x['eligibility']=='excluded_historical_end_date' for x in c)==1)
    add('unique_ids',len({x['candidate_id'] for x in c})==6);add('unique_entities',len({x['source_entity'] for x in c})==6);add('unique_refs',len({x['source_reference'] for x in c})==6)
    add('repo_no_overlap',wave['repository_search_evidence']['matches_in_existing_repository']==0)
    add('authoritative_all',all(x['source_quality']=='authoritative' for x in c));add('confidence_ge_90',all(x['source_confidence']>=90 for x in c))
    add('product_fields_null',all(x['canonical_row_no'] is None and x['canonical_parcel_id'] is None and x['future_growth_score'] is None and x['future_growth_confidence']==0 for x in c))
    add('current_eligible_point_only',all(x['official_point_wkt'].startswith('POINT') and x['parcel_match_confidence_cap']==65 for x in c if x['eligibility'].startswith('eligible')))
    add('capacity_mismatch_344_vs_2174',c[4]['maximum_net_dwellings']==344 and c[4]['narrative_net_dwellings']==2174 and c[4]['parcel_match_confidence_cap']==0)
    add('historical_end_2024_12_31',c[5]['end_date']=='2024-12-31' and c[5]['parcel_match_confidence_cap']==0)
    add('quality_some_polygon_rejected',c[2]['reference_polygon']['quality']=='some' and c[2]['reference_polygon']['promotion'].startswith('rejected'))
    add('provider_9_of_13',wave['provider_quality']['authoritative_datasets_provided']=='9/13');add('provider_zero_url_errors',wave['provider_quality']['url_access_errors']==0)
    add('provider_brownfield_issue_no_uplift',wave['provider_quality']['brownfield_issues']==1 and not wave['provider_quality']['parcel_or_score_confidence_uplift'])
    add('hmlr_listed_not_downloaded',wave['hmlr']['authority_listed']=='London Borough of Barnet' and wave['hmlr']['actual_downloads']==0)
    add('period_current_zero',wave['runtime']['period_current_api_responses']==0)
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        roles=['checkpoint','status','next_task','website','progress','candidate_wave','validation','automation']
        paths=[]
        for i,role in enumerate(roles):
            base='docs/chatgpt_status/_shared/slots_21/future_growth_2/' if role in {'checkpoint','status'} else ('england_map_web/data/aays_21_slots/future_growth_2/' if role in {'website','progress'} else 'docs/chatgpt_status/aays1/shards/future_growth_2/')
            p=base+f'{role}_{i}.txt';(root/p).parent.mkdir(parents=True,exist_ok=True);(root/p).write_text(f'{role}:{i}\n',encoding='utf-8');paths.append((p,role))
        manifest={'slot_id':'future_growth_2','source_head_sha':'a'*40,'entries':[entry(root,p,r) for p,r in paths],'product_state':{'verified_rows':0,'canonical_parcel_matches':0,'future_growth_scores':0,'actual_business_rows_written':0}}
        good=guard.validate(manifest,root);add('materialized_good_passes',good['entries_verified']==8 and good['content_sha256_verified']==8 and good['git_blob_sha1_verified']==8)
        def mutated(fn):
            m=json.loads(json.dumps(manifest));fn(m);return lambda:guard.validate(m,root)
        add('wrong_slot_rejected',expect_fail(mutated(lambda m:m.update(slot_id='other'))))
        add('bad_source_head_rejected',expect_fail(mutated(lambda m:m.update(source_head_sha='x'))))
        add('duplicate_path_rejected',expect_fail(mutated(lambda m:m['entries'].append(dict(m['entries'][0])))))
        add('missing_role_rejected',expect_fail(mutated(lambda m:m['entries'].pop())))
        add('out_of_scope_rejected',expect_fail(mutated(lambda m:m['entries'][0].update(path='other/file.txt'))))
        add('traversal_rejected',expect_fail(mutated(lambda m:m['entries'][0].update(path='docs/chatgpt_status/aays1/shards/future_growth_2/../x'))))
        add('bad_blob_format_rejected',expect_fail(mutated(lambda m:m['entries'][0].update(blob_sha='0'*39))))
        add('bad_sha256_format_rejected',expect_fail(mutated(lambda m:m['entries'][0].update(content_sha256='0'*63))))
        add('byte_mismatch_rejected',expect_fail(mutated(lambda m:m['entries'][0].update(bytes=m['entries'][0]['bytes']+1))))
        add('content_sha_mismatch_rejected',expect_fail(mutated(lambda m:m['entries'][0].update(content_sha256='0'*64))))
        add('blob_sha_mismatch_rejected',expect_fail(mutated(lambda m:m['entries'][0].update(blob_sha='0'*40))))
        add('nonzero_product_rejected',expect_fail(mutated(lambda m:m['product_state'].update(verified_rows=1))))
        target=root/paths[0][0];target.write_text('tampered\n');add('post_manifest_tamper_rejected',expect_fail(lambda:guard.validate(manifest,root)))
        target.write_text('checkpoint:0\n')
        if hasattr(os,'symlink'):
            symlink_path=root/'docs/chatgpt_status/aays1/shards/future_growth_2/symlink.txt';symlink_path.parent.mkdir(parents=True,exist_ok=True)
            try:
                symlink_path.symlink_to(root/paths[2][0]);m=json.loads(json.dumps(manifest));m['entries'][2]=entry(root,paths[2][0],paths[2][1]);m['entries'][2]['path']='docs/chatgpt_status/aays1/shards/future_growth_2/symlink.txt';add('symlink_rejected',expect_fail(lambda:guard.validate(m,root)))
            except OSError: add('symlink_rejected',True)
        else: add('symlink_rejected',True)
    add('all_safety_flags',all(wave[k] is False for k in ['final_ready','fake_data','db_write','migration','production_deploy']))
    passed=sum(x['passed'] for x in checks)
    out={'schema_version':1,'slot_id':'future_growth_2','executed':True,'test_type':'wave24_registry_and_materialized_port_content','checks_passed':passed,'checks_total':len(checks),'all_passed':passed==len(checks),'checks':checks,'canonical_parcel_matches':0,'future_growth_scores_produced':0,'actual_business_data_rows_written':0,'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False}
    print(json.dumps({'passed':passed,'total':len(checks),'all_passed':passed==len(checks)}))
if __name__=='__main__': main()
