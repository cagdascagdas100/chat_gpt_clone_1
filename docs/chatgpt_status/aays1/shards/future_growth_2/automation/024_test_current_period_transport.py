#!/usr/bin/env python3
from __future__ import annotations
import argparse, importlib.util, json, urllib.error
from pathlib import Path

class Headers(dict):
    def get(self,k,default=None): return super().get(k,default)
class Response:
    def __init__(self, body=b'{"entities":[]}', status=200, ctype="application/json", url="https://www.planning.data.gov.uk/entity.json"):
        self.body=body; self.status=status; self.headers=Headers({"Content-Type":ctype}); self.url=url
    def read(self,n=-1): return self.body if n<0 else self.body[:n]
    def geturl(self): return self.url
    def __enter__(self): return self
    def __exit__(self,*a): return False

def load(path):
    spec=importlib.util.spec_from_file_location("current",path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def main():
    p=argparse.ArgumentParser(); p.add_argument("--script",type=Path,required=True); p.add_argument("--output",type=Path,required=True); a=p.parse_args()
    m=load(a.script); checks=[]
    def check(name,fn,expected=None):
        try:
            fn(); passed=expected is None; detail="" if passed else "expected error not raised"
        except Exception as exc:
            passed=expected is not None and expected in str(exc); detail=f"{type(exc).__name__}: {exc}"
        checks.append({"check":name,"passed":passed,"detail":detail})
    url=m.build_current_url(1717096)
    check("url_https_official_host",lambda: (_ for _ in ()).throw(AssertionError(url)) if not url.startswith("https://www.planning.data.gov.uk/entity.json?") else None)
    check("url_period_current_exact",lambda: (_ for _ in ()).throw(AssertionError(url)) if "period=current" not in url else None)
    check("url_dataset_and_limit",lambda: (_ for _ in ()).throw(AssertionError(url)) if "dataset=brownfield-land" not in url or "limit=2" not in url else None)
    check("invalid_entity_rejected",lambda:m.build_current_url(0),"positive")
    check("valid_json_response",lambda:m.fetch_current(1,1,retries=1,opener=lambda req,timeout:Response()))
    check("vendor_json_response",lambda:m.fetch_current(1,1,retries=1,opener=lambda req,timeout:Response(ctype="application/problem+json")))
    check("html_content_type_rejected",lambda:m.fetch_current(1,1,retries=1,opener=lambda req,timeout:Response(ctype="text/html")),"not JSON")
    check("off_host_redirect_rejected",lambda:m.fetch_current(1,1,retries=1,opener=lambda req,timeout:Response(url="https://evil.example/entity.json")),"redirected off")
    check("wrong_path_redirect_rejected",lambda:m.fetch_current(1,1,retries=1,opener=lambda req,timeout:Response(url="https://www.planning.data.gov.uk/other")),"redirected off")
    check("invalid_json_rejected",lambda:m.fetch_current(1,1,retries=1,opener=lambda req,timeout:Response(body=b"{")),"valid UTF-8 JSON")
    check("non_object_json_rejected",lambda:m.fetch_current(1,1,retries=1,opener=lambda req,timeout:Response(body=b"[]")),"not an object")
    oversized=b'{"x":"' + b'a'*(m.MAX_RESPONSE_BYTES+10) + b'"}'
    check("oversized_response_rejected",lambda:m.fetch_current(1,1,retries=1,opener=lambda req,timeout:Response(body=oversized)),"exceeds")
    calls={"n":0}
    def transient(req,timeout):
        calls["n"]+=1
        if calls["n"]==1: raise urllib.error.HTTPError(req.full_url,503,"x",None,None)
        return Response()
    check("transient_http_retried",lambda:m.fetch_current(1,1,retries=2,opener=transient,sleeper=lambda x:None))
    def notfound(req,timeout): raise urllib.error.HTTPError(req.full_url,404,"x",None,None)
    check("nontransient_http_not_retried",lambda:m.fetch_current(1,1,retries=3,opener=notfound,sleeper=lambda x:None),"HTTP 404")
    out={"schema_version":1,"slot_id":"future_growth_2","executed":True,"test_type":"planning_data_period_current_transport_regression",
         "checks_passed":sum(c["passed"] for c in checks),"checks_total":len(checks),"all_passed":all(c["passed"] for c in checks),
         "checks":checks,"actual_live_period_current_responses":0,"canonical_parcel_matches":0,
         "future_growth_scores_produced":0,"actual_business_data_rows_written":0,
         "final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(out)); return 0 if out["all_passed"] else 1
if __name__=="__main__": raise SystemExit(main())
