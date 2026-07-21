#!/usr/bin/env python3
"""HTTP 8012 and static DOM-contract acceptance for internet_access_3 review page."""
from __future__ import annotations
import argparse,hashlib,json,time,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path
from typing import Any
SLOT_ID="internet_access_3";DEFAULT_BASE_URL="http://127.0.0.1:8012/data/aays_18_slots/internet_access_3/"
REQUIRED_DOM_IDS=('id="metrics"','id="operations"','id="runtime"','id="runtimeResults"','id="runtimeSamples"','id="reproducibility"','id="executionLock"','id="runnerBlocker"','id="directZip"','id="targeted"','id="polygon"','id="eligibility"','id="blobs"','id="publish"','id="runner"','id="sources"','id="examples"')
JSON_ENDPOINTS=("progress_latest.json","operations_latest.json","runtime_bundle_latest.json","runtime_results_latest.json","runtime_reproducibility_latest.json","execution_lock_latest.json","runner_blocker_diagnostics_latest.json","runner_eligibility_latest.json","polygon_popup_acceptance_latest.json","runner_task_latest.json","source_candidates_latest.json","examples_latest.json","remote_publish_latest.json")
class GateError(RuntimeError):pass
def require(c,m):
    if not c:raise GateError(m)
def sha256_bytes(v:bytes)->str:return hashlib.sha256(v).hexdigest()
def fetch_bytes(url:str,*,timeout:float,retries:int,max_bytes:int=8_000_000)->tuple[bytes,str]:
    last=None
    for attempt in range(1,retries+1):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"internet_access_3-http-acceptance/4"})
            with urllib.request.urlopen(req,timeout=timeout) as response:
                status=int(getattr(response,"status",response.getcode()));require(status==200,f"{url}: HTTP {status}");ctype=response.headers.get("Content-Type","");body=response.read(max_bytes+1);require(len(body)<=max_bytes,f"{url}: response too large");require(body,f"{url}: empty response");return body,ctype
        except Exception as exc:
            last=exc
            if attempt<retries:time.sleep(min(.25*attempt,1.0))
    raise GateError(f"{url}: fetch failed after {retries} attempts: {last}")
def load_json_bytes(body:bytes,name:str)->dict[str,Any]:
    try:v=json.loads(body.decode("utf-8-sig"))
    except Exception as exc:raise GateError(f"{name}: invalid UTF-8 JSON: {exc}") from exc
    require(isinstance(v,dict),f"{name}: object required");require(v.get("slot_id")==SLOT_ID,f"{name}: wrong slot_id");return v
def validate_documents(index_html:str,d:dict[str,dict[str,Any]])->dict[str,Any]:
    for marker in REQUIRED_DOM_IDS:require(marker in index_html,f"index missing {marker}")
    require("Görünüm yüklenemedi" in index_html,"load error rendering missing");require("undefined" not in index_html,"literal undefined")
    p=d['progress_latest.json'];o=d['operations_latest.json'];rb=d['runtime_bundle_latest.json'];rr=d['runtime_results_latest.json'];rep=d['runtime_reproducibility_latest.json'];lock=d['execution_lock_latest.json'];block=d['runner_blocker_diagnostics_latest.json'];elig=d['runner_eligibility_latest.json'];poly=d['polygon_popup_acceptance_latest.json'];runner=d['runner_task_latest.json'];sources=d['source_candidates_latest.json'];examples=d['examples_latest.json'];publish=d['remote_publish_latest.json']
    require(p.get('display_state')=='progress_not_final' and p.get('final_ready') is False,'progress');require(int(p.get('completed_operations',-1))==7 and int(p.get('total_operations',-1))==12,'operations summary');require(int(p.get('verified_product_rows',-1))==0 and int(p.get('actual_business_data_rows_written',-1))==0,'row truth')
    rows=o.get('operations');require(isinstance(rows,list) and len(rows)==12 and [int(x.get('operation_no',-1)) for x in rows]==list(range(1,13)),'operation rows')
    require(isinstance(rb.get('gates'),list) and len(rb['gates'])>=8 and rb.get('remote_runner_execution') is False,'runtime bundle');require(int(rr.get('real_runtime_rows_validated',-1)) in (0,30761),'runtime rows')
    require(rep.get('automatic_acceptance') is False and int(rep.get('required_receipts',-1))==2,'reproducibility');require(lock.get('status') in ('PREPARED_WAITING_EXISTING_RUNNER','PASS_EXECUTION_LOCK_REVIEW_ONLY') and int(lock.get('locked_blob_count',-1))>=14,'lock');require(lock.get('auto_claim') is False and lock.get('queue_submission') is False and lock.get('create_new_runner') is False,'lock mutation')
    require(block.get('status') in ('BLOCKED_STALE_RUNNER_EVIDENCE_OPERATOR_RECOVERY_NOT_EXECUTED','REVIEW_RUNNER_EVIDENCE'),'blocker status');require(block.get('repository_evidence_only') is True and block.get('live_os_process_probe_performed') is False,'blocker boundary');require(len(block.get('gates') or [])==9,'blocker gates');require(block.get('auto_claim') is False and block.get('queue_submission') is False and block.get('create_new_runner') is False,'blocker mutation');require(float((block.get('ages_hours') or {}).get('daemon_heartbeat',-1))>=0,'blocker age')
    require(elig.get('auto_claim') is False and elig.get('queue_submission') is False and elig.get('create_new_runner') is False,'eligibility');require(poly.get('polygon_popup_acceptance') in (False,True),'polygon');require(runner.get('single_shared_runner_only') is True and runner.get('create_new_runner') is False and runner.get('queue_submission') is False,'runner');require('runner_blocker_diagnostics_latest.json' in str(runner.get('blocker_diagnostics_command','')),'blocker command')
    cc=int(sources.get('candidate_count',-1));pc=int(sources.get('promoted_count',-1));require(cc>=10 and pc>=9 and len(sources.get('candidates') or [])==cc,'sources');ec=int(examples.get('example_count',-1));require(ec>=25 and len(examples.get('examples') or [])==ec and int(examples.get('verified_product_example_rows',-1))==0,'examples');require(publish.get('authoritative_remote_publish') is True and publish.get('http_8012_acceptance') is False,'publish')
    return {'operation_rows':12,'runtime_rows_visible':int(rr.get('real_runtime_rows_validated',0)),'locked_blobs':int(lock.get('locked_blob_count',0)),'blocker_status':block.get('status'),'blocker_gate_rows':9,'source_candidates_visible':cc,'promoted_sources_visible':pc,'examples_visible':ec}
def run_acceptance(base_url:str,*,timeout:float,retries:int)->dict[str,Any]:
    base=base_url if base_url.endswith('/') else base_url+'/';u=urllib.parse.urljoin(base,'index.html');body,ctype=fetch_bytes(u,timeout=timeout,retries=retries);text=body.decode('utf-8-sig');docs={};receipts=[{'path':'index.html','url':u,'bytes':len(body),'sha256':sha256_bytes(body),'content_type':ctype,'state':'PASS'}]
    for name in JSON_ENDPOINTS:
        u=urllib.parse.urljoin(base,name);body,ctype=fetch_bytes(u,timeout=timeout,retries=retries);docs[name]=load_json_bytes(body,name);receipts.append({'path':name,'url':u,'bytes':len(body),'sha256':sha256_bytes(body),'content_type':ctype,'state':'PASS'})
    visible=validate_documents(text,docs);return {'schema_version':4,'slot_id':SLOT_ID,'state':'PASS_HTTP_8012_AND_STATIC_DOM_CONTRACT','accepted_at':datetime.now(timezone.utc).isoformat(),'base_url':base,'endpoints':receipts,'visible_counts':visible,'http_8012_acceptance':True,'static_dom_contract_acceptance':True,'browser_console_acceptance':False,'polygon_popup_acceptance':False,'actual_business_data_rows_written':0,'scores_written':0,'fake_data':False,'db_write':False,'migration':False,'production_deploy':False,'final_ready':False}
def main():
    p=argparse.ArgumentParser();p.add_argument('--base-url',default=DEFAULT_BASE_URL);p.add_argument('--output',required=True,type=Path);p.add_argument('--timeout-seconds',type=float,default=10);p.add_argument('--retries',type=int,default=2);a=p.parse_args();require(a.timeout_seconds>0,'timeout');require(1<=a.retries<=5,'retries');r=run_acceptance(a.base_url,timeout=a.timeout_seconds,retries=a.retries);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'state':r['state'],'visible_counts':r['visible_counts']},sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
