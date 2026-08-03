#!/usr/bin/env python3
"""Wave364: bounded GHCR bottle-layer tar header stream gate; never downloads a full layer."""
from __future__ import annotations
import argparse, gzip, hashlib, io, json, os, tempfile, time
import urllib.error, urllib.parse, urllib.request
from pathlib import Path

BASE="https://ghcr.io"
REPO="homebrew/core/overturemaps"
TAGS=["1.0.1_1","1.0.1"]
MAX_CHILD=4
MAX_LAYERS=4
MAX_COMPRESSED=65536
MAX_DECOMPRESSED=131072
RANGE=f"bytes=0-{MAX_COMPRESSED-1}"
ACCEPT=", ".join([
 "application/vnd.oci.image.index.v1+json",
 "application/vnd.docker.distribution.manifest.list.v2+json",
 "application/vnd.oci.image.manifest.v1+json",
 "application/vnd.docker.distribution.manifest.v2+json",
])

def sha(b: bytes)->str: return hashlib.sha256(b).hexdigest()

def atomic_json(path: str, obj: dict)->None:
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    raw=(json.dumps(obj,sort_keys=True,separators=(",",":"))+"\n").encode()
    with tempfile.NamedTemporaryFile(dir=p.parent,delete=False) as h:
        h.write(raw); n=h.name
    os.replace(n,p)

def req(url:str,timeout:int,headers:dict|None=None,max_bytes:int=0)->dict:
    started=time.monotonic()
    r=urllib.request.Request(url,headers={"User-Agent":"AAYS-W364","Accept-Encoding":"identity",**(headers or {})})
    try:
        with urllib.request.urlopen(r,timeout=timeout) as x:
            b=x.read(max_bytes+1)
            if len(b)>max_bytes: raise ValueError("RESPONSE_EXCEEDED_BOUND")
            return {"ok":True,"status":getattr(x,"status",None),"url":url,"bytes":len(b),
                    "body_sha256":sha(b),"headers":{k.lower():v for k,v in x.headers.items()
                    if k.lower() in {"content-range","content-length","content-type","docker-content-digest","location"}},
                    "body":b,"seconds":round(time.monotonic()-started,3)}
    except urllib.error.HTTPError as e:
        return {"ok":False,"status":e.code,"url":url,"bytes":0,"error":f"HTTPError:{e.code}:{e.reason}",
                "seconds":round(time.monotonic()-started,3)}
    except Exception as e:
        return {"ok":False,"url":url,"bytes":0,"error":f"{type(e).__name__}:{e}",
                "seconds":round(time.monotonic()-started,3)}

def clean(r:dict)->dict: return {k:v for k,v in r.items() if k!="body"}

def parse_json(r:dict)->dict:
    try: return json.loads((r.get("body") or b"").decode())
    except Exception: return {}

def bounded_tar_headers(blob:bytes)->dict:
    compression="UNKNOWN"; data=b""
    try:
        if blob.startswith(b"\x1f\x8b"):
            compression="GZIP"
            with gzip.GzipFile(fileobj=io.BytesIO(blob)) as g:
                data=g.read(MAX_DECOMPRESSED+1)
        elif len(blob)>=262 and blob[257:262]==b"ustar":
            compression="TAR"; data=blob
        else:
            return {"compression_magic":compression,"tar_header_count":0,"tar_names":[],"decompressed_bytes":0}
    except Exception as e:
        return {"compression_magic":compression,"tar_header_count":0,"tar_names":[],"decompressed_bytes":0,
                "bounded_decode_error":f"{type(e).__name__}:{e}"}
    if len(data)>MAX_DECOMPRESSED:
        return {"compression_magic":compression,"tar_header_count":0,"tar_names":[],"decompressed_bytes":len(data),
                "bounded_decode_error":"DECOMPRESSED_BOUND_EXCEEDED"}
    names=[]
    for offset in range(0,max(0,len(data)-511),512):
        block=data[offset:offset+512]
        if not block or block==b"\0"*512: break
        name=block[:100].split(b"\0",1)[0].decode("utf-8","replace")
        if name: names.append(name)
        if len(names)>=8: break
    return {"compression_magic":compression,"tar_header_count":len(names),"tar_names":names,
            "decompressed_bytes":len(data),"decompressed_sha256":sha(data)}

def self_test()->None:
    header=bytearray(512); header[:8]=b"file.txt"; header[257:262]=b"ustar"
    raw=bytes(header)+b"\0"*512
    a=bounded_tar_headers(gzip.compress(raw))
    assert a["compression_magic"]=="GZIP" and a["tar_header_count"]==1 and a["tar_names"][0]=="file.txt"
    assert RANGE=="bytes=0-65535"
    print("SELF_TEST_PASS")

def main()->None:
    p=argparse.ArgumentParser()
    p.add_argument("--canonical"); p.add_argument("--fixture"); p.add_argument("--output")
    p.add_argument("--timeout",type=int,default=20); p.add_argument("--accessed-at"); p.add_argument("--self-test",action="store_true")
    a=p.parse_args()
    if a.self_test: self_test(); return
    canonical=json.load(open(a.canonical,encoding="utf-8"))
    fixture=json.load(open(a.fixture,encoding="utf-8"))
    assessments=[]
    for row in canonical["rows"][:3]:
        q=row["properties"]; assessments.append({"parcel_id":q["parcel_id"],"hmlr_inspire_id":q["hmlr_inspire_id"],
        "longitude":q["hmlr_lon"],"latitude":q["hmlr_lat"]})
    ping=req(BASE+"/v2/",a.timeout,max_bytes=64000)
    token_url=BASE+"/token?"+urllib.parse.urlencode({"service":"ghcr.io","scope":f"repository:{REPO}:pull"})
    tr=req(token_url,a.timeout,max_bytes=256000); td=parse_json(tr); token=td.get("token") or td.get("access_token")
    auth={"Authorization":f"Bearer {token}"} if token else {}
    records=[]; manifests=layers=streams=headers=total=0
    if token:
        for tag in TAGS:
            ir=req(f"{BASE}/v2/{REPO}/manifests/{tag}",a.timeout,{**auth,"Accept":ACCEPT},1000000)
            doc=parse_json(ir); children=[m for m in doc.get("manifests",[]) if (m.get("platform") or {}).get("os")=="linux"][:MAX_CHILD]
            if not children and doc.get("layers"): children=[{"digest":tag,"direct":True,"platform":{}}]
            rr={"tag":tag,"index_receipt":clean(ir),"children":[]}
            for c in children:
                mr=ir if c.get("direct") else req(f"{BASE}/v2/{REPO}/manifests/{c['digest']}",a.timeout,{**auth,"Accept":ACCEPT},1000000)
                md=doc if c.get("direct") else parse_json(mr)
                if mr.get("ok"): manifests+=1
                cr={"platform":c.get("platform"),"manifest_receipt":clean(mr),"layers":[]}
                for layer in (md.get("layers") or []):
                    if layers>=MAX_LAYERS: break
                    digest=layer.get("digest")
                    if not digest: continue
                    layers+=1
                    br=req(f"{BASE}/v2/{REPO}/blobs/{digest}",a.timeout,{**auth,"Range":RANGE},MAX_COMPRESSED)
                    body=br.get("body") or b""; parsed=bounded_tar_headers(body) if body else {}
                    if br.get("ok") and br.get("status")==206: streams+=1
                    headers+=parsed.get("tar_header_count",0); total+=len(body)
                    cr["layers"].append({"descriptor":{k:layer.get(k) for k in ("mediaType","digest","size")},
                                         "stream_receipt":clean(br),"range":RANGE,"tar_header_assessment":parsed})
                rr["children"].append(cr)
            records.append(rr)
    blockers=[]
    if not ping.get("ok"): blockers.append("GHCR_V2_ENDPOINT_NOT_LIVE_ACQUIRED")
    if not token: blockers.append("GHCR_ANONYMOUS_PULL_TOKEN_NOT_ACQUIRED")
    if manifests==0: blockers.append("OVERTUREMAPS_CHILD_MANIFEST_NOT_LIVE_ACQUIRED")
    if layers==0: blockers.append("OCI_LAYER_DESCRIPTOR_NOT_ACQUIRED")
    if streams==0: blockers.append("BOUNDED_TAR_HEADER_STREAM_NOT_ACQUIRED")
    if headers==0: blockers.append("TAR_HEADER_NOT_PARSED")
    blockers += ["FULL_LAYER_BODY_NOT_DOWNLOADED_BY_DESIGN","THREE_BOUNDED_BBOX_STREAMS_NOT_COMPLETED",
                 "THREE_OVERTURE_BUILDING_FEATURES_NOT_ACQUIRED","THREE_EXACT_UPRNS_NOT_ACQUIRED",
                 "EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"]
    excerpt=f"ping={bool(ping.get('ok'))};token={bool(token)};manifests={manifests};layers={layers};streams={streams};tar_headers={headers};bytes={total}"
    runtime={"source_url":f"{BASE}/v2/{REPO}/blobs/<digest>","accessed_at":a.accessed_at,
      "content_sha256":sha(excerpt.encode()),"supports_fields":["bounded_range","compression_magic","tar_header_name","no_full_layer_body"],
      "relevant_record_ids_or_excerpt":excerpt,
      "license_or_terms_url":"https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry"}
    out={"schema_version":1,"architecture_version":3,"workstream_id":"AAYS_21_SLOT_SAFE_PARALLEL_V1","slot_id":"gas_emissions_2",
      "wave":364,"accessed_at":a.accessed_at,"assessments":assessments,"ghcr_ping":clean(ping),"token_receipt":clean(tr),
      "token_acquired":bool(token),"tag_records":records,"child_manifest_count":manifests,"layer_descriptor_count":layers,
      "bounded_stream_count":streams,"tar_header_count":headers,"total_stream_bytes":total,"range_header":RANGE,
      "business_rows_produced":0,"parcel_rows_bound":0,"completed_count":0,"target_count":30761,
      "previous_percent":0.0,"current_percent":0.0,"percent_increase":0.0,
      "decision":"GHCR_BOTTLE_LAYER_BOUNDED_TAR_HEADER_STREAM_ASSESSED","state":"NO_DATA_CONTINUE",
      "blocker":";".join(blockers),"first_unverified_step":"ASSESS_GHCR_BOTTLE_LAYER_BOUNDED_TAR_MEMBER_INDEX_OR_NO_DATA_CONTINUE",
      "source_evidence_manifest":fixture["source_evidence_manifest"],"runtime_source_evidence":[runtime],
      "fake_data":False,"final_ready":False}
    atomic_json(a.output,out)

if __name__=="__main__": main()
