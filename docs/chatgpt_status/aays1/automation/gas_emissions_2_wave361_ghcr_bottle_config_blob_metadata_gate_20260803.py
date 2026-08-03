#!/usr/bin/env python3
"""Wave361: bounded GHCR OCI bottle config-blob metadata gate; no layer bodies."""
from __future__ import annotations
import argparse, hashlib, json, os, tempfile, time, urllib.parse, urllib.request
from pathlib import Path
BASE='https://ghcr.io'; REPO='homebrew/core/overturemaps'; TAGS=['1.0.1_1','1.0.1']
MAX_MANIFEST=1_000_000; MAX_CONFIG=1_000_000; MAX_CONFIG_COUNT=4
ACCEPT_INDEX='application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.list.v2+json, application/vnd.oci.image.manifest.v1+json, application/vnd.docker.distribution.manifest.v2+json'
ACCEPT_MANIFEST='application/vnd.oci.image.manifest.v1+json, application/vnd.docker.distribution.manifest.v2+json'
def h(b:bytes)->str: return hashlib.sha256(b).hexdigest()
def atomic_write(path,obj):
 p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); raw=(json.dumps(obj,sort_keys=True,separators=(',',':'))+'\n').encode()
 with tempfile.NamedTemporaryFile(dir=p.parent,delete=False) as f: f.write(raw); tmp=f.name
 os.replace(tmp,p)
def get(url,timeout,max_bytes,headers=None):
 started=time.monotonic(); req=urllib.request.Request(url,headers={'User-Agent':'AAYS-W361',**(headers or {})})
 try:
  with urllib.request.urlopen(req,timeout=timeout) as r:
   body=r.read(max_bytes+1)
   if len(body)>max_bytes: raise ValueError('RESPONSE_TOO_LARGE')
   out={'ok':True,'url':url,'status':getattr(r,'status',None),'bytes':len(body),'sha256':h(body),'headers':dict(r.headers.items()),'seconds':round(time.monotonic()-started,3)}
   try: out['json']=json.loads(body) if body else {}
   except Exception: out['json_error']=True
   return out
 except Exception as e:
  return {'ok':False,'url':url,'bytes':0,'error':f'{type(e).__name__}:{e}','seconds':round(time.monotonic()-started,3)}
def receipt(r): return {k:v for k,v in r.items() if k!='json'}
def safe_config_summary(obj):
 cfg=obj.get('config') if isinstance(obj,dict) else None; cfg=cfg if isinstance(cfg,dict) else {}
 labels=cfg.get('Labels') if isinstance(cfg.get('Labels'),dict) else {}
 env=cfg.get('Env') if isinstance(cfg.get('Env'),list) else []
 env_names=sorted({str(x).split('=',1)[0] for x in env if isinstance(x,str) and '=' in x})[:64]
 rootfs=obj.get('rootfs') if isinstance(obj.get('rootfs'),dict) else {}
 history=obj.get('history') if isinstance(obj.get('history'),list) else []
 return {'created':obj.get('created'),'author':obj.get('author'),'architecture':obj.get('architecture'),'os':obj.get('os'),'variant':obj.get('variant'),'top_level_keys':sorted(obj.keys())[:64],'config_keys':sorted(cfg.keys())[:64],'label_keys':sorted(labels.keys())[:128],'env_names':env_names,'rootfs_type':rootfs.get('type'),'rootfs_diff_id_count':len(rootfs.get('diff_ids') or []),'history_count':len(history)}
def choose_index_descriptors(doc):
 ds=[]
 for d in (doc.get('manifests') or []):
  p=d.get('platform') or {}; osname=p.get('os'); arch=p.get('architecture')
  if osname=='linux' and arch in {'amd64','arm64'} and d.get('digest'):
   ds.append({'mediaType':d.get('mediaType'),'digest':d.get('digest'),'size':d.get('size'),'platform':p,'annotations':d.get('annotations')})
 return ds[:4]
def selftest():
 assert urllib.parse.quote(REPO,safe='/:')==REPO
 sample={'architecture':'amd64','os':'linux','config':{'Labels':{'a':'b'},'Env':['A=1','B=2']},'rootfs':{'type':'layers','diff_ids':['sha256:x']},'history':[{}]}
 s=safe_config_summary(sample); assert s['architecture']=='amd64' and s['label_keys']==['a'] and s['env_names']==['A','B']
 print('SELF_TEST_PASS')
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--canonical'); ap.add_argument('--fixture'); ap.add_argument('--output'); ap.add_argument('--timeout',type=int,default=20); ap.add_argument('--accessed-at'); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args()
 if a.self_test: selftest(); return
 canonical=json.load(open(a.canonical)); fixture=json.load(open(a.fixture)); points=[]
 for row in canonical['rows'][:3]:
  p=row['properties']; points.append({'parcel_id':p['parcel_id'],'hmlr_inspire_id':p['hmlr_inspire_id'],'longitude':p['hmlr_lon'],'latitude':p['hmlr_lat']})
 ping=get(BASE+'/v2/',a.timeout,MAX_MANIFEST)
 token_url=BASE+'/token?'+urllib.parse.urlencode({'service':'ghcr.io','scope':f'repository:{REPO}:pull'})
 tok=get(token_url,a.timeout,MAX_MANIFEST); token=(tok.get('json') or {}).get('token') or (tok.get('json') or {}).get('access_token')
 headers={'Authorization':f'Bearer {token}'} if token else {}
 tags=[]; config_records=[]; child_manifest_count=0; descriptor_count=0; config_descriptor_count=0; config_blob_count=0
 if token:
  for tag in TAGS:
   idx=get(f'{BASE}/v2/{REPO}/manifests/{tag}',a.timeout,MAX_MANIFEST,{**headers,'Accept':ACCEPT_INDEX}); doc=idx.get('json') or {}
   ds=choose_index_descriptors(doc); descriptor_count+=len(ds)
   tagrec={'tag':tag,'receipt':receipt(idx),'mediaType':doc.get('mediaType'),'schemaVersion':doc.get('schemaVersion'),'selected_descriptors':ds}
   if not ds and doc.get('config'):
    ds=[{'digest':tag,'direct_manifest':True,'platform':{'os':None,'architecture':None}}]
   child=[]
   for d in ds:
    if len(config_records)>=MAX_CONFIG_COUNT: break
    if d.get('direct_manifest'):
     m=idx; mdoc=doc
    else:
     m=get(f"{BASE}/v2/{REPO}/manifests/{d['digest']}",a.timeout,MAX_MANIFEST,{**headers,'Accept':ACCEPT_MANIFEST}); mdoc=m.get('json') or {}
    if m.get('ok'): child_manifest_count+=1
    cfg=mdoc.get('config') if isinstance(mdoc.get('config'),dict) else {}; cfgdesc={'mediaType':cfg.get('mediaType'),'digest':cfg.get('digest'),'size':cfg.get('size')}
    if cfgdesc['digest']: config_descriptor_count+=1
    crec={'tag':tag,'platform':d.get('platform'),'child_manifest_receipt':receipt(m),'config_descriptor':cfgdesc,'layer_descriptor_count':len(mdoc.get('layers') or []),'config_blob_attempted':False}
    size=cfgdesc.get('size'); digest=cfgdesc.get('digest')
    if digest and isinstance(size,int) and 0<=size<=MAX_CONFIG and len(config_records)<MAX_CONFIG_COUNT:
     blob=get(f'{BASE}/v2/{REPO}/blobs/{digest}',a.timeout,MAX_CONFIG,headers); crec['config_blob_attempted']=True; crec['config_blob_receipt']=receipt(blob)
     if blob.get('ok') and isinstance(blob.get('json'),dict):
      config_blob_count+=1; raw_sha=blob.get('sha256'); digest_ok=(digest==f'sha256:{raw_sha}') if digest.startswith('sha256:') else None
      crec['digest_verified']=digest_ok; crec['config_summary']=safe_config_summary(blob['json'])
    child.append(crec); config_records.append(crec)
   tagrec['child_records']=child; tags.append(tagrec)
 else:
  tags=[{'tag':tag,'attempted':False,'reason':'TOKEN_NOT_ACQUIRED','selected_descriptors':[],'child_records':[]} for tag in TAGS]
 blockers=[]
 if not ping.get('ok'): blockers.append('GHCR_V2_ENDPOINT_NOT_LIVE_ACQUIRED')
 if not token: blockers.append('GHCR_ANONYMOUS_PULL_TOKEN_NOT_ACQUIRED')
 if child_manifest_count==0: blockers.append('OVERTUREMAPS_CHILD_MANIFEST_NOT_LIVE_ACQUIRED')
 if config_descriptor_count==0: blockers.append('OCI_CONFIG_DESCRIPTOR_NOT_ACQUIRED')
 if config_blob_count==0: blockers.append('OCI_CONFIG_BLOB_METADATA_NOT_ACQUIRED')
 blockers += ['BOTTLE_LAYER_BODIES_NOT_DOWNLOADED_BY_DESIGN','THREE_BOUNDED_BBOX_STREAMS_NOT_COMPLETED','THREE_OVERTURE_BUILDING_FEATURES_NOT_ACQUIRED','THREE_EXACT_UPRNS_NOT_ACQUIRED','EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE']
 excerpt=f'ping={ping.get("ok",False)};token={bool(token)};index_descriptors={descriptor_count};child_manifests={child_manifest_count};config_descriptors={config_descriptor_count};config_blobs={config_blob_count};layer_bodies=False'
 runtime={'source_url':BASE+'/v2/','accessed_at':a.accessed_at,'content_sha256':h(excerpt.encode()),'hash_scope':'ghcr_index_child_manifest_config_blob_receipts','record_scope':'GHCR v2 ping, anonymous token, two bottle tags, selected Linux child manifests and at most four config JSON blobs; no layer bodies.','relevant_record_ids_or_excerpt':excerpt,'supports_fields':['index_descriptor','child_manifest','config_media_type','config_digest','config_size','config_json_metadata','no_layer_body'],'license_or_terms_url':'https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry'}
 out={'schema_version':1,'architecture_version':3,'slot_id':'gas_emissions_2','wave':361,'accessed_at':a.accessed_at,'assessments':points,'ghcr_ping':receipt(ping),'token_receipt':receipt(tok),'token_acquired':bool(token),'tag_records':tags,'index_descriptor_count':descriptor_count,'child_manifest_count':child_manifest_count,'config_descriptor_count':config_descriptor_count,'config_blob_metadata_count':config_blob_count,'config_records':config_records,'bottle_layer_body_downloaded':False,'business_rows_produced':0,'parcel_rows_bound':0,'completed_count':0,'target_count':30761,'previous_percent':0.0,'current_percent':0.0,'percent_increase':0.0,'decision':'GHCR_BOTTLE_CONFIG_BLOB_METADATA_GATE_ASSESSED','state':'NO_DATA_CONTINUE','blocker':';'.join(blockers),'first_unverified_step':'ASSESS_GHCR_BOTTLE_LAYER_TARBALL_RANGE_METADATA_OR_NO_DATA_CONTINUE','source_evidence_manifest':fixture['source_evidence_manifest'],'runtime_source_evidence':[runtime],'fake_data':False,'final_ready':False}
 atomic_write(a.output,out)
if __name__=='__main__': main()
