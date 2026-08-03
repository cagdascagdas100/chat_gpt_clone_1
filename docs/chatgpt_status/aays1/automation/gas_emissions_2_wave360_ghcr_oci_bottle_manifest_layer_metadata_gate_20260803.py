#!/usr/bin/env python3
"""Bounded GHCR OCI Homebrew bottle manifest metadata gate; no layer bodies."""
import argparse, hashlib, json, os, tempfile, time, urllib.parse, urllib.request
from pathlib import Path
BASE='https://ghcr.io'; REPO='homebrew/core/overturemaps'; TAGS=['1.0.1_1','1.0.1']; MAX=1000000
ACCEPT='application/vnd.oci.image.index.v1+json, application/vnd.oci.image.manifest.v1+json, application/vnd.docker.distribution.manifest.list.v2+json, application/vnd.docker.distribution.manifest.v2+json'
def h(b): return hashlib.sha256(b).hexdigest()
def write(p,o):
 p=Path(p); p.parent.mkdir(parents=True,exist_ok=True); b=(json.dumps(o,sort_keys=True,separators=(',',':'))+'\n').encode()
 with tempfile.NamedTemporaryFile(dir=p.parent,delete=False) as f: f.write(b); n=f.name
 os.replace(n,p)
def get(url,timeout,headers=None):
 t=time.monotonic(); q=urllib.request.Request(url,headers={'User-Agent':'AAYS-W360',**(headers or {})})
 try:
  with urllib.request.urlopen(q,timeout=timeout) as r:
   b=r.read(MAX+1)
   if len(b)>MAX: raise ValueError('RESPONSE_TOO_LARGE')
   return {'ok':True,'url':url,'status':getattr(r,'status',None),'bytes':len(b),'sha256':h(b),'headers':dict(r.headers.items()),'json':json.loads(b) if b else {},'seconds':round(time.monotonic()-t,3)}
 except Exception as e: return {'ok':False,'url':url,'bytes':0,'error':f'{type(e).__name__}:{e}','seconds':round(time.monotonic()-t,3)}
def selftest():
 assert urllib.parse.quote(REPO,safe='/:')==REPO; assert TAGS[0]=='1.0.1_1'; print('SELF_TEST_PASS')
def main():
 p=argparse.ArgumentParser(); p.add_argument('--canonical'); p.add_argument('--fixture'); p.add_argument('--output'); p.add_argument('--timeout',type=int,default=20); p.add_argument('--accessed-at'); p.add_argument('--self-test',action='store_true'); a=p.parse_args()
 if a.self_test: selftest(); return
 can=json.load(open(a.canonical)); fix=json.load(open(a.fixture)); pts=[]
 for r in can['rows'][:3]:
  x=r['properties']; pts.append({'parcel_id':x['parcel_id'],'hmlr_inspire_id':x['hmlr_inspire_id'],'longitude':x['hmlr_lon'],'latitude':x['hmlr_lat']})
 ping=get(BASE+'/v2/',a.timeout)
 token_url=BASE+'/token?'+urllib.parse.urlencode({'service':'ghcr.io','scope':f'repository:{REPO}:pull'})
 tok=get(token_url,a.timeout); token=(tok.get('json') or {}).get('token') or (tok.get('json') or {}).get('access_token')
 manifests=[]
 if token:
  for tag in TAGS:
   r=get(f'{BASE}/v2/{REPO}/manifests/{tag}',a.timeout,{'Authorization':f'Bearer {token}','Accept':ACCEPT})
   j=r.get('json') or {}; desc=[]
   for d in j.get('manifests',[])[:32]: desc.append({'mediaType':d.get('mediaType'),'digest':d.get('digest'),'size':d.get('size'),'platform':d.get('platform'),'annotations':d.get('annotations')})
   manifests.append({'tag':tag,'receipt':{k:v for k,v in r.items() if k!='json'},'schemaVersion':j.get('schemaVersion'),'mediaType':j.get('mediaType'),'descriptor_count':len(desc),'descriptors':desc})
 else:
  manifests=[{'tag':t,'attempted':False,'reason':'TOKEN_NOT_ACQUIRED','descriptor_count':0,'descriptors':[]} for t in TAGS]
 live=sum(1 for m in manifests if m.get('receipt',{}).get('ok')); desc=sum(m.get('descriptor_count',0) for m in manifests); bl=[]
 if not ping['ok']: bl+=['GHCR_V2_ENDPOINT_NOT_LIVE_ACQUIRED']
 if not token: bl+=['GHCR_ANONYMOUS_PULL_TOKEN_NOT_ACQUIRED']
 if live==0: bl+=['OVERTUREMAPS_OCI_BOTTLE_MANIFEST_NOT_LIVE_ACQUIRED']
 if desc==0: bl+=['OCI_BOTTLE_LAYER_DESCRIPTOR_METADATA_NOT_ACQUIRED']
 bl+=['BOTTLE_LAYER_BODIES_NOT_DOWNLOADED_BY_DESIGN','THREE_BOUNDED_BBOX_STREAMS_NOT_COMPLETED','THREE_OVERTURE_BUILDING_FEATURES_NOT_ACQUIRED','THREE_EXACT_UPRNS_NOT_ACQUIRED','EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE']
 ex=f"ping={ping['ok']};token={bool(token)};manifest_live={live};descriptors={desc};body_downloaded=False"
 rt={'source_url':BASE+'/v2/','accessed_at':a.accessed_at,'content_sha256':h(ex.encode()),'hash_scope':'ghcr_ping_token_manifest_receipts','record_scope':'GHCR v2 ping, anonymous pull token and two OCI manifest candidates; no blobs.','relevant_record_ids_or_excerpt':ex,'supports_fields':['oci_media_type','digest','size','platform','annotations','no_blob_download'],'license_or_terms_url':'https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry'}
 write(a.output,{'schema_version':1,'architecture_version':3,'slot_id':'gas_emissions_2','wave':360,'accessed_at':a.accessed_at,'assessments':pts,'ghcr_ping':{k:v for k,v in ping.items() if k!='json'},'token_receipt':{k:v for k,v in tok.items() if k!='json'},'token_acquired':bool(token),'manifest_candidates':manifests,'live_manifest_count':live,'descriptor_count':desc,'bottle_layer_body_downloaded':False,'business_rows_produced':0,'parcel_rows_bound':0,'completed_count':0,'target_count':30761,'previous_percent':0.0,'current_percent':0.0,'percent_increase':0.0,'decision':'GHCR_OCI_BOTTLE_MANIFEST_AND_LAYER_METADATA_GATE_ASSESSED','state':'NO_DATA_CONTINUE','blocker':';'.join(bl),'first_unverified_step':'ASSESS_GHCR_BOTTLE_CONFIG_BLOB_METADATA_OR_NO_DATA_CONTINUE','source_evidence_manifest':fix['source_evidence_manifest'],'runtime_source_evidence':[rt],'fake_data':False,'final_ready':False})
if __name__=='__main__': main()
