#!/usr/bin/env python3
"""Static fail-closed validator for revision-8 guarded runtime wrapper."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
SLOT_ID="future_growth_1"

def validate_text(text:str)->dict:
    dep_self=text.find("\n    dependency_selftest_run=run")
    bundle_self=text.find("\n    bundle_selftest_run=run")
    dep_run=text.find("\n    dependency_run=run")
    import_marker=text.find("spec=importlib.util.spec_from_file_location")
    core_marker=text.find("core_exit=int(module.main())")
    out_marker=text.find("\n    output_validation_run=run")
    bundle_marker=text.find("\n    bundle_validation_run=run")
    accept_marker=text.find('write_json(WEB_ACCEPTANCE,{"schema_version":2,"slot_id":"future_growth_1","state":"COMPLETED_RUNTIME_ACCEPTANCE"')
    allowed_predecessor='PREDECESSOR_STATUS=REPO/"docs/chatgpt_status/_shared/slots_21/height_difference_2/status_latest.json"'
    checks={
      "core_path_exact":'future_growth_1_official_geometry_entry_v8.py' in text,
      "queue_validator_v2_exact":'030_validate_revision8_queue_request_contract_v2.py' in text,
      "queue_selftest_v2_exact":'031_selftest_revision8_queue_request_contract_v2.py' in text,
      "dependency_validator_exact":'034_validate_revision8_predecessor_dependency_v1.py' in text,
      "dependency_selftest_exact":'035_selftest_revision8_predecessor_dependency_v1.py' in text,
      "bundle_validator_exact":'036_validate_revision8_runtime_evidence_bundle_v1.py' in text,
      "bundle_selftest_exact":'037_selftest_revision8_runtime_evidence_bundle_v1.py' in text,
      "bundle_output_exact":'038_revision8_runtime_evidence_bundle_latest.json' in text,
      "predecessor_status_path_exact":allowed_predecessor in text and text.count("height_difference_2")==1,
      "output_validator_exact":'022_validate_revision8_runner_output_v1.py' in text,
      "required_files_checked":'required=[CORE,QUEUE_VALIDATOR,QUEUE_SELFTEST,DEPENDENCY_VALIDATOR,DEPENDENCY_SELFTEST,BUNDLE_VALIDATOR,BUNDLE_SELFTEST,QUEUE_MANIFEST,PREDECESSOR_STATUS,OUTPUT_VALIDATOR]' in text,
      "dependency_selftest_before_import":0<=dep_self<import_marker,
      "bundle_selftest_before_import":0<=bundle_self<import_marker,
      "dependency_validation_before_import":0<=dep_run<import_marker,
      "dependency_requires_19_checks":'dependency.get("checks_passed")!=19' in text,
      "bundle_selftest_requires_13":'bundle_selftest.get("result")!="13/13 PASS"' in text,
      "validator_override_before_main":0<=text.find('module.QUEUE_REQUEST_VALIDATOR=QUEUE_VALIDATOR')<core_marker,
      "selftest_override_before_main":0<=text.find('module.QUEUE_REQUEST_SELFTEST=QUEUE_SELFTEST')<core_marker,
      "single_core_main_call":text.count('module.main()')==1,
      "output_validator_after_core":out_marker>core_marker and 'output_validation.get("checks_passed")!=58' in text,
      "bundle_validator_after_output":bundle_marker>out_marker and 'bundle_validation.get("checks_passed")!=64' in text,
      "bundle_validator_before_acceptance":0<=bundle_marker<accept_marker,
      "no_unapproved_cross_slot_token":all(token not in text for token in ("future_growth_2","future_growth_3")),
      "no_direct_network_call":all(token not in text for token in ("urlopen(","requests.get(","httpx.get(")),
      "no_business_or_final_claim":all(token not in text for token in ('actual_business_data_rows_written":1','final_ready":True','business_progress_claimed":True')),
    }
    failed=[k for k,v in checks.items() if not v]
    return {"schema_version":3,"slot_id":SLOT_ID,"validation_kind":"REVISION8_GUARDED_RUNTIME_WITH_BUNDLE_STATIC_FAIL_CLOSED","result":"PASS" if not failed else "FAIL","checks_passed":sum(checks.values()),"checks_total":len(checks),"checks":checks,"failed_checks":failed,"runner_execution_claimed":False,"business_progress_claimed":False,"final_ready":False}

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("wrapper",type=Path); p.add_argument("--output",type=Path); args=p.parse_args()
    try: result=validate_text(args.wrapper.read_text(encoding="utf-8"))
    except Exception as exc: result={"schema_version":3,"slot_id":SLOT_ID,"validation_kind":"REVISION8_GUARDED_RUNTIME_WITH_BUNDLE_STATIC_FAIL_CLOSED","result":"FAIL","checks_passed":0,"checks_total":1,"checks":{"read":False},"failed_checks":[f"{type(exc).__name__}:{exc}"],"runner_execution_claimed":False,"business_progress_claimed":False,"final_ready":False}
    text=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
    if args.output: args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(text,encoding="utf-8")
    else: sys.stdout.write(text)
    return 0 if result["result"]=="PASS" else 2
if __name__=="__main__": raise SystemExit(main())
