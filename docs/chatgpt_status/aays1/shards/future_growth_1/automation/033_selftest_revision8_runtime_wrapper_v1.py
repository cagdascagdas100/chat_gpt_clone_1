#!/usr/bin/env python3
"""Offline fixtures for revision-8 guarded runtime wrapper validator."""
from __future__ import annotations
import importlib.util, json
from pathlib import Path
HERE=Path(__file__).resolve().parent
TARGET=HERE/"032_validate_revision8_runtime_wrapper_v1.py"
WRAPPER=HERE.parents[2]/"automation/future_growth_1_official_geometry_entry_v8_runtime.py"
spec=importlib.util.spec_from_file_location("validator",TARGET)
mod=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(mod)

def case(name,text,expected):
    actual=mod.validate_text(text)["result"]
    return {"name":name,"expected":expected,"actual":actual,"pass":actual==expected}

def main():
    exact=WRAPPER.read_text(encoding="utf-8")
    cases=[
      case("exact_guarded_wrapper",exact,"PASS"),
      case("old_queue_validator",exact.replace("030_validate_revision8_queue_request_contract_v2.py","026_validate_revision8_queue_request_contract_v1.py"),"FAIL"),
      case("missing_dependency_validator",exact.replace("034_validate_revision8_predecessor_dependency_v1.py","removed.py"),"FAIL"),
      case("missing_dependency_selftest",exact.replace("035_selftest_revision8_predecessor_dependency_v1.py","removed.py"),"FAIL"),
      case("wrong_predecessor_path",exact.replace("height_difference_2/status_latest.json","future_growth_2/status_latest.json"),"FAIL"),
      case("dependency_after_import",exact.replace("\n    dependency_run=run","\n    dependency_process=run"),"FAIL"),
      case("wrong_dependency_check_count",exact.replace('dependency.get("checks_passed")!=19','dependency.get("checks_passed")!=18'),"FAIL"),
      case("missing_queue_override",exact.replace("module.QUEUE_REQUEST_VALIDATOR=QUEUE_VALIDATOR","pass # removed"),"FAIL"),
      case("output_validator_before_core",exact.replace("\n    output_validation_run=run","\n    output_process=run"),"FAIL"),
      case("business_claim",exact+'\n# business_progress_claimed":True\n',"FAIL"),
    ]
    passed=sum(c["pass"] for c in cases)
    out={"schema_version":2,"slot_id":"future_growth_1","selftest_kind":"REVISION8_GUARDED_RUNTIME_WRAPPER","result":f"{passed}/{len(cases)} PASS","passed":passed,"total":len(cases),"cases":cases,"runner_execution_claimed":False,"business_progress_claimed":False,"final_ready":False}
    print(json.dumps(out,ensure_ascii=False,indent=2)); return 0 if passed==len(cases) else 2
if __name__=="__main__": raise SystemExit(main())
