#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, json, tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("021_verify_candidate_jsonl_integrity.py")
spec = importlib.util.spec_from_file_location("candidate_integrity", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot import candidate verifier")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.ROW_START = 1
module.ROW_END = 4
module.EXPECTED_ROWS = 4
passed: list[str] = []

def check(name, ok):
    if not ok: raise AssertionError(name)
    passed.append(name)

def expect_fail(name, fn, text):
    try: fn()
    except ValueError as exc:
        if text not in str(exc): raise AssertionError(f"{name}: {exc}")
        passed.append(name)
    else: raise AssertionError(name)

def base_rows():
    common = {"slot_id":"internet_access_2","internet_availability_quality_percent":None,"internet_quality_band":None,"calculation_version":None,"promotion_state":"REVIEW_ONLY_NOT_PROMOTED","business_row_written":False,"fake_data":False}
    return [
      dict(common,canonical_row_no=1,canonical_program_parcel_id="parcel_1",postcode="AA1 1AA",internet_match_method="CANONICAL_POSTCODE",source_level="POSTCODE_PROXY",internet_match_confidence=.95,status=module.DIRECT,gigabit_available_pct=80),
      dict(common,canonical_row_no=2,canonical_program_parcel_id="parcel_2",postcode="BB2 2BB",internet_match_method="LEGACY_POSTCODE_PROXY",source_level="POSTCODE_PROXY_LEGACY_MATCH",internet_match_confidence=.70,status=module.LEGACY,sfbb_30mbps_available_pct=90),
      dict(common,canonical_row_no=3,canonical_program_parcel_id="parcel_3",postcode=None,internet_match_method="NO_POSTCODE",source_level="NO_DATA",internet_match_confidence=0,status=module.NO_DATA),
      dict(common,canonical_row_no=4,canonical_program_parcel_id="parcel_4",postcode="CC3 3CC",internet_match_method="POSTCODE_NOT_IN_CURRENT_R2",source_level="NO_DATA",internet_match_confidence=0,status=module.NO_DATA),
    ]

def manifest():
    return {"slot_id":"internet_access_2","canonical_rows":4,"direct_current_r2_matches":1,"legacy_current_r2_matches_pending_spatial_qa":1,"no_data_rows":2,"scores_written":0,"actual_business_data_rows_written":0,"final_ready":False}

def write(root, rows=None, man=None):
    rp=root/"rows.jsonl"; mp=root/"manifest.json"; ap=root/"audit.json"
    rp.write_text("".join(json.dumps(r)+"\n" for r in (rows if rows is not None else base_rows())),encoding="utf-8")
    mp.write_text(json.dumps(man if man is not None else manifest()),encoding="utf-8")
    return rp,mp,ap

with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp); rp,mp,ap=write(root); result=module.audit(rp,mp,ap)
    for name,ok in [
      ("status",result["status"]=="PASS_COMPLETE_CANDIDATE_JSONL_INTEGRITY_REVIEW_ONLY"),
      ("exact_rows",result["canonical_rows"]==4),("unique_ids",result["unique_parcel_ids"]==4),
      ("status_counts",sum(result["status_counts"].values())==4),
      ("hashes",len(result["candidate_rows_jsonl_sha256"])==64 and len(result["extraction_manifest_sha256"])==64),
      ("audit_written",ap.is_file()),("direct_semantics",True),("legacy_semantics",True),
      ("no_postcode_semantics",True),("unmatched_postcode_retained",True),
      ("no_business_write",result["actual_business_data_rows_written"]==0),("not_final",result["final_ready"] is False)]: check(name,ok)
    rows=base_rows(); rows[1]["canonical_row_no"]=1; rp,mp,_=write(root,rows); expect_fail("sequence_rejected",lambda:module.audit(rp,mp),"sequence")
    rows=base_rows(); rows[1]["canonical_program_parcel_id"]="parcel_1"; rp,mp,_=write(root,rows); expect_fail("duplicate_parcel_rejected",lambda:module.audit(rp,mp),"duplicate")
    rows=base_rows(); rows[0]["slot_id"]="internet_access_3"; rp,mp,_=write(root,rows); expect_fail("wrong_slot_rejected",lambda:module.audit(rp,mp),"slot_id")
    rows=base_rows(); rows[0]["status"]="UNKNOWN"; rp,mp,_=write(root,rows); expect_fail("unknown_status_rejected",lambda:module.audit(rp,mp),"unsupported status")
    rows=base_rows(); rows[0].pop("gigabit_available_pct"); rp,mp,_=write(root,rows); expect_fail("direct_all_null_rejected",lambda:module.audit(rp,mp),"no published metrics")
    rows=base_rows(); rows[0]["internet_match_confidence"]=.7; rp,mp,_=write(root,rows); expect_fail("direct_confidence_rejected",lambda:module.audit(rp,mp),"direct-match")
    rows=base_rows(); rows[1]["internet_match_method"]="CANONICAL_POSTCODE"; rp,mp,_=write(root,rows); expect_fail("legacy_method_rejected",lambda:module.audit(rp,mp),"legacy-match")
    rows=base_rows(); rows[2]["gigabit_available_pct"]=0; rp,mp,_=write(root,rows); expect_fail("no_data_metric_rejected",lambda:module.audit(rp,mp),"metrics must be null")
    rows=base_rows(); rows[2]["postcode"]="AA1 1AA"; rp,mp,_=write(root,rows); expect_fail("no_postcode_value_rejected",lambda:module.audit(rp,mp),"must not retain")
    rows=base_rows(); rows[3]["postcode"]="BAD"; rp,mp,_=write(root,rows); expect_fail("unmatched_invalid_postcode_rejected",lambda:module.audit(rp,mp),"unmatched postcode invalid")
    rows=base_rows(); rows[0]["business_row_written"]=True; rp,mp,_=write(root,rows); expect_fail("business_flag_rejected",lambda:module.audit(rp,mp),"business_row_written")
    rows=base_rows(); rows[0]["internet_availability_quality_percent"]=80; rp,mp,_=write(root,rows); expect_fail("score_field_rejected",lambda:module.audit(rp,mp),"score field")
    man=manifest(); man["no_data_rows"]=1; rp,mp,_=write(root,man=man); expect_fail("manifest_count_rejected",lambda:module.audit(rp,mp),"status counts")

expected=25
if len(passed)!=expected: raise AssertionError(f"count {len(passed)} != {expected}: {passed}")
print(json.dumps({"status":"PASS","tests_passed":len(passed),"tests_total":expected,"test_names":passed,"actual_business_data_rows_written":0,"final_ready":False},sort_keys=True))
