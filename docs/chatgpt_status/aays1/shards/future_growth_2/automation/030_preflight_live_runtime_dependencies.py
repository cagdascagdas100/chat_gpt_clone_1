#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, socket, urllib.request
from pathlib import Path
from typing import Callable, Any

PLANNING_URL="https://www.planning.data.gov.uk/entity.json?entity=1739891&dataset=brownfield-land&period=current&limit=2"
HMLR_URL="https://use-land-property-data.service.gov.uk/datasets/inspire/download"
PLANNING_HOST="www.planning.data.gov.uk"
HMLR_HOST="use-land-property-data.service.gov.uk"
DEFAULT_CANONICAL_GIT_BLOB_SHA="8afd1d2bac414cf0f6b9484014e7878a4ceff877"
DEFAULT_MIN_BYTES=50_000_000

def git_blob_sha(path: Path) -> str:
    size=path.stat().st_size; h=hashlib.sha1(); h.update(f"blob {size}\0".encode())
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def validate_canonical(path: Path, expected_blob_sha: str, min_bytes: int=DEFAULT_MIN_BYTES) -> dict[str,Any]:
    if not path.exists(): return {"state":"MISSING","ready":False,"path":str(path)}
    if not path.is_file(): return {"state":"NOT_A_FILE","ready":False,"path":str(path)}
    size=path.stat().st_size
    if size < min_bytes: return {"state":"TOO_SMALL","ready":False,"path":str(path),"bytes":size,"minimum_bytes":min_bytes}
    actual=git_blob_sha(path)
    if actual != expected_blob_sha: return {"state":"GIT_BLOB_SHA_MISMATCH","ready":False,"path":str(path),"bytes":size,"expected_git_blob_sha":expected_blob_sha,"actual_git_blob_sha":actual}
    return {"state":"PRESENT_GIT_BLOB_SHA_MATCH","ready":True,"path":str(path),"bytes":size,"git_blob_sha":actual}

def probe_https(url: str, expected_host: str, expected_types: tuple[str,...], timeout: float=15.0, resolver: Callable=socket.getaddrinfo, opener: Callable=urllib.request.urlopen) -> dict[str,Any]:
    from urllib.parse import urlparse
    parsed=urlparse(url)
    if parsed.scheme!="https" or parsed.hostname!=expected_host:
        return {"state":"URL_POLICY_REJECTED","ready":False,"url":url}
    try: resolver(expected_host,443)
    except Exception as exc: return {"state":"DNS_BLOCKED","ready":False,"url":url,"error":f"{type(exc).__name__}: {exc}"}
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"TerraYield-AAYS-future-growth-2-preflight/1.0"})
        with opener(req,timeout=timeout) as r:
            status=int(getattr(r,"status",0)); ctype=str(r.headers.get("content-type") or "").lower(); sample=r.read(256)
        if status!=200: return {"state":"HTTP_STATUS_REJECTED","ready":False,"url":url,"status":status,"content_type":ctype}
        if not any(t in ctype for t in expected_types): return {"state":"CONTENT_TYPE_REJECTED","ready":False,"url":url,"status":status,"content_type":ctype}
        return {"state":"REACHABLE_POLICY_VALIDATED","ready":True,"url":url,"status":status,"content_type":ctype,"sample_bytes":len(sample)}
    except Exception as exc: return {"state":"HTTP_BLOCKED","ready":False,"url":url,"error":f"{type(exc).__name__}: {exc}"}

def build_result(canonical: dict, planning: dict, hmlr: dict) -> dict:
    ready=bool(canonical.get("ready") and planning.get("ready") and hmlr.get("ready"))
    return {"schema_version":1,"slot_id":"future_growth_2","executed":True,"canonical":canonical,"planning_period_current":planning,"hmlr_index":hmlr,"ready_for_live_chain":ready,"actual_period_current_api_responses":0,"actual_hmlr_downloads":0,"actual_exact_intersections":0,"canonical_rows_exported":0,"canonical_parcel_matches":0,"future_growth_scores_produced":0,"actual_business_data_rows_written":0,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}

def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("--canonical-source",type=Path,required=True); p.add_argument("--expected-git-blob-sha",default=DEFAULT_CANONICAL_GIT_BLOB_SHA); p.add_argument("--minimum-bytes",type=int,default=DEFAULT_MIN_BYTES); p.add_argument("--output",type=Path,required=True); p.add_argument("--timeout",type=float,default=15.0); a=p.parse_args()
    result=build_result(validate_canonical(a.canonical_source,a.expected_git_blob_sha,a.minimum_bytes),probe_https(PLANNING_URL,PLANNING_HOST,("application/json","+json"),a.timeout),probe_https(HMLR_URL,HMLR_HOST,("text/html","application/xhtml+xml"),a.timeout))
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); print(json.dumps(result)); return 0 if result["ready_for_live_chain"] else 2
if __name__=="__main__": raise SystemExit(main())
