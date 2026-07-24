#!/usr/bin/env python3
"""Offline fixtures for revision-8 predecessor dependency validator."""
from __future__ import annotations
import importlib.util, json
from pathlib import Path
HERE=Path(__file__).resolve().parent
TARGET=HERE/"034_validate_revision8_predecessor_dependency_v1.py"
spec=importlib.util.spec_from_file_location("validator",TARGET)
mod=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(mod)

def fixture():
    q={"slot_id":mod.SLOT_ID,"task_id":mod.TASK_ID,"attempt_id":mod.ATTEMPT_ID,"contract_revision":8,"state":"pending","claimable":True,"ready_for_claim":True,"single_runner_only":True,"new_runner":False,"parallel_runner":False,"sequential_after_task_id":mod.PREDECESSOR_TASK_ID,"final_ready":False,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
    p={"slot_id":mod.PREDECESSOR_SLOT_ID,"current_task_id":mod.PREDECESSOR_TASK_ID,"state":"completed_binary_exact_stream","runner_execution_state":"completed_binary_exact_stream","queue_status":"completed","candidate_seed_rows_written":3,"hmlr_exact_polygon_rows_written":3,"ea_dtm1m_polygon_sample_rows_written":3,"os_terrain50_crosscheck_rows_written":3,"port_8012_acceptance_rows_written":1,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False}
    return q,p

def case(name,mutate,expected):
    q,p=fixture(); mutate(q,p); actual=mod.validate(q,p)["result"]
    return {"name":name,"expected":expected,"actual":actual,"pass":actual==expected}

def main():
    cases=[
      case("exact_completed_dependency",lambda q,p:None,"PASS"),
      case("pending_predecessor_state",lambda q,p:p.__setitem__("state","pending_guarded_operator_recovery"),"FAIL"),
      case("wrong_predecessor_slot",lambda q,p:p.__setitem__("slot_id","future_growth_2"),"FAIL"),
      case("wrong_predecessor_task",lambda q,p:p.__setitem__("current_task_id","wrong"),"FAIL"),
      case("runner_not_completed",lambda q,p:p.__setitem__("runner_execution_state","running"),"FAIL"),
      case("queue_not_completed",lambda q,p:p.__setitem__("queue_status","pickup_requested"),"FAIL"),
      case("missing_hmlr_polygon",lambda q,p:p.__setitem__("hmlr_exact_polygon_rows_written",2),"FAIL"),
      case("missing_http_acceptance",lambda q,p:p.__setitem__("port_8012_acceptance_rows_written",0),"FAIL"),
      case("wrong_sequential_dependency",lambda q,p:q.__setitem__("sequential_after_task_id","wrong"),"FAIL"),
      case("unsafe_truth_flag",lambda q,p:p.__setitem__("fake_data",True),"FAIL"),
    ]
    passed=sum(c["pass"] for c in cases)
    out={"schema_version":1,"slot_id":mod.SLOT_ID,"selftest_kind":"REVISION8_PREDECESSOR_DEPENDENCY","result":f"{passed}/{len(cases)} PASS","passed":passed,"total":len(cases),"cases":cases,"runner_execution_claimed":False,"business_progress_claimed":False,"final_ready":False}
    print(json.dumps(out,ensure_ascii=False,indent=2)); return 0 if passed==len(cases) else 2
if __name__=="__main__": raise SystemExit(main())
