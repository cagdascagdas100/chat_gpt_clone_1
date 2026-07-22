#!/usr/bin/env python3
"""Offline fixtures for revision-8 runtime evidence bundle validator."""
from __future__ import annotations
import importlib.util, json, tempfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
TARGET=HERE/"036_validate_revision8_runtime_evidence_bundle_v1.py"
spec=importlib.util.spec_from_file_location("validator",TARGET)
mod=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(mod)

def safe(slot=mod.SLOT_ID):
    return {"slot_id":slot,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False,"final_ready":False}

def queue():
    return {"slot_id":mod.SLOT_ID,"task_id":mod.TASK_ID,"attempt_id":mod.ATTEMPT_ID,"contract_revision":8,"expected_outputs":sorted(mod.QUEUE_EXPECTED_OUTPUTS),"single_runner_only":True,"new_runner":False,"parallel_runner":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False,"final_ready":False}

def payloads():
    p={}
    for rel in mod.PRE_ACCEPTANCE_OUTPUTS: p[rel]=dict(safe(),kind=rel)
    runner="docs/chatgpt_status/aays1/shards/future_growth_1/runner_outputs/006_official_geometry_pipeline_v8_latest.json"
    p[runner].update(workstream_id=mod.WORKSTREAM_ID,task_id=mod.TASK_ID,attempt_id=mod.ATTEMPT_ID,contract_revision=8,state="COMPLETED_SLOT_LOCAL_GEOMETRY_AND_PLANNING_QUERY_SAMPLE",actual_business_data_rows_written=0)
    dep="england_map_web/data/aays_21_slots/future_growth_1/revision8_predecessor_dependency_validation_latest.json"
    p[dep].update(result="PASS",dependency_complete=True,checks_passed=19,checks_total=19)
    ov="docs/chatgpt_status/aays1/shards/future_growth_1/validation/036_revision8_runner_output_runtime_validation_latest.json"
    p[ov].update(result="PASS",checks_passed=58,checks_total=58,business_progress_claimed=False)
    return p

def write_fixture(root:Path,q:dict,ps:dict):
    for rel,obj in ps.items():
        path=root/rel; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(obj,sort_keys=True),encoding="utf-8")
    qp=root/"queue.json"; qp.write_text(json.dumps(q),encoding="utf-8"); return qp

def run_case(name,mutate,expected):
    with tempfile.TemporaryDirectory() as td:
        root=Path(td); q=queue(); ps=payloads(); mutate(q,ps,root); qp=write_fixture(root,q,ps)
        actual=mod.validate(root,json.loads(qp.read_text()))["result"]
        return {"name":name,"expected":expected,"actual":actual,"pass":actual==expected}

def main():
    runner="docs/chatgpt_status/aays1/shards/future_growth_1/runner_outputs/006_official_geometry_pipeline_v8_latest.json"
    dep="england_map_web/data/aays_21_slots/future_growth_1/revision8_predecessor_dependency_validation_latest.json"
    ov="docs/chatgpt_status/aays1/shards/future_growth_1/validation/036_revision8_runner_output_runtime_validation_latest.json"
    cases=[
      run_case("exact_bundle",lambda q,p,r:None,"PASS"),
      run_case("missing_file",lambda q,p,r:p.pop(next(iter(p))),"FAIL"),
      run_case("wrong_slot",lambda q,p,r:p[runner].__setitem__("slot_id","future_growth_2"),"FAIL"),
      run_case("wrong_task",lambda q,p,r:p[runner].__setitem__("task_id","wrong"),"FAIL"),
      run_case("wrong_attempt",lambda q,p,r:p[runner].__setitem__("attempt_id","wrong"),"FAIL"),
      run_case("wrong_revision",lambda q,p,r:p[runner].__setitem__("contract_revision",7),"FAIL"),
      run_case("runner_not_completed",lambda q,p,r:p[runner].__setitem__("state","PENDING"),"FAIL"),
      run_case("dependency_false",lambda q,p,r:p[dep].__setitem__("dependency_complete",False),"FAIL"),
      run_case("dependency_18_checks",lambda q,p,r:p[dep].__setitem__("checks_passed",18),"FAIL"),
      run_case("output_validator_57",lambda q,p,r:p[ov].__setitem__("checks_passed",57),"FAIL"),
      run_case("legacy_nine_outputs",lambda q,p,r:q.__setitem__("expected_outputs",q["expected_outputs"][:-1]),"FAIL"),
      run_case("unsafe_truth_flag",lambda q,p,r:p[runner].__setitem__("fake_data",True),"FAIL"),
      run_case("business_row_claim",lambda q,p,r:p[runner].__setitem__("actual_business_data_rows_written",1),"FAIL"),
    ]
    passed=sum(c["pass"] for c in cases)
    out={"schema_version":1,"slot_id":mod.SLOT_ID,"selftest_kind":"REVISION8_RUNTIME_EVIDENCE_BUNDLE","result":f"{passed}/{len(cases)} PASS","passed":passed,"total":len(cases),"cases":cases,"runner_execution_claimed":False,"business_progress_claimed":False,"final_ready":False}
    print(json.dumps(out,ensure_ascii=False,indent=2)); return 0 if passed==len(cases) else 2
if __name__=="__main__": raise SystemExit(main())
