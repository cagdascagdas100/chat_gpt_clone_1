#!/usr/bin/env python3
"""Deterministic network-free tests for 025_http_8012_acceptance.py."""
from __future__ import annotations
import copy, importlib.util, json, tempfile, threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable
ROOT=Path(__file__).parent

def load()->Any:
    spec=importlib.util.spec_from_file_location("http025",ROOT/"025_http_8012_acceptance.py")
    if spec is None or spec.loader is None: raise RuntimeError("cannot load http025")
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

def fixture()->tuple[str,dict[str,dict[str,Any]]]:
    ids=("metrics","operations","runtime","runtimeResults","runtimeSamples","directZip","targeted","blobs","publish","runner","sources","examples")
    html="<html>"+"".join(f'<div id="{value}"></div>' for value in ids)+"<script>function fail(){return 'Görünüm yüklenemedi'}</script></html>"
    documents={
      "progress_latest.json":{"slot_id":"internet_access_3","display_state":"progress_not_final","final_ready":False,"completed_operations":7,"total_operations":12,"verified_product_rows":0,"actual_business_data_rows_written":0},
      "operations_latest.json":{"slot_id":"internet_access_3","operations":[{"operation_no":n} for n in range(1,13)]},
      "runtime_bundle_latest.json":{"slot_id":"internet_access_3","gates":[{"gate_no":n,"state":"PREPARED"} for n in range(1,9)],"remote_runner_execution":False},
      "runtime_results_latest.json":{"slot_id":"internet_access_3","status":"WAITING_REAL_RUNTIME_BUNDLE","real_runtime_rows_validated":0,"final_ready":False},
      "runner_task_latest.json":{"slot_id":"internet_access_3","single_shared_runner_only":True,"create_new_runner":False,"queue_submission":False},
      "source_candidates_latest.json":{"slot_id":"internet_access_3","candidate_count":10,"promoted_count":9,"candidates":[{} for _ in range(10)]},
      "examples_latest.json":{"slot_id":"internet_access_3","example_count":13,"examples":[{} for _ in range(13)],"verified_product_example_rows":0},
      "remote_publish_latest.json":{"slot_id":"internet_access_3","authoritative_remote_publish":True,"http_8012_acceptance":False},
    }
    return html,documents

def expect_fail(fn:Callable[[],None])->None:
    try: fn()
    except Exception: return
    raise AssertionError("expected failure")

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self,format:str,*args:object)->None: return

def main()->int:
    module=load(); html,base=fixture(); results=[]
    visible=module.validate_documents(html,copy.deepcopy(base)); assert visible["operation_rows"]==12 and visible["source_candidates_visible"]==10; results.append("valid_documents")
    for name,old,new in (("missing_dom_id",'id="runtimeResults"','id="missingRuntimeResults"'),("literal_undefined","</html>","undefined</html>")):
        expect_fail(lambda old=old,new=new:module.validate_documents(html.replace(old,new),copy.deepcopy(base))); results.append(name)
    cases=[
      ("progress_final",lambda d:d["progress_latest.json"].update(final_ready=True)),("wrong_completed",lambda d:d["progress_latest.json"].update(completed_operations=8)),("product_rows",lambda d:d["progress_latest.json"].update(verified_product_rows=1)),
      ("operation_count",lambda d:d["operations_latest.json"]["operations"].pop()),("operation_sequence",lambda d:d["operations_latest.json"]["operations"][2].update(operation_no=9)),
      ("runtime_gate_count",lambda d:d["runtime_bundle_latest.json"]["gates"].pop()),("runtime_claim",lambda d:d["runtime_bundle_latest.json"].update(remote_runner_execution=True)),("runtime_rows_invalid",lambda d:d["runtime_results_latest.json"].update(real_runtime_rows_validated=5)),
      ("new_runner",lambda d:d["runner_task_latest.json"].update(create_new_runner=True)),("queue_submission",lambda d:d["runner_task_latest.json"].update(queue_submission=True)),
      ("source_count",lambda d:d["source_candidates_latest.json"].update(candidate_count=9)),("example_count",lambda d:d["examples_latest.json"].update(example_count=12)),("product_example",lambda d:d["examples_latest.json"].update(verified_product_example_rows=1)),("publish_missing",lambda d:d["remote_publish_latest.json"].update(authoritative_remote_publish=False)),
    ]
    for name,change in cases:
        broken=copy.deepcopy(base); change(broken); expect_fail(lambda broken=broken:module.validate_documents(html,broken)); results.append(name)
    with tempfile.TemporaryDirectory() as temp:
        web=Path(temp); (web/"index.html").write_text(html,encoding="utf-8")
        for name,value in base.items(): (web/name).write_text(json.dumps(value),encoding="utf-8")
        handler=lambda *args,**kwargs:QuietHandler(*args,directory=str(web),**kwargs); server=ThreadingHTTPServer(("127.0.0.1",0),handler); thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
        try:
            receipt=module.run_acceptance(f"http://127.0.0.1:{server.server_address[1]}/",timeout=3.0,retries=1); assert receipt["state"]=="PASS_HTTP_8012_AND_STATIC_DOM_CONTRACT" and len(receipt["endpoints"])==9; results.append("local_http_roundtrip")
        finally:
            server.shutdown(); server.server_close(); thread.join(timeout=2)
    print(json.dumps({"passed":len(results),"total":len(results),"results":[{"test":x,"state":"PASS"} for x in results]},sort_keys=True)); return 0

if __name__=="__main__": raise SystemExit(main())
