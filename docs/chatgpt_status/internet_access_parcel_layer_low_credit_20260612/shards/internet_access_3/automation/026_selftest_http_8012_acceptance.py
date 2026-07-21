#!/usr/bin/env python3
from __future__ import annotations
import copy,importlib.util,json,tempfile,threading
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from typing import Any,Callable
ROOT=Path(__file__).parent
def load()->Any:
    spec=importlib.util.spec_from_file_location("http025",ROOT/"025_http_8012_acceptance.py");assert spec and spec.loader
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def fixture():
    ids=("metrics","operations","runtime","runtimeResults","runtimeSamples","reproducibility","directZip","targeted","polygon","eligibility","blobs","publish","runner","sources","examples")
    html="<html>"+"".join(f'<div id="{v}"></div>' for v in ids)+"<script>function fail(){return 'Görünüm yüklenemedi'}</script></html>"
    docs={
    "progress_latest.json":{"slot_id":"internet_access_3","display_state":"progress_not_final","final_ready":False,"completed_operations":7,"total_operations":12,"verified_product_rows":0,"actual_business_data_rows_written":0},
    "operations_latest.json":{"slot_id":"internet_access_3","operations":[{"operation_no":n} for n in range(1,13)]},
    "runtime_bundle_latest.json":{"slot_id":"internet_access_3","gates":[{"gate_no":n,"state":"PREPARED"} for n in range(1,9)],"remote_runner_execution":False},
    "runtime_results_latest.json":{"slot_id":"internet_access_3","status":"WAITING_REAL_RUNTIME_BUNDLE","real_runtime_rows_validated":0,"final_ready":False},
    "runtime_reproducibility_latest.json":{"slot_id":"internet_access_3","status":"WAITING_TWO_REAL_VALIDATED_RUNTIME_RECEIPTS","automatic_acceptance":False,"required_receipts":2,"real_validated_receipts_available":0,"exact_reproducibility_pass":False},
    "runner_eligibility_latest.json":{"slot_id":"internet_access_3","auto_claim":False,"queue_submission":False,"create_new_runner":False},
    "polygon_popup_acceptance_latest.json":{"slot_id":"internet_access_3","polygon_popup_acceptance":False},
    "runner_task_latest.json":{"slot_id":"internet_access_3","single_shared_runner_only":True,"create_new_runner":False,"queue_submission":False},
    "source_candidates_latest.json":{"slot_id":"internet_access_3","candidate_count":10,"promoted_count":9,"candidates":[{} for _ in range(10)]},
    "examples_latest.json":{"slot_id":"internet_access_3","example_count":21,"examples":[{} for _ in range(21)],"verified_product_example_rows":0},
    "remote_publish_latest.json":{"slot_id":"internet_access_3","authoritative_remote_publish":True,"http_8012_acceptance":False}}
    return html,docs
def expect_fail(fn:Callable[[],None]):
    try:fn()
    except Exception:return
    raise AssertionError("expected failure")
class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self,format:str,*args:object)->None:return
def main():
    m=load();html,base=fixture();results=[]
    visible=m.validate_documents(html,copy.deepcopy(base));assert visible["operation_rows"]==12 and visible["source_candidates_visible"]==10 and visible["reproducibility_status"]=="WAITING_TWO_REAL_VALIDATED_RUNTIME_RECEIPTS";results.append("valid_documents")
    for name,old,new in (("missing_dom_id",'id="runtimeResults"','id="missingRuntimeResults"'),("missing_repro_dom",'id="reproducibility"','id="missingReproducibility"'),("literal_undefined","</html>","undefined</html>")):
        expect_fail(lambda old=old,new=new:m.validate_documents(html.replace(old,new),copy.deepcopy(base)));results.append(name)
    cases=[
    ("progress_final",lambda d:d["progress_latest.json"].update(final_ready=True)),
    ("wrong_completed",lambda d:d["progress_latest.json"].update(completed_operations=8)),
    ("product_rows",lambda d:d["progress_latest.json"].update(verified_product_rows=1)),
    ("operation_count",lambda d:d["operations_latest.json"]["operations"].pop()),
    ("operation_sequence",lambda d:d["operations_latest.json"]["operations"][2].update(operation_no=9)),
    ("runtime_gate_count",lambda d:d["runtime_bundle_latest.json"]["gates"].pop()),
    ("runtime_claim",lambda d:d["runtime_bundle_latest.json"].update(remote_runner_execution=True)),
    ("runtime_rows_invalid",lambda d:d["runtime_results_latest.json"].update(real_runtime_rows_validated=5)),
    ("repro_auto_accept",lambda d:d["runtime_reproducibility_latest.json"].update(automatic_acceptance=True)),
    ("repro_required_receipts",lambda d:d["runtime_reproducibility_latest.json"].update(required_receipts=1)),
    ("repro_available_receipts",lambda d:d["runtime_reproducibility_latest.json"].update(real_validated_receipts_available=1)),
    ("repro_exact_without_two",lambda d:d["runtime_reproducibility_latest.json"].update(exact_reproducibility_pass=True,status="PASS_EXACT_RUNTIME_REPRODUCIBILITY")),
    ("eligibility_auto_claim",lambda d:d["runner_eligibility_latest.json"].update(auto_claim=True)),
    ("eligibility_queue",lambda d:d["runner_eligibility_latest.json"].update(queue_submission=True)),
    ("new_runner",lambda d:d["runner_task_latest.json"].update(create_new_runner=True)),
    ("queue_submission",lambda d:d["runner_task_latest.json"].update(queue_submission=True)),
    ("source_count",lambda d:d["source_candidates_latest.json"].update(candidate_count=9)),
    ("example_count",lambda d:d["examples_latest.json"].update(example_count=18)),
    ("product_example",lambda d:d["examples_latest.json"].update(verified_product_example_rows=1)),
    ("publish_missing",lambda d:d["remote_publish_latest.json"].update(authoritative_remote_publish=False))]
    for name,change in cases:
        broken=copy.deepcopy(base);change(broken);expect_fail(lambda broken=broken:m.validate_documents(html,broken));results.append(name)
    with tempfile.TemporaryDirectory() as temp:
        web=Path(temp);(web/"index.html").write_text(html,encoding="utf-8")
        for name,value in base.items():(web/name).write_text(json.dumps(value),encoding="utf-8")
        handler=lambda *args,**kwargs:QuietHandler(*args,directory=str(web),**kwargs);server=ThreadingHTTPServer(("127.0.0.1",0),handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            receipt=m.run_acceptance(f"http://127.0.0.1:{server.server_address[1]}/",timeout=3.0,retries=1);assert receipt["state"]=="PASS_HTTP_8012_AND_STATIC_DOM_CONTRACT" and len(receipt["endpoints"])==12;results.append("local_http_roundtrip")
        finally:
            server.shutdown();server.server_close();thread.join(timeout=2)
    print(json.dumps({"passed":len(results),"total":len(results),"results":[{"test":x,"state":"PASS"} for x in results]},sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
