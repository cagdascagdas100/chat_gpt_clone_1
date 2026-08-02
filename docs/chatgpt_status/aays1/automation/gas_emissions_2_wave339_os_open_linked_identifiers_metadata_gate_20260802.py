#!/usr/bin/env python3
"""Wave339: bounded OS Open Linked Identifiers metadata gate."""
from __future__ import annotations
import argparse, hashlib, json, os, tempfile, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

PRODUCTS_URL="https://api.os.uk/downloads/v1/products"
RELATIONSHIP="BLPU_UPRN_TopographicArea_TOID_5"
MAX_BYTES=2_000_000
EXPECTED_IDS={"data_gov_open_linked_identifiers","os_open_linked_identifiers_product","os_open_linked_identifiers_technical_spec","os_downloads_api_download_endpoint"}
EXPECTED_INSPIRE=["46058185","46037757","45981756"]

def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def now()->str:return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
def load(path:str):
    value=json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value,dict):raise ValueError("fixture_not_object")
    return value

def evidence(f):
    if (f.get("slot_id"),f.get("wave")) != ("gas_emissions_2",339):raise ValueError("slot_wave_mismatch")
    if f.get("hmlr_inspire_ids_in_scope")!=EXPECTED_INSPIRE:raise ValueError("inspire_ids_mismatch")
    rows=f.get("source_evidence_manifest")
    if not isinstance(rows,list):raise ValueError("manifest_missing")
    by={}
    for r in rows:
        sid=str(r.get("source_id", "")); text=r.get("relevant_record_ids_or_excerpt")
        if not sid or not isinstance(text,str) or not text:raise ValueError("source_identity_missing")
        if r.get("content_sha256")!=sha(text.encode()):raise ValueError("source_hash_mismatch:"+sid)
        for k in ("publisher","source_url","accessed_at","hash_scope","record_scope","supports_fields","license_or_terms_url"):
            if not r.get(k):raise ValueError("source_field_missing:"+sid+":"+k)
        by[sid]=r
    if set(by)!=EXPECTED_IDS:raise ValueError("source_set_mismatch")
    if RELATIONSHIP not in by["os_open_linked_identifiers_technical_spec"]["relevant_record_ids_or_excerpt"]:raise ValueError("relationship_missing")
    return [by[k] for k in sorted(by)]

def get_json(url:str,timeout:int):
    req=urllib.request.Request(url,headers={"User-Agent":"AAYS-wave339/1.0","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=timeout) as res:
        body=res.read(MAX_BYTES+1)
        if len(body)>MAX_BYTES:raise ValueError("response_too_large")
        return int(getattr(res,"status",res.getcode())),json.loads(body.decode()),body,str(res.geturl())

def product(items):
    if not isinstance(items,list):return None
    ranked=[]
    for item in items:
        if not isinstance(item,dict):continue
        text=" ".join(str(v) for v in item.values() if v is not None).lower().replace("-"," ")
        ident=str(item.get("id","")).lower().replace("-","").replace("_","")
        score=(20 if "openlinkedidentifiers" in ident or "openlinkedids" in ident else 0)+(10 if "open linked identifiers" in text else 0)
        if score:ranked.append((score,item))
    return max(ranked,key=lambda x:x[0])[1] if ranked else None

def matches(items):
    out=[]
    if not isinstance(items,list):return out
    for item in items:
        if not isinstance(item,dict):continue
        text=" ".join(str(v) for v in item.values() if v is not None).lower()
        if RELATIONSHIP.lower() in text or all(t in text for t in ("blpu","uprn","topographicarea","toid")):
            out.append({k:item.get(k) for k in ("fileName","format","subformat","area","size","md5","url")})
    return out

def build(f,accessed,ps,pp,pb,purl,p,ds,dp,db,durl,error):
    sources=evidence(f); pid=None if p is None else p.get("id"); found=matches(dp)
    ok=error is None and ps==200 and isinstance(pid,str) and bool(pid) and ds==200 and bool(found)
    blocker=None if ok else "OS_DOWNLOADS_PRODUCTS_OR_OPEN_LINKED_IDENTIFIERS_DOWNLOAD_METADATA_NOT_ACQUIRED;BLPU_UPRN_TOPOGRAPHICAREA_TOID_5_PACKAGE_UNVERIFIED;THREE_EXACT_UPRNS_NOT_ACQUIRED;EXACT_OPEN_PARCEL_BINDING_REMAINS_NO_DATA_CONTINUE"
    return {"schema_version":1,"architecture_version":3,"workstream_id":"AAYS_21_SLOT_SAFE_PARALLEL_V1","slot_id":"gas_emissions_2","wave":339,"accessed_at":accessed,"state":"SOURCE_READY" if ok else "NO_DATA_CONTINUE","decision":"OS_OPEN_LINKED_IDENTIFIERS_UPRN_TO_BUILDING_TOID_METADATA_ACQUIRED" if ok else "OS_OPEN_LINKED_IDENTIFIERS_UPRN_TO_BUILDING_TOID_METADATA_NOT_ACQUIRED","blocker":blocker,"first_unverified_step":"ACQUIRE_3_EXACT_UPRNS_THEN_LOOKUP_BLPU_UPRN_TOPOGRAPHICAREA_TOID_5" if ok else "USE_NEXT_OFFICIAL_OPEN_IDENTIFIER_OR_BINDING_SOURCE_WITHOUT_GUESSING","products_url":PRODUCTS_URL,"products_http_status":ps,"products_final_url":purl,"products_content_sha256":sha(pb or b""),"products_bytes_read":len(pb or b""),"selected_product_id":pid,"selected_product_name":None if p is None else p.get("name"),"selected_product_version":None if p is None else p.get("version"),"downloads_url":None if not pid else f"{PRODUCTS_URL}/{urllib.parse.quote(str(pid),safe='')}/downloads","downloads_http_status":ds,"downloads_final_url":durl,"downloads_content_sha256":sha(db or b""),"downloads_bytes_read":len(db or b""),"relationship_id":RELATIONSHIP,"matching_download_count":len(found),"matching_downloads":found,"network_or_validation_error":error,"official_source_evidence_count":len(sources),"source_evidence_manifest":sources,"canonical_sample_rows_in_scope":3,"hmlr_inspire_ids_in_scope":EXPECTED_INSPIRE,"business_rows_produced":0,"parcel_rows_bound":0,"completed_count":0,"target_count":30761,"previous_percent":0.0,"current_percent":0.0,"percent_increase":0.0,"fake_data":False,"final_ready":False}

def write(path:str,payload):
    target=Path(path);target.parent.mkdir(parents=True,exist_ok=True);data=json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(",",":"))
    fd,tmp=tempfile.mkstemp(prefix=target.name+".",suffix=".tmp",dir=str(target.parent))
    try:
        with os.fdopen(fd,"w",encoding="utf-8",newline="\n") as h:h.write(data);h.flush();os.fsync(h.fileno())
        os.replace(tmp,target)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def self_test():
    texts={"data_gov_open_linked_identifiers":"Last updated 23 June 2026; authoritative relationships connect UPRNs, USRNs and TOIDs.","os_open_linked_identifiers_product":"Free to use for everyone; updated every six weeks; supplied as a CSV lookup table.","os_open_linked_identifiers_technical_spec":RELATIONSHIP+" links BLPU UPRN to TopographicArea TOID.","os_downloads_api_download_endpoint":"GET /products/{productId}/downloads returns OpenData download metadata or a redirect."}
    f={"slot_id":"gas_emissions_2","wave":339,"hmlr_inspire_ids_in_scope":EXPECTED_INSPIRE,"source_evidence_manifest":[{"source_id":k,"publisher":"OS","source_url":"https://example.invalid","accessed_at":"2026-08-02T12:47:00Z","content_sha256":sha(v.encode()),"hash_scope":"test","relevant_record_ids_or_excerpt":v,"record_scope":"test","supports_fields":["test"],"license_or_terms_url":"https://example.invalid/licence"} for k,v in texts.items()]}
    products=[{"id":"OpenLinkedIdentifiers","name":"OS Open Linked Identifiers","version":"1"}];downloads=[{"fileName":RELATIONSHIP+".zip","format":"CSV","url":"https://example.invalid/a.zip"}]
    r=build(f,"2026-08-02T12:47:00Z",200,products,json.dumps(products).encode(),PRODUCTS_URL,product(products),200,downloads,json.dumps(downloads).encode(),PRODUCTS_URL+"/OpenLinkedIdentifiers/downloads",None)
    assert r["state"]=="SOURCE_READY" and r["matching_download_count"]==1
    r=build(f,"2026-08-02T12:47:00Z",None,None,None,None,None,None,None,None,None,"URLError:test")
    assert r["state"]=="NO_DATA_CONTINUE" and r["business_rows_produced"]==0
    print("SELF_TEST_PASS")

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--fixture");ap.add_argument("--output");ap.add_argument("--timeout",type=int,default=30);ap.add_argument("--self-test",action="store_true");a=ap.parse_args()
    if a.self_test:self_test();return
    if not a.fixture or not a.output:ap.error("--fixture and --output required")
    f=load(a.fixture);ps=pp=pb=purl=p=ds=dp=db=durl=None;error=None
    try:
        ps,pp,pb,purl=get_json(PRODUCTS_URL,a.timeout);p=product(pp)
        if p is None or not p.get("id"):raise ValueError("open_linked_identifiers_product_not_found")
        ds,dp,db,durl=get_json(f"{PRODUCTS_URL}/{urllib.parse.quote(str(p['id']),safe='')}/downloads",a.timeout)
    except (urllib.error.URLError,urllib.error.HTTPError,TimeoutError,OSError,ValueError,json.JSONDecodeError) as exc:error=f"{type(exc).__name__}:{exc}"
    r=build(f,now(),ps,pp,pb,purl,p,ds,dp,db,durl,error);write(a.output,r)
    print("DECISION="+r["decision"]);print("MATCHING_DOWNLOAD_COUNT="+str(r["matching_download_count"]));print("BUSINESS_ROWS_PRODUCED=0")
if __name__=="__main__":main()
