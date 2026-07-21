#!/usr/bin/env python3
"""HTTP 8012 and static DOM-contract acceptance for the internet_access_3 review page.

This proves page and JSON reachability/consistency. Browser-console and polygon-popup
acceptance remain separate gates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SLOT_ID="internet_access_3"
DEFAULT_BASE_URL="http://127.0.0.1:8012/data/aays_18_slots/internet_access_3/"
REQUIRED_DOM_IDS=('id="metrics"','id="operations"','id="runtime"','id="runtimeResults"','id="runtimeSamples"','id="directZip"','id="targeted"','id="blobs"','id="publish"','id="runner"','id="sources"','id="examples"')
JSON_ENDPOINTS=("progress_latest.json","operations_latest.json","runtime_bundle_latest.json","runtime_results_latest.json","runner_task_latest.json","source_candidates_latest.json","examples_latest.json","remote_publish_latest.json")

class GateError(RuntimeError): pass

def require(condition: bool, message: str) -> None:
    if not condition: raise GateError(message)

def sha256_bytes(value: bytes) -> str: return hashlib.sha256(value).hexdigest()

def fetch_bytes(url: str, *, timeout: float, retries: int, max_bytes: int=8_000_000) -> tuple[bytes,str]:
    last_error: Exception|None=None
    for attempt in range(1,retries+1):
        try:
            request=urllib.request.Request(url,headers={"User-Agent":"internet_access_3-http-acceptance/1"})
            with urllib.request.urlopen(request,timeout=timeout) as response:
                status=int(getattr(response,"status",response.getcode())); require(status==200,f"{url}: HTTP {status}")
                content_type=response.headers.get("Content-Type",""); body=response.read(max_bytes+1)
                require(len(body)<=max_bytes,f"{url}: response too large"); require(len(body)>0,f"{url}: empty response")
                return body,content_type
        except Exception as exc:
            last_error=exc
            if attempt<retries: time.sleep(min(.25*attempt,1.0))
    raise GateError(f"{url}: fetch failed after {retries} attempts: {last_error}")

def load_json_bytes(body: bytes, name: str) -> dict[str,Any]:
    try: value=json.loads(body.decode("utf-8-sig"))
    except Exception as exc: raise GateError(f"{name}: invalid UTF-8 JSON: {exc}") from exc
    require(isinstance(value,dict),f"{name}: JSON object required"); require(value.get("slot_id")==SLOT_ID,f"{name}: wrong slot_id"); return value

def validate_documents(index_html: str, documents: dict[str,dict[str,Any]]) -> dict[str,Any]:
    for marker in REQUIRED_DOM_IDS: require(marker in index_html,f"index.html missing DOM marker {marker}")
    require("Görünüm yüklenemedi" in index_html,"index.html lacks explicit load-error rendering"); require("undefined" not in index_html,"index.html contains literal undefined")
    progress=documents["progress_latest.json"]; operations=documents["operations_latest.json"]; runtime=documents["runtime_bundle_latest.json"]; runtime_results=documents["runtime_results_latest.json"]; runner=documents["runner_task_latest.json"]; sources=documents["source_candidates_latest.json"]; examples=documents["examples_latest.json"]; publish=documents["remote_publish_latest.json"]
    require(progress.get("display_state")=="progress_not_final","progress display_state"); require(progress.get("final_ready") is False,"progress final_ready"); require(int(progress.get("completed_operations",-1))==7,"completed operations"); require(int(progress.get("total_operations",-1))==12,"total operations"); require(int(progress.get("verified_product_rows",-1))==0,"product rows must remain zero before real runtime"); require(int(progress.get("actual_business_data_rows_written",-1))==0,"business rows must be zero")
    operation_rows=operations.get("operations"); require(isinstance(operation_rows,list) and len(operation_rows)==12,"exactly 12 operation rows required"); require([int(row.get("operation_no",-1)) for row in operation_rows]==list(range(1,13)),"operation numbering must be contiguous")
    gates=runtime.get("gates"); require(isinstance(gates,list) and len(gates)>=8,"runtime preparation gates missing"); require(runtime.get("remote_runner_execution") is False,"runtime bundle must not claim remote execution")
    require(runtime_results.get("status") in ("WAITING_REAL_RUNTIME_BUNDLE","REAL_RUNTIME_BUNDLE_VALIDATED_REVIEW_ONLY"),"runtime results status"); real_rows=int(runtime_results.get("real_runtime_rows_validated",-1)); require(real_rows in (0,30_761),"runtime result row count must be 0 or 30,761")
    if real_rows==0: require(runtime_results.get("final_ready") is False,"waiting runtime result final_ready")
    else: require(isinstance(runtime_results.get("samples"),list) and runtime_results["samples"],"real runtime samples missing")
    require(runner.get("single_shared_runner_only") is True,"single-runner contract"); require(runner.get("create_new_runner") is False,"new runner forbidden"); require(runner.get("queue_submission") is False,"queue submission must remain false")
    candidate_count=int(sources.get("candidate_count",-1)); promoted_count=int(sources.get("promoted_count",-1)); require(candidate_count>=10 and promoted_count>=9,"official source refresh not visible"); require(len(sources.get("candidates") or [])==candidate_count,"source candidate count mismatch")
    example_count=int(examples.get("example_count",-1)); require(example_count>=13,"expanded examples not visible"); require(len(examples.get("examples") or [])==example_count,"example count mismatch"); require(int(examples.get("verified_product_example_rows",-1))==0,"aggregate examples must not be product rows")
    require(publish.get("authoritative_remote_publish") is True,"authoritative publish evidence missing"); require(publish.get("http_8012_acceptance") is False,"pre-acceptance record must remain false until this receipt is published")
    return {"operation_rows":len(operation_rows),"runtime_preparation_gates":len(gates),"runtime_rows_visible":real_rows,"source_candidates_visible":candidate_count,"promoted_sources_visible":promoted_count,"examples_visible":example_count}

def run_acceptance(base_url: str, *, timeout: float, retries: int) -> dict[str,Any]:
    base=base_url if base_url.endswith("/") else base_url+"/"; index_url=urllib.parse.urljoin(base,"index.html"); index_body,index_type=fetch_bytes(index_url,timeout=timeout,retries=retries); index_text=index_body.decode("utf-8-sig")
    documents: dict[str,dict[str,Any]]={}; endpoint_receipts=[{"path":"index.html","url":index_url,"bytes":len(index_body),"sha256":sha256_bytes(index_body),"content_type":index_type,"state":"PASS"}]
    for name in JSON_ENDPOINTS:
        url=urllib.parse.urljoin(base,name); body,content_type=fetch_bytes(url,timeout=timeout,retries=retries); documents[name]=load_json_bytes(body,name); endpoint_receipts.append({"path":name,"url":url,"bytes":len(body),"sha256":sha256_bytes(body),"content_type":content_type,"state":"PASS"})
    visible=validate_documents(index_text,documents)
    return {"schema_version":1,"slot_id":SLOT_ID,"state":"PASS_HTTP_8012_AND_STATIC_DOM_CONTRACT","accepted_at":datetime.now(timezone.utc).isoformat(),"base_url":base,"endpoints":endpoint_receipts,"visible_counts":visible,"http_8012_acceptance":True,"static_dom_contract_acceptance":True,"browser_console_acceptance":False,"polygon_popup_acceptance":False,"actual_business_data_rows_written":0,"scores_written":0,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False,"final_ready":False}

def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("--base-url",default=DEFAULT_BASE_URL); parser.add_argument("--output",required=True,type=Path); parser.add_argument("--timeout-seconds",type=float,default=10.0); parser.add_argument("--retries",type=int,default=2); args=parser.parse_args()
    require(args.timeout_seconds>0,"timeout must be positive"); require(1<=args.retries<=5,"retries must be between 1 and 5")
    receipt=run_acceptance(args.base_url,timeout=args.timeout_seconds,retries=args.retries); args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); print(json.dumps({"state":receipt["state"],"visible_counts":receipt["visible_counts"]},sort_keys=True)); return 0

if __name__=="__main__": raise SystemExit(main())
