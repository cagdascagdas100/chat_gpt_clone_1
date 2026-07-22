#!/usr/bin/env python3
"""Offline fixtures for the revision-8 runtime-wrapper validator."""
from __future__ import annotations
import importlib.util, json
from pathlib import Path

HERE=Path(__file__).resolve().parent
TARGET=HERE/'032_validate_revision8_runtime_wrapper_v1.py'
WRAPPER=HERE.parents[2]/'automation/future_growth_1_official_geometry_entry_v8_runtime.py'
spec=importlib.util.spec_from_file_location('validator',TARGET)
mod=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(mod)

def case(name,text,expected):
    actual=mod.validate_text(text)['result']; return {'name':name,'expected':expected,'actual':actual,'pass':actual==expected}

def main():
    exact=WRAPPER.read_text(encoding='utf-8')
    cases=[
      case('exact_wrapper',exact,'PASS'),
      case('old_queue_validator',exact.replace('030_validate_revision8_queue_request_contract_v2.py','026_validate_revision8_queue_request_contract_v1.py'),'FAIL'),
      case('old_queue_selftest',exact.replace('031_selftest_revision8_queue_request_contract_v2.py','027_selftest_revision8_queue_request_contract_v1.py'),'FAIL'),
      case('missing_validator_override',exact.replace('module.QUEUE_REQUEST_VALIDATOR=QUEUE_VALIDATOR','pass # removed validator override'),'FAIL'),
      case('late_selftest_override',exact.replace('module.QUEUE_REQUEST_SELFTEST=QUEUE_SELFTEST\n    return int(module.main())','result=int(module.main())\n    module.QUEUE_REQUEST_SELFTEST=QUEUE_SELFTEST\n    return result'),'FAIL'),
      case('cross_slot_token',exact+'\n# future_growth_2\n','FAIL'),
    ]
    out={'schema_version':1,'slot_id':'future_growth_1','selftest_kind':'REVISION8_RUNTIME_WRAPPER','result':f"{sum(c['pass'] for c in cases)}/{len(cases)} PASS",'passed':sum(c['pass'] for c in cases),'total':len(cases),'cases':cases,'runner_execution_claimed':False,'business_progress_claimed':False,'final_ready':False}
    print(json.dumps(out,ensure_ascii=False,indent=2)); return 0 if all(c['pass'] for c in cases) else 2
if __name__=='__main__': raise SystemExit(main())
