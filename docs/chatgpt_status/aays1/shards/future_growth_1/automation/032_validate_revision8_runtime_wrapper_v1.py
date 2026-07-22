#!/usr/bin/env python3
"""Static fail-closed validator for the revision-8 runtime wrapper."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

SLOT_ID="future_growth_1"

def validate_text(text:str)->dict:
    checks={
      "core_path_exact":'future_growth_1_official_geometry_entry_v8.py' in text,
      "queue_validator_v2_exact":'030_validate_revision8_queue_request_contract_v2.py' in text,
      "queue_selftest_v2_exact":'031_selftest_revision8_queue_request_contract_v2.py' in text,
      "required_files_checked":'required=[CORE,QUEUE_VALIDATOR,QUEUE_SELFTEST]' in text,
      "validator_override_before_main":text.find('module.QUEUE_REQUEST_VALIDATOR=QUEUE_VALIDATOR')>=0 and text.find('module.QUEUE_REQUEST_VALIDATOR=QUEUE_VALIDATOR')<text.find('module.main()'),
      "selftest_override_before_main":text.find('module.QUEUE_REQUEST_SELFTEST=QUEUE_SELFTEST')>=0 and text.find('module.QUEUE_REQUEST_SELFTEST=QUEUE_SELFTEST')<text.find('module.main()'),
      "no_cross_slot_token":all(token not in text for token in ('height_difference_2','future_growth_2','future_growth_3')),
      "single_core_main_call":text.count('module.main()')==1,
      "no_network_or_business_claim":all(token not in text for token in ('urlopen(','requests.get(','actual_business_data_rows_written=1','final_ready=True')),
    }
    failed=[k for k,v in checks.items() if not v]
    return {"schema_version":1,"slot_id":SLOT_ID,"validation_kind":"REVISION8_RUNTIME_WRAPPER_STATIC_FAIL_CLOSED","result":"PASS" if not failed else "FAIL","checks_passed":sum(checks.values()),"checks_total":len(checks),"checks":checks,"failed_checks":failed,"runner_execution_claimed":False,"business_progress_claimed":False,"final_ready":False}

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument('wrapper',type=Path); p.add_argument('--output',type=Path); args=p.parse_args()
    try: result=validate_text(args.wrapper.read_text(encoding='utf-8'))
    except Exception as exc: result={"schema_version":1,"slot_id":SLOT_ID,"validation_kind":"REVISION8_RUNTIME_WRAPPER_STATIC_FAIL_CLOSED","result":"FAIL","checks_passed":0,"checks_total":1,"checks":{"read":False},"failed_checks":[f"{type(exc).__name__}:{exc}"],"runner_execution_claimed":False,"business_progress_claimed":False,"final_ready":False}
    text=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    if args.output: args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(text,encoding='utf-8')
    else: sys.stdout.write(text)
    return 0 if result['result']=='PASS' else 2
if __name__=='__main__': raise SystemExit(main())
