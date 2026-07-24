#!/usr/bin/env python3
"""Create a fail-closed provenance manifest for official internet_access_3 sources."""
from __future__ import annotations
import argparse, hashlib, json, os, tempfile, urllib.request
from pathlib import Path
from typing import Any

SLOT = "internet_access_3"
REGISTRY_ROOT = Path("docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/source_snapshots")
OUTPUT_ROOT = Path("docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3/runner_outputs")
WEB_ROOT = Path("england_map_web/data/aays_21_slots/internet_access_3")
SOURCES = [
    {"id":"ofcom_spring_2026","registry":"001_ofcom_spring_2026_registry_latest.json","url_keys":["source_page","download_url"],"required_tokens":["2026","broadband"],"required":True},
    {"id":"onspd_may_2026","registry":"003_onspd_may_2026_registry_latest.json","url_keys":["service_url","dataset_page","source_page"],"required_tokens":["2026"],"required":True},
    {"id":"hmlr_inspire_july_2026","registry":"004_hmlr_inspire_july_2026_registry_latest.json","url_keys":["download_page","dataset_page","source_page"],"required_tokens":["inspire"],"required":True},
    {"id":"os_open_uprn","registry":"007_official_uprn_relation_registry_latest.json","url_keys":["url","documentation_url"],"required_tokens":["uprn"],"required":True},
]
def parse_args():
 p=argparse.ArgumentParser();p.add_argument('--repo-root',type=Path);p.add_argument('--timeout',type=int,default=120);p.add_argument('--max-read-bytes',type=int,default=2000000);p.add_argument('--runner-output',default=str(OUTPUT_ROOT/'029_official_source_package_provenance_latest.json'));p.add_argument('--web-output',default=str(WEB_ROOT/'official_source_package_provenance_latest.json'));return p.parse_args()
def repo_root(explicit):
 if explicit:
  r=explicit.expanduser().resolve()
  if not (r/'docs').exists():raise FileNotFoundError(r)
  return r
 for p in [Path.cwd(),*Path(__file__).resolve().parents]:
  if (p/'docs').exists() and (p/'england_map_web').exists():return p
 raise FileNotFoundError('repository root')
def load(path):
 with path.open('r',encoding='utf-8-sig') as h:return json.load(h)
def atomic_json(path,payload):
 path.parent.mkdir(parents=True,exist_ok=True);fd,name=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=path.parent)
 try:
  with os.fdopen(fd,'w',encoding='utf-8') as h:json.dump(payload,h,ensure_ascii=False,separators=(',',':'));h.write('\n')
  os.replace(name,path)
 except Exception:
  try:os.unlink(name)
  except FileNotFoundError:pass
  raise
def recursive_urls(value,wanted):
 urls=[]
 if isinstance(value,dict):
  for key,child in value.items():
   if key in wanted and isinstance(child,str) and child.startswith('http'):urls.append(child)
   urls.extend(recursive_urls(child,wanted))
 elif isinstance(value,list):
  for child in value:urls.extend(recursive_urls(child,wanted))
 return urls
def probe(url,timeout,max_bytes):
 req=urllib.request.Request(url,headers={'User-Agent':'TerraYield-AAYS-internet-access-3/4.0','Accept':'application/json,text/html,application/zip,application/octet-stream,*/*','Range':f'bytes=0-{max_bytes-1}'})
 with urllib.request.urlopen(req,timeout=timeout) as response:
  body=response.read(max_bytes);headers={k.lower():v for k,v in response.headers.items()}
  return {'requested_url':url,'final_url':response.geturl(),'status':int(getattr(response,'status',response.getcode())),'content_type':headers.get('content-type'),'content_length_header':headers.get('content-length'),'etag':headers.get('etag'),'last_modified':headers.get('last-modified'),'content_range':headers.get('content-range'),'bytes_read':len(body),'sample_sha256':hashlib.sha256(body).hexdigest(),'sample_prefix_hex':body[:16].hex(),'sample_text':body[:5000].decode('utf-8',errors='ignore').lower()}
def main():
 args=parse_args();root=repo_root(args.repo_root);results=[];blockers=[]
 for spec in SOURCES:
  rp=root/REGISTRY_ROOT/spec['registry'];item={'id':spec['id'],'registry_path':str(rp.relative_to(root)),'required':spec['required'],'registry_exists':rp.exists(),'probes':[]}
  if not rp.exists():blockers.append(f"{spec['id']}:REGISTRY_MISSING");results.append(item);continue
  registry=load(rp);item['registry_sha256']=hashlib.sha256(rp.read_bytes()).hexdigest();urls=list(dict.fromkeys(recursive_urls(registry,set(spec['url_keys']))));item['resolved_urls']=urls
  if not urls:blockers.append(f"{spec['id']}:URL_MISSING");results.append(item);continue
  source_passed=False;errors=[]
  for url in urls[:2]:
   try:
    evidence=probe(url,args.timeout,args.max_read_bytes);text=evidence.pop('sample_text');hits={token:token.lower() in (text+' '+evidence['final_url'].lower()) for token in spec['required_tokens']};evidence['required_token_hits']=hits;evidence['passed']=evidence['status'] in {200,206} and evidence['bytes_read']>0 and all(hits.values());source_passed=source_passed or evidence['passed'];item['probes'].append(evidence)
   except Exception as exc:errors.append(f'{type(exc).__name__}:{exc}')
  item['errors']=errors;item['passed']=source_passed
  if spec['required'] and not source_passed:blockers.append(f"{spec['id']}:PROVENANCE_PROBE_FAILED")
  results.append(item)
 passed=not blockers;payload={'schema_version':1,'slot_id':SLOT,'state':'provenance_passed' if passed else 'blocked','sources_expected':len(SOURCES),'sources_passed':sum(1 for i in results if i.get('passed')),'results':results,'blockers':blockers,'provenance_semantics':'HTTP_RELEASE_IDENTITY_AND_REGISTRY_HASH_ONLY_NO_PARCEL_PROMOTION','parcel_relations_promoted':0,'confidence_uplifts':0,'final_ready':False,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False};atomic_json(root/args.runner_output,payload);atomic_json(root/args.web_output,payload);print(json.dumps(payload,ensure_ascii=False,indent=2));return 0 if passed else 2
if __name__=='__main__':raise SystemExit(main())
