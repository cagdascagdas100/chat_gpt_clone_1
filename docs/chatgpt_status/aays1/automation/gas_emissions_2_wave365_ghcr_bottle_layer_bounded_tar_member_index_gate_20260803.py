#!/usr/bin/env python3
"""Wave365: bounded GHCR bottle-layer tar member index; never downloads a full layer."""
from __future__ import annotations
import argparse, hashlib, io, json, os, tarfile, tempfile, time, urllib.error, urllib.parse, urllib.request, zlib
from pathlib import Path

BASE="https://ghcr.io"; REPO="homebrew/core/overturemaps"; TAGS=["1.0.1_1","1.0.1"]
MAX_CHILD=4; MAX_LAYERS=4; MAX_COMPRESSED=262144; MAX_DECOMPRESSED=524288; MAX_MEMBERS=32
RANGE=f"bytes=0-{MAX_COMPRESSED-1}"
ACCEPT=", ".join(["application/vnd.oci.image.index.v1+json","application/vnd.docker.distribution.manifest.list.v2+json","application/vnd.oci.image.manifest.v1+json","application/vnd.docker.distribution.manifest.v2+json"])

def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def atomic_json(path:str,obj:dict)->None:
 p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);raw=(json.dumps(obj,sort_keys=True,separators=(",",":"))+"\n").encode()
 with tempfile.NamedTemporaryFile(dir=p.parent,delete=False) as h:h.write(raw);n=h.name
 os.replace(n,p)
def req(url:str,timeout:int,headers:dict|None=None,max_bytes:int=0)->dict:
 t=time.monotonic();r=urllib.request.Request(url,headers={"User-Agent":"AAYS-W365","Accept-Encoding":"identity",**(headers or {})})
 try:
  with urllib.request.urlopen(r,timeout=timeout) as x:
   b=x.read(max_bytes+1)
   if len(b)>max_bytes:raise ValueError("RESPONSE_EXCEEDED_BOUND")
   return {"ok":True,"status":getattr(x,"status",None),"url":url,"bytes":len(b),"body_sha256":sha(b),"headers":{k.lower():v for k,v in x.headers.items() if k.lower() in {"content-range","content-length","content-type","docker-content-digest","location"}},"body":b,"seconds":round(time.monotonic()-t,3)}
 except urllib.error.HTTPError as e:return {"ok":False,"status":e.code,"url":url,"bytes":0,"error":f"HTTPError:{e.code}:{e.reason}","seconds":round(time.monotonic()-t,3)}
 except Exception as e:return {"ok":False,"url":url,"bytes":0,"error":f"{type(e).__name__}:{e}","seconds":round(time.monotonic()-t,3)}
def clean(r:dict)->dict:return {k:v for k,v in r.items() if k!="body"}
def doc(r:dict)->dict:
 try:return json.loads((r.get("body")or b"").decode())
 except Exception:return {}
def octal(b:bytes)->int:return int((b.split(b"\0",1)[0].strip()or b"0"),8)
def member_index(blob:bytes)->dict:
 comp="UNKNOWN";data=b"";err=None
 try:
  if blob.startswith(b"\x1f\x8b"):
   comp="GZIP";data=zlib.decompressobj(16+zlib.MAX_WBITS).decompress(blob,MAX_DECOMPRESSED+1)
  elif len(blob)>=262 and blob[257:262]==b"ustar":comp="TAR";data=blob
  elif blob.startswith(b"\x28\xb5\x2f\xfd"):return {"compression_magic":"ZSTD","member_count":0,"members":[],"decompressed_bytes":0,"bounded_decode_error":"ZSTD_DECODER_NOT_AVAILABLE_IN_STDLIB"}
  else:return {"compression_magic":comp,"member_count":0,"members":[],"decompressed_bytes":0}
 except Exception as e:err=f"{type(e).__name__}:{e}"
 if len(data)>MAX_DECOMPRESSED:return {"compression_magic":comp,"member_count":0,"members":[],"decompressed_bytes":len(data),"bounded_decode_error":"DECOMPRESSED_BOUND_EXCEEDED"}
 members=[];off=0
 while off+512<=len(data) and len(members)<MAX_MEMBERS:
  block=data[off:off+512]
  if block==b"\0"*512:break
  name=block[:100].split(b"\0",1)[0].decode("utf-8","replace");prefix=block[345:500].split(b"\0",1)[0].decode("utf-8","replace")
  try:size=octal(block[124:136])
  except Exception as e:err=f"TAR_SIZE_PARSE_ERROR:{type(e).__name__}:{e}";break
  members.append({"index":len(members),"name":f"{prefix}/{name}" if prefix else name,"size":size,"typeflag":block[156:157].decode("ascii","replace")or"0","header_offset":off})
  off+=512+((size+511)//512)*512
 out={"compression_magic":comp,"member_count":len(members),"members":members,"decompressed_bytes":len(data),"decompressed_sha256":sha(data),"index_complete_within_bound":bool(off+512<=len(data)and data[off:off+512]==b"\0"*512)}
 if err:out["bounded_decode_error"]=err
 return out
def self_test()->None:
 raw=io.BytesIO()
 with tarfile.open(fileobj=raw,mode="w") as a:
  for n,p in [("one.txt",b"one"),("dir/two.json",b'{"two":2}')]:
   i=tarfile.TarInfo(n);i.size=len(p);a.addfile(i,io.BytesIO(p))
 z=zlib.compressobj(wbits=16+zlib.MAX_WBITS);r=member_index(z.compress(raw.getvalue())+z.flush())
 assert r["compression_magic"]=="GZIP" and [m["name"] for m in r["members"]]==["one.txt","dir/two.json"] and RANGE=="bytes=0-262143"
 print("SELF_TEST_PASS")
def main()->None:
 p=argparse.ArgumentParser();p.add_argument("--prior");p.add_argument("--output");p.add_argument("--timeout",type=int,default=20);p.add_argument("--accessed-at");p.add_argument("--self-test",action="store_true");a=p.parse_args()
 if a.self_test:self_test();return
 prior=json.load(open(a.prior,encoding="utf-8"));ping=req(BASE+"/v2/",a.timeout,max_bytes=64000)
 token_url=BASE+"/token?"+urllib.parse.urlencode({"service":"ghcr.io","scope":f"repository:{REPO}:pull"});tr=req(token_url,a.timeout,max_bytes=256000);td=doc(tr);token=td.get("token")or td.get("access_token");auth={"Authorization":f"Bearer {token}"}if token else{}
 records=[];manifests=layers=streams=members=total=0
 if token:
  for tag in TAGS:
   ir=req(f"{BASE}/v2/{REPO}/manifests/{tag}",a.timeout,{**auth,"Accept":ACCEPT},1000000);idx=doc(ir);children=[x for x in idx.get("manifests",[])if(x.get("platform")or{}).get("os")=="linux"][:MAX_CHILD]
   if not children and idx.get("layers"):children=[{"digest":tag,"direct":True,"platform":{}}]
   rr={"tag":tag,"index_receipt":clean(ir),"children":[]}
   for c in children:
    mr=ir if c.get("direct")else req(f"{BASE}/v2/{REPO}/manifests/{c['digest']}",a.timeout,{**auth,"Accept":ACCEPT},1000000);md=idx if c.get("direct")else doc(mr)
    if mr.get("ok"):manifests+=1
    cr={"platform":c.get("platform"),"manifest_receipt":clean(mr),"layers":[]}
    for layer in md.get("layers",[])or[]:
     if layers>=MAX_LAYERS:break
     digest=layer.get("digest")
     if not digest:continue
     layers+=1;br=req(f"{BASE}/v2/{REPO}/blobs/{digest}",a.timeout,{**auth,"Range":RANGE},MAX_COMPRESSED);body=br.get("body")or b"";ix=member_index(body)if body else{}
     if br.get("ok")and br.get("status")==206:streams+=1
     members+=ix.get("member_count",0);total+=len(body);cr["layers"].append({"descriptor":{k:layer.get(k)for k in("mediaType","digest","size")},"stream_receipt":clean(br),"range":RANGE,"tar_member_index":ix})
    rr["children"].append(cr)
   records.append(rr)
 blockers=[]
 if not ping.get("ok"):blockers.append("GHCR_V2_ENDPOINT_NOT_LIVE_ACQUIRED")
 if not token:blockers.append("GHCR_ANONYMOUS_PULL_TOKEN_NOT_ACQUIRED")
 if manifests==0:blockers.append("OVERTUREMAPS_CHILD_MANIFEST_NOT_LIVE_ACQUIRED")
 if layers==0:blockers.append("OCI_LAYER_DESCRIPTOR_NOT_ACQUIRED")
 if streams==0:blockers.append("BOUNDED_TAR_MEMBER_STREAM_NOT_ACQUIRED")
 if members==0:blockers.append("TAR_MEMBER_INDEX_NOT_PARSED")
 blockers+=["FULL_LAYER_BODY_NOT_DOWNLOADED_BY_DESIGN","THREE_OVERTURE_BUILDING_FEATURES_NOT_ACQUIRED","THREE_EXACT_UPRNS_NOT_ACQUIRED","EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"]
 excerpt=f"ping={bool(ping.get('ok'))};token={bool(token)};manifests={manifests};layers={layers};streams={streams};members={members};bytes={total}"
 runtime={"source_url":f"{BASE}/v2/{REPO}/blobs/<digest>","accessed_at":a.accessed_at,"content_sha256":sha(excerpt.encode()),"hash_scope":"normalized_runtime_receipt_utf8","record_scope":"Bounded OCI layer prefix and tar member index receipt.","supports_fields":["bounded_range","tar_member_name","tar_member_size","tar_member_typeflag","no_full_layer_body"],"relevant_record_ids_or_excerpt":excerpt,"license_or_terms_url":"https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry"}
 out={"schema_version":1,"architecture_version":3,"workstream_id":"AAYS_21_SLOT_SAFE_PARALLEL_V1","slot_id":"gas_emissions_2","wave":365,"accessed_at":a.accessed_at,"assessments":prior.get("assessments",[])[:3],"ghcr_ping":clean(ping),"token_receipt":clean(tr),"token_acquired":bool(token),"tag_records":records,"child_manifest_count":manifests,"layer_descriptor_count":layers,"bounded_stream_count":streams,"tar_member_count":members,"total_stream_bytes":total,"range_header":RANGE,"business_rows_produced":0,"parcel_rows_bound":0,"completed_count":0,"target_count":30761,"previous_percent":0.0,"current_percent":0.0,"percent_increase":0.0,"decision":"GHCR_BOTTLE_LAYER_BOUNDED_TAR_MEMBER_INDEX_ASSESSED","state":"NO_DATA_CONTINUE","blocker":";".join(blockers),"first_unverified_step":"ASSESS_GHCR_BOTTLE_LAYER_BOUNDED_TAR_MEMBER_METADATA_OR_NO_DATA_CONTINUE","source_evidence_manifest":prior.get("source_evidence_manifest",[]),"runtime_source_evidence":[runtime],"fake_data":False,"final_ready":False}
 atomic_json(a.output,out)
if __name__=="__main__":main()
