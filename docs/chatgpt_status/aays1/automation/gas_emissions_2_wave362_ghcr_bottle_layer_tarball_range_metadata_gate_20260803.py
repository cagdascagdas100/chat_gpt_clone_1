#!/usr/bin/env python3
"""Wave362: GHCR bottle layer HEAD + bytes=0-0 metadata gate; never full layers."""
from __future__ import annotations
import argparse, hashlib, json, os, tempfile, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path
BASE='https://ghcr.io'; REPO='homebrew/core/overturemaps'; TAGS=['1.0.1_1','1.0.1']
MAX_MANIFEST=1_000_000; MAX_CHILD=4; MAX_LAYERS=6; RANGE='bytes=0-0'
AI='application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.list.v2+json, application/vnd.oci.image.manifest.v1+json, application/vnd.docker.distribution.manifest.v2+json'
AM='application/vnd.oci.image.manifest.v1+json, application/vnd.docker.distribution.manifest.v2+json'
KEEP={'accept-ranges','content-length','content-range','content-type','docker-content-digest','etag','last-modified','location'}
def sh(b): return hashlib.sha256(b).hexdigest()
def atomic(path,obj):
 p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); raw=(json.dumps(obj,sort_keys=True,separators=(',',':'))+'\n').encode()
 with tempfile.NamedTemporaryFile(dir=p.parent,delete=False) as f: f.write(raw); n=f.name
 os.replace(n,p)
def hs(h): return {k.lower():v for k,v in h.items() if k.lower() in KEEP}
def req(url,timeout,method='GET',headers=None,max_bytes=0):
 t=time.monotonic(); q=urllib.request.Request(url,method=method,headers={'User-Agent':'AAYS-W362','Accept-Encoding':'identity',**(headers or {})})
 try:
  with urllib.request.urlopen(q,timeout=timeout) as r:
   b=b'' if method=='HEAD' else r.read(max_bytes+1)
   if len(b)>max_bytes: raise ValueError('RESPONSE_EXCEEDED_BOUND')
   o={'ok':True,'url':url,'method':method,'status':getattr(r,'status',None),'bytes':len(b),'body_sha256':sh(b),'headers':hs(r.headers),'seconds':round(time.monotonic()-t,3)}
   if b:
    try:o['json']=json.loads(b)
    except Exception:pass
   return o
 except urllib.error.HTTPError as e:
  return {'ok':False,'url':url,'method':method,'status':e.code,'bytes':0,'error':f'HTTPError:{e.code}:{e.reason}','headers':hs(e.headers),'seconds':round(time.monotonic()-t,3)}
 except Exception as e:return {'ok':False,'url':url,'method':method,'bytes':0,'error':f'{type(e).__name__}:{e}','seconds':round(time.monotonic()-t,3)}
def rc(o): return {k:v for k,v in o.items() if k!='json'}
def children(d):
 out=[]
 for x in d.get('manifests') or []:
  p=x.get('platform') or {}
  if p.get('os')=='linux' and p.get('architecture') in {'amd64','arm64'} and x.get('digest'):
   out.append({'mediaType':x.get('mediaType'),'digest':x.get('digest'),'size':x.get('size'),'platform':p,'annotations':x.get('annotations')})
 return out[:MAX_CHILD]
def layer(x): return {'mediaType':x.get('mediaType'),'digest':x.get('digest'),'size':x.get('size'),'annotations':x.get('annotations')}
def selftest():
 d={'manifests':[{'digest':'sha256:a','platform':{'os':'linux','architecture':'amd64'}},{'digest':'sha256:b','platform':{'os':'darwin','architecture':'arm64'}}]}
 assert children(d)[0]['digest']=='sha256:a' and RANGE=='bytes=0-0'; print('SELF_TEST_PASS')
def main():
 a=argparse.ArgumentParser(); a.add_argument('--canonical'); a.add_argument('--fixture'); a.add_argument('--output'); a.add_argument('--timeout',type=int,default=20); a.add_argument('--accessed-at'); a.add_argument('--self-test',action='store_true'); x=a.parse_args()
 if x.self_test:selftest(); return
 c=json.load(open(x.canonical)); f=json.load(open(x.fixture)); pts=[]
 for row in c['rows'][:3]:
  p=row['properties']; pts.append({'parcel_id':p['parcel_id'],'hmlr_inspire_id':p['hmlr_inspire_id'],'longitude':p['hmlr_lon'],'latitude':p['hmlr_lat'],'geometry_type':row.get('geometry_type') or (row.get('geometry') or {}).get('type')})
 ping=req(BASE+'/v2/',x.timeout,max_bytes=64000); tu=BASE+'/token?'+urllib.parse.urlencode({'service':'ghcr.io','scope':f'repository:{REPO}:pull'}); tr=req(tu,x.timeout,max_bytes=256000); token=(tr.get('json') or {}).get('token') or (tr.get('json') or {}).get('access_token'); ah={'Authorization':f'Bearer {token}'} if token else {}
 tags=[]; cm=ld=lh=lr=rb=0; full=False
 if token:
  for tag in TAGS:
   ir=req(f'{BASE}/v2/{REPO}/manifests/{tag}',x.timeout,headers={**ah,'Accept':AI},max_bytes=MAX_MANIFEST); doc=ir.get('json') or {}; ds=children(doc); direct=False
   if not ds and isinstance(doc.get('layers'),list): ds=[{'digest':tag,'platform':{},'direct':True}]; direct=True
   trec={'tag':tag,'index_receipt':rc(ir),'index_media_type':doc.get('mediaType'),'selected_child_descriptors':ds,'child_records':[],'direct_manifest':direct}
   for d in ds:
    mr,md=(ir,doc) if d.get('direct') else (req(f"{BASE}/v2/{REPO}/manifests/{d['digest']}",x.timeout,headers={**ah,'Accept':AM},max_bytes=MAX_MANIFEST),None)
    if md is None: md=mr.get('json') or {}
    if mr.get('ok'): cm+=1
    cr={'platform':d.get('platform'),'child_manifest_receipt':rc(mr),'layer_records':[]}
    for z in md.get('layers') or []:
     if ld>=MAX_LAYERS: break
     q=layer(z); dg=q.get('digest')
     if not dg: continue
     ld+=1; u=f'{BASE}/v2/{REPO}/blobs/{dg}'; hr=req(u,x.timeout,method='HEAD',headers=ah); rr=req(u,x.timeout,headers={**ah,'Range':RANGE},max_bytes=1)
     if hr.get('ok') and hr.get('status')==200: lh+=1
     if rr.get('ok') and rr.get('status')==206 and rr.get('bytes',0)<=1: lr+=1
     rb+=int(rr.get('bytes') or 0); full=full or int(rr.get('bytes') or 0)>1
     cr['layer_records'].append({'descriptor':q,'head_receipt':rc(hr),'range_receipt':rc(rr),'range_header':RANGE})
    trec['child_records'].append(cr)
   tags.append(trec)
 else: tags=[{'tag':t,'attempted':False,'reason':'TOKEN_NOT_ACQUIRED','child_records':[]} for t in TAGS]
 b=[]
 if not ping.get('ok'):b.append('GHCR_V2_ENDPOINT_NOT_LIVE_ACQUIRED')
 if not token:b.append('GHCR_ANONYMOUS_PULL_TOKEN_NOT_ACQUIRED')
 if cm==0:b.append('OVERTUREMAPS_CHILD_MANIFEST_NOT_LIVE_ACQUIRED')
 if ld==0:b.append('OCI_LAYER_DESCRIPTOR_NOT_ACQUIRED')
 if lh==0:b.append('OCI_LAYER_HEAD_METADATA_NOT_ACQUIRED')
 if lr==0:b.append('OCI_LAYER_RANGE_METADATA_NOT_ACQUIRED')
 b += ['BOTTLE_LAYER_TARBALL_FULL_BODY_NOT_DOWNLOADED_BY_DESIGN','THREE_BOUNDED_BBOX_STREAMS_NOT_COMPLETED','THREE_OVERTURE_BUILDING_FEATURES_NOT_ACQUIRED','THREE_EXACT_UPRNS_NOT_ACQUIRED','EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE']
 ex=f'ping={bool(ping.get("ok"))};token={bool(token)};child_manifests={cm};layer_descriptors={ld};head_metadata={lh};range_metadata={lr};range_bytes={rb};full_layer_body={full}'
 run={'source_url':f'{BASE}/v2/{REPO}/blobs/<digest>','accessed_at':x.accessed_at,'content_sha256':sh(ex.encode()),'hash_scope':'ghcr_layer_descriptor_head_and_one_byte_range_receipts','record_scope':'GHCR v2 ping, anonymous token, two bottle tags, up to four Linux child manifests and six layer HEAD/bytes=0-0 probes; no complete layer body.','relevant_record_ids_or_excerpt':ex,'supports_fields':['layer_media_type','layer_digest','layer_size','content_length','content_range','accept_ranges','docker_content_digest','one_byte_range_only','no_full_layer_body'],'license_or_terms_url':'https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry'}
 out={'schema_version':1,'architecture_version':3,'slot_id':'gas_emissions_2','wave':362,'accessed_at':x.accessed_at,'assessments':pts,'ghcr_ping':rc(ping),'token_receipt':rc(tr),'token_acquired':bool(token),'tag_records':tags,'child_manifest_count':cm,'layer_descriptor_count':ld,'layer_head_metadata_count':lh,'layer_range_metadata_count':lr,'total_range_bytes_read':rb,'range_header':RANGE,'bottle_layer_full_body_downloaded':full,'business_rows_produced':0,'parcel_rows_bound':0,'completed_count':0,'target_count':30761,'previous_percent':0.0,'current_percent':0.0,'percent_increase':0.0,'decision':'GHCR_BOTTLE_LAYER_TARBALL_RANGE_METADATA_GATE_ASSESSED','state':'NO_DATA_CONTINUE','blocker':';'.join(b),'first_unverified_step':'ASSESS_GHCR_BOTTLE_LAYER_TARBALL_PREFIX_OR_NO_DATA_CONTINUE','source_evidence_manifest':f['source_evidence_manifest'],'runtime_source_evidence':[run],'fake_data':False,'final_ready':False}
 atomic(x.output,out)
if __name__=='__main__':main()
