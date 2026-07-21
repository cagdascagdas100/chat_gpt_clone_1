#!/usr/bin/env python3
"""HTTP 8012 and static DOM-contract acceptance for internet_access_3 review page."""
from __future__ import annotations
import argparse,hashlib,json,time,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path
from typing import Any
SLOT_ID="internet_access_3"
DEFAULT_BASE_URL="http://127.0.0.1:8012/data/aays_18_slots/internet_access_3/"
REQUIRED_DOM_IDS=('id="metrics"','id="operations"','id="runtime"','id="runtimeResults"','id="runtimeSamples"','id="reproducibility"','id="executionLock"','id="directZip"','id="targeted"','id="polygon"','id="eligibility"','id="blobs"','id="publish"','id="runner"','id="sources"','id="examples"')
JSON_ENDPOINTS=("progress_latest.json","operations_latest.json","runtime_bundle_latest.json","runtime_results_latest.json","runtime_reproducibility_latest.json","execution_lock_latest.json","runner_eligibility_latest.json","polygon_popup_acceptance_latest.json","runner_task_latest.json","source_candidates_latest.json","examples_latest.json","remote_publish_latest.json")
class GateError(RuntimeError):pass
def require(c,m):
    if not c:raise GateError(m)
def sha256_bytes(v:bytes)->str:return hashlib.sha256(v).hexdigest()
def fetch_bytes(url:str,*,timeout:float,retries:int,max_bytes:int=8_000_000)->tuple[bytes,str]:
    last=None
    for attempt in range(1,retries+1):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"internet_access_3-http-acceptance/3"})
            with urllib.request.urlopen(req,timeout=timeout) as response:
                status=int(getattr(response,"status",response.getcode()));require(status==200,f"{url}: HTTP {status}")
                ctype=response.headers.get("Content-Type","");body=response.read(max_bytes+1);require(len(body)<=max_bytes,f"{url}: response too large");require(body,f"{url}: empty response");return body,ctype
        except Exception as exc:
            last=exc
            if attempt<retries:time.sleep(min(.25*attempt,1.0))
    raise GateError(f"{url}: fetch failed after {retries} attempts: {last}")
def load_json_bytes(body:bytes,name:str)->dict[str,Any]:
    try:value=json.loads(body.decode("utf-8-sig"))
    except Exception as exc:raise GateError(f"{name}: invalid UTF-8 JSON: {exc}") from exc
    require(isinstance(value,dict),f"{name}: JSON object required");require(value.get("slot_id")==SLOT_ID,f"{name}: wrong slot_id");return value
def validate_documents(index_html:str,documents:dict[str,dict[str,Any]])->dict[str,Any]:
    for marker in REQUIRED_DOM_IDS:require(marker in index_html,f"index.html missing DOM marker {marker}")
    require("Görünüm yüklenemedi" in index_html,"index.html lacks explicit load-error rendering");require("undefined" not in index_html,"index.html contains literal undefined")
    p=documents["progress_latest.json"];o=documents["operations_latest.json"];rb=documents["runtime_bundle_latest.json"];rr=documents["runtime_results_latest.json"];rep=documents["runtime_reproducibility_latest.json"];lock=documents["execution_lock_latest.json"];elig=documents["runner_eligibility_latest.json"];poly=documents["polygon_popup_acceptance_latest.json"];runner=documents["runner_task_latest.json"];sources=documents["source_candidates_latest.json"];examples=documents["examples_latest.json"];publish=documents["remote_publish_latest.json"]
    require(p.get("display_state")=="progress_not_final","progress display_state");require(p.get("final_ready") is False,"progress final_ready");require(int(p.get("completed_operations",-1))==7,"completed operations");require(int(p.get("total_operations",-1))==12,"total operations");require(int(p.get("verified_product_rows",-1))==0,"product rows must remain zero before real runtime");require(int(p.get("actual_business_data_rows_written",-1))==0,"business rows must be zero")
    rows=o.get("operations");require(isinstance(rows,list) and len(rows)==12,"exactly 12 operation rows required");require([int(r.get("operation_no",-1)) for r in rows]==list(range(1,13)),"operation numbering must be contiguous")
    gates=rb.get("gates");require(isinstance(gates,list) and len(gates)>=8,"runtime preparation gates missing");require(rb.get("remote_runner_execution") is False,"runtime bundle must not claim remote execution")
    require(rr.get("status") in ("WAITING_REAL_RUNTIME_BUNDLE","REAL_RUNTIME_BUNDLE_VALIDATED_REVIEW_ONLY"),"runtime results status");real_rows=int(rr.get("real_runtime_rows_validated",-1));require(real_rows in (0,30761),"runtime result row count must be 0 or 30,761")
    if real_rows==0:require(rr.get("final_ready") is False,"waiting runtime result final_ready")
    else:require(isinstance(rr.get("samples"),list) and rr["samples"],"real runtime samples missing")
    require(rep.get("status") in ("WAITING_TWO_REAL_VALIDATED_RUNTIME_RECEIPTS","PASS_EXACT_RUNTIME_REPRODUCIBILITY","REVIEW_METADATA_ONLY_DRIFT","BLOCKED_SOURCE_INPUT_DRIFT","BLOCKED_NONDETERMINISTIC_RUNTIME_OUTPUT","BLOCKED_RECEIPT_INCONSISTENCY"),"reproducibility status")
    require(rep.get("automatic_acceptance") is False,"reproducibility cannot auto accept");require(int(rep.get("required_receipts",-1))==2,"two receipts required");available=int(rep.get("real_validated_receipts_available",0));require(available in (0,2),"receipt count must be 0 or 2")
    if rep.get("exact_reproducibility_pass") is True:require(available==2 and rep.get("status")=="PASS_EXACT_RUNTIME_REPRODUCIBILITY","exact reproducibility receipt mismatch")
    require(lock.get("status") in ("PREPARED_WAITING_EXISTING_RUNNER","PASS_EXECUTION_LOCK_REVIEW_ONLY"),"execution lock status")
    require(int(lock.get("locked_blob_count",-1))>=14,"execution lock must cover at least 14 blobs")
    require(lock.get("auto_claim") is False and lock.get("queue_submission") is False and lock.get("create_new_runner") is False,"execution lock mutation guard")
    if lock.get("exact_execution_lock_pass") is True:require(lock.get("status")=="PASS_EXECUTION_LOCK_REVIEW_ONLY","execution lock PASS mismatch")
    require(elig.get("auto_claim") is False and elig.get("queue_submission") is False and elig.get("create_new_runner") is False,"eligibility mutation guard")
    require(poly.get("polygon_popup_acceptance") in (False,True),"polygon acceptance boolean")
    require(runner.get("single_shared_runner_only") is True,"single-runner contract");require(runner.get("create_new_runner") is False,"new runner forbidden");require(runner.get("queue_submission") is False,"queue submission must remain false");require("execution_lock_latest.json" in str(runner.get("execution_lock_command",'')),"execution lock command missing")
    cc=int(sources.get("candidate_count",-1));pc=int(sources.get("promoted_count",-1));require(cc>=10 and pc>=9,"official source refresh not visible");require(len(sources.get("candidates") or [])==cc,"source candidate count mismatch")
    ec=int(examples.get("example_count",-1));require(ec>=21,"expanded examples not visible");require(len(examples.get("examples") or [])==ec,"example count mismatch");require(int(examples.get("verified_product_example_rows",-1))==0,"aggregate examples must not be product rows")
    require(publish.get("authoritative_remote_publish") is True,"authoritative publish evidence missing");require(publish.get("http_8012_acceptance") is False,"pre-acceptance record must remain false until this receipt is published")
    return {"operation_rows":len(rows),"runtime_preparation_gates":len(gates),"runtime_rows_visible":real_rows,"reproducibility_status":rep.get("status"),"execution_lock_status":lock.get("status"),"locked_blobs":int(lock.get("locked_blob_count",0)),"source_candidates_visible":cc,"promoted_sources_visible":pc,"examples_visible":ec}
def run_acceptance(base_url:str,*,timeout:float,retries:int)->dict[str,Any]:
    base=base_url if base_url.endswith("/") else base_url+"/";index_url=urllib.parse.urljoin(base,"index.html");index_body,index_type=fetch_bytes(index_url,timeout=timeout,retries=retries);index_text=index_body.decode("utf-8-sig")
    documents={};receipts=[{"path":"index.html","url":index_url,"bytes":len(index_body),"sha256":sha256_bytes(index_body),"content_type":index_type,"state":"PASS"}]
    for name in JSON_ENDPOINTS:
        url=urllib.parse.urljoin(base,name);body,ctype=fetch_bytes(url,timeout=timeout,retries=retries);documents[name]=load_json_bytes(body,name);receipts.append({"path":name,"url":url,"bytes":len(body),"sha256":sha256_bytes(body),"content_type":ctype,"state":"PASS"})
    visible=validate_documents(index_text,documents)
    return {"schema_version":3,"slot_id":SLOT_ID,"state":"PASS_HTTP_8012_AND_STATIC_DOM_CONTRACT","accepted_at":datetime.now(timezone.utc).isoformat(),"base_url":base,"endpoints":receipts,"visible_counts":visible,"http_8012_acceptance":True,"static_dom_contract_acceptance":True,"browser_console_acceptance":False,"polygon_popup_acceptance":False,"actual_business_data_rows_written":0,"scores_written":0,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False,"final_ready":False}
def main():
    p=argparse.ArgumentParser();p.add_argument("--base-url",default=DEFAULT_BASE_URL);p.add_argument("--output",required=True,type=Path);p.add_argument("--timeout-seconds",type=float,default=10.0);p.add_argument("--retries",type=int,default=2);a=p.parse_args();require(a.timeout_seconds>0,"timeout must be positive");require(1<=a.retries<=5,"retries must be between 1 and 5")
    r=run_acceptance(a.base_url,timeout=a.timeout_seconds,retries=a.retries);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");print(json.dumps({"state":r["state"],"visible_counts":r["visible_counts"]},sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
