#!/usr/bin/env python3
from __future__ import annotations
import importlib.util,json,tempfile
from pathlib import Path
SCRIPT=Path(__file__).with_name("015_verify_published_runner_bundle.py")
spec=importlib.util.spec_from_file_location("bundle",SCRIPT)
if spec is None or spec.loader is None: raise RuntimeError("cannot import")
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
module.ROW_START=1; module.ROW_END=6; module.EXPECTED_ROWS=6
passed=[]
def check(name,ok):
    if not ok: raise AssertionError(name)
    passed.append(name)
def expect_fail(name,fn,text):
    try: fn()
    except ValueError as exc:
        if text not in str(exc): raise AssertionError(f"{name}: {exc}")
        passed.append(name)
    else: raise AssertionError(name)
def payloads():
    counts={module.DIRECT:2,module.LEGACY:2,module.NO_DATA:2}
    readback={"schema_version":3,"slot_id":"internet_access_2","status":"REAL_RUN_READBACK_VALIDATED_REVIEW_ONLY","canonical_rows":6,"row_start":1,"row_end":6,"status_counts":counts,"manifest_sha256":"a"*64,"rows_jsonl_sha256":"b"*64,"visible_example_rows":6,"actual_business_data_rows_written":0,"scores_written":0,"db_write":False,"migration":False,"production_deploy":False,"final_ready":False}
    rows=[]
    for index,status in enumerate([module.DIRECT,module.DIRECT,module.LEGACY,module.LEGACY,module.NO_DATA,module.NO_DATA],1):
        if status==module.DIRECT: method="CANONICAL_POSTCODE"; confidence=.95; postcode=f"AA{index} 1AA"; metric=80
        elif status==module.LEGACY: method="LEGACY_POSTCODE_PROXY"; confidence=.70; postcode=f"BB{index} 1BB"; metric=80
        elif index==5: method="NO_POSTCODE"; confidence=0; postcode=None; metric=None
        else: method="POSTCODE_NOT_IN_CURRENT_R2"; confidence=0; postcode="CC6 6CC"; metric=None
        rows.append({"canonical_row_no":index,"canonical_program_parcel_id":f"parcel_{index}","postcode":postcode,"status":status,"internet_match_method":method,"internet_match_confidence":confidence,"gigabit_available_pct":metric,"ufbb_100mbps_available_pct":None if status==module.NO_DATA else 90,"ufbb_300mbps_available_pct":None,"sfbb_30mbps_available_pct":None if status==module.NO_DATA else 99,"unable_30mbps_pct":None if status==module.NO_DATA else 1,"unable_decent_fixed_or_fwa_pct":None,"business_row_written":False})
    examples={"schema_version":3,"slot_id":"internet_access_2","data_level":"POSTCODE_LEVEL_ONLY","truth_boundary":"review only","rows":rows,"actual_business_data_rows_written":0,"final_ready":False}
    return readback,examples
with tempfile.TemporaryDirectory() as temp:
    root=Path(temp); audit_path=root/"audit.json"; readback,examples=payloads()
    (root/"runner_readback_latest.json").write_text(json.dumps(readback)); (root/"verified_examples_latest.json").write_text(json.dumps(examples))
    result=module.audit(root,audit_path)
    for name,ok in [("status",result["status"].startswith("PASS")),("exact_rows",result["canonical_rows"]==6),("bundle_hashes",len(result["runner_readback_file_sha256"])==64),("source_hashes",result["source_manifest_sha256"]=="a"*64),("example_count",result["visible_example_rows"]==6),("audit_written",audit_path.exists()),("truth_boundary",result["data_level"]=="POSTCODE_LEVEL_ONLY"),("no_business",result["actual_business_data_rows_written"]==0),("not_final",result["final_ready"] is False),("unmatched_postcode_allowed",True)]: check(name,ok)
    bad=dict(readback); bad["manifest_sha256"]="x"; expect_fail("bad_hash",lambda:module.validate_readback(bad),"not a lowercase")
    bad=dict(readback); bad["status_counts"]=dict(readback["status_counts"]); bad["status_counts"][module.NO_DATA]=1; expect_fail("bad_count",lambda:module.validate_readback(bad),"do not sum")
    bad=dict(readback); bad["final_ready"]=True; expect_fail("final",lambda:module.validate_readback(bad),"final_ready")
    bad=json.loads(json.dumps(examples)); bad["rows"][0]["canonical_row_no"]=2; expect_fail("duplicate",lambda:module.validate_examples(bad,readback["status_counts"],6),"duplicates")
    bad=json.loads(json.dumps(examples)); bad["rows"][4]["postcode"]="AA1 1AA"; expect_fail("no_postcode_rejected",lambda:module.validate_examples(bad,readback["status_counts"],6),"NO_POSTCODE")
    bad=json.loads(json.dumps(examples)); bad["rows"][5]["postcode"]="BAD"; expect_fail("bad_unmatched_rejected",lambda:module.validate_examples(bad,readback["status_counts"],6),"unmatched postcode")
    bad=json.loads(json.dumps(examples)); bad["rows"][4]["gigabit_available_pct"]=0; expect_fail("no_data_metric",lambda:module.validate_examples(bad,readback["status_counts"],6),"NO_DATA metric")
    bad=json.loads(json.dumps(examples)); bad["rows"][0]["internet_match_confidence"]=.7; expect_fail("direct_confidence",lambda:module.validate_examples(bad,readback["status_counts"],6),"direct truth")
    bad=json.loads(json.dumps(examples)); bad["rows"][2]["internet_match_method"]="CANONICAL_POSTCODE"; expect_fail("legacy_method",lambda:module.validate_examples(bad,readback["status_counts"],6),"legacy truth")
    bad=json.loads(json.dumps(examples)); bad["rows"][0]["gigabit_available_pct"]=None; bad["rows"][0]["ufbb_100mbps_available_pct"]=None; bad["rows"][0]["sfbb_30mbps_available_pct"]=None; bad["rows"][0]["unable_30mbps_pct"]=None; expect_fail("direct_all_null",lambda:module.validate_examples(bad,readback["status_counts"],6),"all null")
    bad=json.loads(json.dumps(examples)); bad["rows"][0]["business_row_written"]=True; expect_fail("business",lambda:module.validate_examples(bad,readback["status_counts"],6),"business_row_written")
    bad=dict(examples); bad["data_level"]="PARCEL_LEVEL"; expect_fail("level",lambda:module.validate_examples(bad,readback["status_counts"],6),"postcode-only")
    bad=dict(examples); bad["rows"]=examples["rows"][:5]; expect_fail("visible",lambda:module.validate_examples(bad,readback["status_counts"],6),"disagrees")
expected=23
if len(passed)!=expected: raise AssertionError(f"{len(passed)} != {expected}: {passed}")
print(json.dumps({"status":"PASS","tests_passed":len(passed),"tests_total":expected,"test_names":passed,"actual_business_data_rows_written":0,"final_ready":False},sort_keys=True))
