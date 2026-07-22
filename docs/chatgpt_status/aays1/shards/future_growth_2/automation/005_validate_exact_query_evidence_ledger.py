#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from urllib.parse import urlparse
ALLOWED={"github.com","services.arcgis.com","gis2.london.gov.uk","gis.lambeth.gov.uk","www.planning.data.gov.uk","www.london.gov.uk","consult.london.gov.uk","www.enfield.gov.uk","www.havering.gov.uk","democracy.havering.gov.uk","www.lambeth.gov.uk"}
def count_ops(d):
 return (len(d['rows']) + sum(len(r['layers']) for r in d['rows']) + len(d['rows'])*len(d['planning_datasets']) + len(d['rows'])*2 + len(d['rows'])*len(d['response_preconditions']) + len(d['current_sources']) + len(d['national_dataset_status']) + len(d['scoring_gates']) + len(d['crosschecks']) + len(d['system_validations']))
def collect_urls(d):
 urls=[]
 for r in d['rows']: urls.append(r['service'])
 urls += [x['source'] for x in d['current_sources']]
 urls += [x['source'] for x in d['national_dataset_status']]
 urls += [x['source'] for x in d['crosschecks']]
 return urls
def main():
 p=argparse.ArgumentParser();p.add_argument('batch',type=Path);p.add_argument('--results',type=Path);a=p.parse_args();d=json.loads(a.batch.read_text())
 checks={'operation_count':count_ops(d)==d['batch_operations_total']==180,'query_jobs':sum(len(r['layers']) for r in d['rows'])+len(d['rows'])*len(d['planning_datasets'])+len(d['rows'])*2==60,'allowlist':all(urlparse(u).hostname in ALLOWED for u in collect_urls(d)),'score_guard':d['exact_parcel_bound_rows']==0 and d['scored_business_rows']==0,'future_status_separation':d['quality_policy']['draft_emerging_proposed_adopted_distinct'] is True}
 result={'batch_checks':checks,'batch_pass':all(checks.values()),'operations':count_ops(d),'result_file':None}
 if a.results:
  raw=a.results.read_bytes();r=json.loads(raw);entries=r.get('results',[])
  rc={'sha256':hashlib.sha256(raw).hexdigest(),'has_exported_at':bool(r.get('exported_at')),'completed_matches':r.get('completed')==len(entries),'sources_official':all(urlparse(x.get('source','')).hostname in ALLOWED for x in entries),'score_guard':r.get('exact_parcel_bound_rows',0)==0 and r.get('scored_business_rows',0)==0}
  result['result_file']={'checks':rc,'pass':all(rc.values()),'entries':len(entries)}
 print(json.dumps(result,indent=2));return 0 if result['batch_pass'] and (not a.results or result['result_file']['pass']) else 1
if __name__=='__main__': raise SystemExit(main())
