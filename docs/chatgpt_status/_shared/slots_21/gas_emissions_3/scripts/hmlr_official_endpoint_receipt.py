#!/usr/bin/env python3
"""Fail-closed validator for official HMLR INSPIRE authority ZIP endpoints."""
from __future__ import annotations
import argparse, hashlib, http.cookiejar, json, ssl
import urllib.error, urllib.parse, urllib.request
from pathlib import Path

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def args():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True,type=Path); p.add_argument("--manifest",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path); p.add_argument("--expected-slot",default="gas_emissions_3")
    p.add_argument("--expected-target-count",type=int,default=2)
    p.add_argument("--expected-input-sha256",required=True); p.add_argument("--expected-manifest-sha256",required=True)
    p.add_argument("--fixture-json",type=Path)
    return p.parse_args()

def receipt(url:str, timeout:int, agent:str)->dict:
    jar=http.cookiejar.CookieJar()
    opener=urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(jar),
        urllib.request.HTTPSHandler(context=ssl.create_default_context()),
        NoRedirect(),
    )
    req=urllib.request.Request(url,method="GET",headers={
        "User-Agent":agent,"Accept":"application/zip,application/octet-stream,*/*;q=0.5","Range":"bytes=0-3"})
    try:
        with opener.open(req,timeout=timeout) as r:
            prefix=r.read(4)
            return {"request_completed":True,"receipt_state":"DIRECT_ZIP" if prefix.startswith(b"PK") else "HTTP_RESPONSE",
                    "http_status":int(getattr(r,"status",200)),"location":None,"content_type":r.headers.get("Content-Type",""),
                    "zip_magic_verified":prefix.startswith(b"PK"),"error_type":None,"error":None}
    except urllib.error.HTTPError as e:
        loc=e.headers.get("Location") if e.headers else None; u=urllib.parse.urlparse(loc or "")
        ok=300<=int(e.code)<400 and u.scheme=="https" and bool(u.netloc)
        return {"request_completed":True,"receipt_state":"HTTPS_REDIRECT" if ok else "HTTP_ERROR",
                "http_status":int(e.code),"location":loc,"content_type":e.headers.get("Content-Type","") if e.headers else "",
                "zip_magic_verified":False,"error_type":None if ok else type(e).__name__,
                "error":None if ok else str(e)[:500]}
    except (urllib.error.URLError,TimeoutError,OSError) as e:
        return {"request_completed":True,"receipt_state":"NO_DATA_CONTINUE","http_status":None,"location":None,
                "content_type":None,"zip_magic_verified":False,"error_type":type(e).__name__,"error":str(e)[:500]}

def validate(t:dict,r:dict)->dict:
    ep=urllib.parse.urlparse(t["endpoint_url"]); loc=urllib.parse.urlparse(r.get("location") or "")
    path_ok=(ep.scheme=="https" and ep.netloc=="use-land-property-data.service.gov.uk"
             and ep.path.startswith("/datasets/inspire/download/") and ep.path.endswith(".zip"))
    redirect_ok=r.get("receipt_state")=="HTTPS_REDIRECT" and loc.scheme=="https" and bool(loc.netloc)
    zip_ok=r.get("receipt_state")=="DIRECT_ZIP" and r.get("zip_magic_verified") is True
    ok=path_ok and (redirect_ok or zip_ok)
    return {"target_id":t["target_id"],"authority_name":t["authority_name"],"endpoint_url":t["endpoint_url"],
            "attempt_completed":bool(r.get("request_completed")),"endpoint_path_valid":path_ok,
            "endpoint_receipt_verified":ok,"receipt_state":r.get("receipt_state"),"http_status":r.get("http_status"),
            "redirect_location":r.get("location"),"content_type":r.get("content_type"),
            "zip_magic_verified":bool(r.get("zip_magic_verified")),"error_type":r.get("error_type"),
            "error":r.get("error"),"decision":"ENDPOINT_VERIFIED" if ok else "NO_DATA_CONTINUE"}

def main()->int:
    a=args(); ib=a.input.read_bytes(); mb=a.manifest.read_bytes()
    if sha(ib)!=a.expected_input_sha256: raise ValueError("input SHA mismatch")
    if sha(mb)!=a.expected_manifest_sha256: raise ValueError("manifest SHA mismatch")
    prev=json.loads(ib); man=json.loads(mb)
    if prev.get("slot_id")!=a.expected_slot or prev.get("state")!="NO_DATA_CONTINUE": raise ValueError("bad input")
    if prev.get("next_unverified_step")!="ACQUIRE_OFFICIAL_HMLR_DOWNLOAD_PAGE_HTML_OR_DIRECT_HREF_EVIDENCE": raise ValueError("bad prerequisite")
    if man.get("schema_version")!=3 or man.get("slot_id")!=a.expected_slot or man.get("input_sha256")!=a.expected_input_sha256:
        raise ValueError("bad manifest")
    targets=man.get("target_records")
    if not isinstance(targets,list) or len(targets)!=a.expected_target_count: raise ValueError("target count mismatch")
    fixtures=json.loads(a.fixture_json.read_text())["receipts"] if a.fixture_json else None
    results=[validate(t,fixtures[t["target_id"]] if fixtures else receipt(
        t["endpoint_url"],int(man["network_policy"]["timeout_seconds"]),man["network_policy"]["user_agent"])) for t in targets]
    completed=sum(x["attempt_completed"] for x in results); verified=sum(x["endpoint_receipt_verified"] for x in results)
    state="ENDPOINTS_VERIFIED" if verified==a.expected_target_count else "NO_DATA_CONTINUE"
    out={"schema_version":3,"architecture_version":3,"workstream_id":"AAYS_21_SLOT_SAFE_PARALLEL_V1",
         "slot_id":a.expected_slot,"task_batch":261,"state":state,
         "result":"OFFICIAL_HMLR_ENDPOINT_RECEIPTS_ATTEMPTED_FAIL_CLOSED",
         "first_unverified_step_completed":"ACQUIRE_OFFICIAL_HMLR_DOWNLOAD_PAGE_HTML_OR_DIRECT_HREF_EVIDENCE",
         "next_unverified_step":"DOWNLOAD_AND_VALIDATE_HMLR_GML_ARCHIVES" if state=="ENDPOINTS_VERIFIED"
             else "RETRY_OFFICIAL_HMLR_ENDPOINT_RECEIPTS_FROM_NETWORK_WITH_WORKING_DNS",
         "input":{"path":a.input.as_posix(),"sha256":sha(ib),"manifest_path":a.manifest.as_posix(),"manifest_sha256":sha(mb)},
         "counts":{"completed_count":completed,"target_count":a.expected_target_count,"official_endpoint_attempts":completed,
                   "official_endpoint_receipts_verified":verified,"raw_gml_archives_downloaded":0,"raw_gml_files_downloaded":0,
                   "raw_polygon_geometries":0,"verified_inspire_ids":0,"parcel_bindings":0},
         "decision":{"endpoint_gate_passed":verified==a.expected_target_count,"https_official_endpoint_path_required":True,
                     "https_redirect_or_zip_magic_required":True,"inferred_values":0,"fake_data":False},"targets":results}
    a.output.parent.mkdir(parents=True,exist_ok=True); tmp=a.output.with_suffix(a.output.suffix+".tmp")
    tmp.write_text(json.dumps(out,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8"); tmp.replace(a.output)
    return 0

if __name__=="__main__": raise SystemExit(main())
