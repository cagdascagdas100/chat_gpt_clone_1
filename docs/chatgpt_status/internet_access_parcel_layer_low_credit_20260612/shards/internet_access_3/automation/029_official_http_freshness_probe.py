#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,tempfile,urllib.request
from pathlib import Path
SLOT='internet_access_3'
SOURCES=[
('ofcom','https://www.ofcom.org.uk/phones-and-broadband/coverage-and-speeds/connected-nations-update-spring-2026',True,['Spring 2026','13 May 2026','January 2026']),
('onspd','https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/ONS_Postcode_Directory_%28May_2026%29_for_the_United_Kingdom_%28Hosted_Table%29/FeatureServer/0?f=pjson',True,['pcd7','east1m','north1m']),
('hmlr','https://use-land-property-data.service.gov.uk/datasets/inspire/download',True,['5 July 2026','first Sunday','local authority']),
('os_uprn_docs','https://docs.os.uk/os-downloads/products/addresses-and-names-portfolio/os-open-uprn',True,['UPRN','six weeks','CSV']),
('os_uprn_supply','https://docs.os.uk/os-downloads/identifiers/os-open-uprn/os-open-uprn-overview/product-supply',True,['CSV','GeoPackage','six-weekly']),
('ons_portal','https://geoportal.statistics.gov.uk/',True,['Open Geography Portal']),
('ons_search','https://www.arcgis.com/sharing/rest/search?f=json&num=10&q=owner%3AONSGeography%20%28NSUL%20OR%20ONSUD%29%20May%202026',False,['results','total'])]
def args():
 p=argparse.ArgumentParser();p.add_argument('--repo-root',type=Path);p.add_argument('--timeout',type=int,default=45);p.add_argument('--runner-output',default='docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs/024_official_http_freshness_probe_latest.json');p.add_argument('--web-output',default='england_map_web/data/aays_21_slots/internet_access_3/official_http_freshness_probe_latest.json');return p.parse_args()
def root(x):
 if x:return x.expanduser().resolve()
 for p in [Path.cwd(),*Path(__file__).resolve().parents]:
  if (p/'docs').exists() and (p/'england_map_web').exists():return p
 raise FileNotFoundError('repo root')
def write(p,o):
 p.parent.mkdir(parents=True,exist_ok=True);fd,t=tempfile.mkstemp(dir=p.parent,prefix=p.name+'.');
 try:
  with os.fdopen(fd,'w',encoding='utf-8') as h:json.dump(o,h,ensure_ascii=False,separators=(',',':'));h.write('\n')
  os.replace(t,p)
 except Exception:
  try:os.unlink(t)
  except FileNotFoundError:pass
  raise
def probe(src,timeout):
 i,u,req,toks=src
 try:
  q=urllib.request.Request(u,headers={'User-Agent':'TerraYield-AAYS-internet-access-3/3.0','Accept':'application/json,text/html,*/*'})
  with urllib.request.urlopen(q,timeout=timeout) as r:
   b=r.read(262144);s=b.decode('utf-8',errors='replace');h={k.lower():v for k,v in r.headers.items()};missing=[x for x in toks if x.lower() not in s.lower()]
   return {'id':i,'required':req,'url':u,'final_url':r.geturl(),'status':getattr(r,'status',200),'content_type':h.get('content-type'),'content_length_header':h.get('content-length'),'etag':h.get('etag'),'last_modified':h.get('last-modified'),'bytes_sampled':len(b),'tokens_missing':missing,'passed':getattr(r,'status',200)<400 and not missing}
 except Exception as e:return {'id':i,'required':req,'url':u,'passed':False,'error_type':type(e).__name__,'error':str(e)}
def main():
 o=args();r=root(o.repo_root);rows=[probe(x,o.timeout) for x in SOURCES];bad=[x['id'] for x in rows if x['required'] and not x['passed']];s={'schema_version':1,'slot_id':SLOT,'state':'passed' if not bad else 'blocked','checks_expected':7,'checks_executed':len(rows),'required_failures':bad,'results':rows,'source_claims':{'ofcom_snapshot':'January 2026','hmlr_publication':'5 July 2026','os_open_uprn_refresh':'six-weekly','parcel_relations_promoted':0,'confidence_uplifts':0},'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False};write(r/o.runner_output,s);write(r/o.web_output,s);print(json.dumps(s,ensure_ascii=False,indent=2));return 0 if not bad else 2
if __name__=='__main__':raise SystemExit(main())
