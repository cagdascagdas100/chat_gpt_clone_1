#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from urllib.parse import urlparse
ALLOWED_HOST='www.planning.data.gov.uk'
def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('--wave',type=Path,required=True); p.add_argument('--output',type=Path,required=True); a=p.parse_args()
    payload=json.loads(a.wave.read_text(encoding='utf-8')); candidates=payload.get('candidates')
    if not isinstance(candidates,list) or not candidates: raise ValueError('candidate array missing or empty')
    checks=[]
    def rec(name,passed,detail): checks.append({'check':name,'passed':bool(passed),'detail':detail})
    ids=[str(c.get('candidate_id') or '') for c in candidates]; entities=[int(c['source_entity']) for c in candidates]; refs=[str(c.get('source_reference') or '').strip() for c in candidates]
    summary=payload.get('candidate_summary') or {}; repo=payload.get('repository_search_evidence') or {}
    rec('candidate_count_matches_summary',len(candidates)==summary.get('researched'),f'{len(candidates)} candidates')
    rec('eligible_count_matches_summary',sum(str(c.get('eligibility','')).startswith('eligible') for c in candidates)==summary.get('eligible'),'eligible count checked')
    rec('candidate_ids_unique',len(ids)==len(set(ids)),f'{len(set(ids))}/{len(ids)} unique')
    rec('source_entities_unique',len(entities)==len(set(entities)),f'{len(set(entities))}/{len(entities)} unique')
    rec('source_references_unique',len(refs)==len(set(refs)),f'{len(set(refs))}/{len(refs)} unique')
    rec('repository_exact_search_no_overlap',repo.get('checked') is True and repo.get('matches_in_existing_repository')==0,'six exact GitHub searches returned no existing match')
    rec('official_source_domain',all(urlparse(c['source_url']).hostname==ALLOWED_HOST for c in candidates),ALLOWED_HOST)
    rec('authoritative_quality',all(c.get('source_quality')=='authoritative' for c in candidates),'all authoritative')
    rec('current_end_date_empty',all(c.get('end_date') in (None,'') for c in candidates),'all end dates empty')
    rec('coordinates_present',all(isinstance(c.get('longitude'),(int,float)) and isinstance(c.get('latitude'),(int,float)) for c in candidates),'all points present')
    rec('fail_closed_product_fields',all(c.get('canonical_row_no') is None and c.get('canonical_parcel_id') is None and c.get('future_growth_score') is None and c.get('future_growth_confidence')==0 for c in candidates),'product fields null/zero')
    rec('source_confidence_threshold',all(90<=int(c.get('source_confidence',-1))<=100 for c in candidates),'all 90..100')
    passed=sum(x['passed'] for x in checks); result={'schema_version':1,'slot_id':'future_growth_2','wave_id':payload.get('wave_id'),'executed':True,'test_type':'actual_wave_registry_and_repository_exact_search_validation','checks_passed':passed,'checks_total':len(checks),'all_passed':passed==len(checks),'checks':checks,'canonical_parcel_matches':0,'future_growth_scores_produced':0,'actual_business_data_rows_written':0,'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps({'passed':passed,'total':len(checks),'all_passed':result['all_passed']})); return 0 if result['all_passed'] else 2
if __name__=='__main__': raise SystemExit(main())
