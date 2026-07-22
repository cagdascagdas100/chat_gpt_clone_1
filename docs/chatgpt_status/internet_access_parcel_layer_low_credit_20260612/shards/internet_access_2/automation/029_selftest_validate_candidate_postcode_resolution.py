#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, json, tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("028_validate_candidate_postcode_resolution.py")
spec = importlib.util.spec_from_file_location("postcode_resolution", SCRIPT)
if spec is None or spec.loader is None: raise RuntimeError("cannot import postcode resolution validator")
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
module.ROW_START = 1; module.ROW_END = 5; module.EXPECTED_ROWS = 5
passed=[]

def check(name, ok):
    if not ok: raise AssertionError(name)
    passed.append(name)

def expect_fail(name, mutate, text):
    rows=base_rows(); mutate(rows)
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/"rows.jsonl"; path.write_text("".join(json.dumps(r)+"\n" for r in rows),encoding="utf-8")
        try: module.audit(path)
        except ValueError as exc:
            if text not in str(exc): raise AssertionError(f"{name}: {exc}")
            passed.append(name)
        else: raise AssertionError(name)

def common(i):
    return {"slot_id":"internet_access_2","canonical_row_no":i,"canonical_program_parcel_id":f"parcel_{i}","internet_availability_quality_percent":None,"promotion_state":"REVIEW_ONLY_NOT_PROMOTED","business_row_written":False,"fake_data":False}

def base_rows():
    return [
      dict(common(1),postcode="AA11AA",canonical_postcode_candidate="AA11AA",canonical_postcode_valid=True,legacy_postcode_candidate=None,legacy_postcode_valid=False,postcode_resolution="CANONICAL_VALID",postcode_conflict=False,invalid_postcode_candidates=[],status=module.DIRECT,internet_match_method="CANONICAL_POSTCODE",internet_match_confidence=.95),
      dict(common(2),postcode="BB22BB",canonical_postcode_candidate=None,canonical_postcode_valid=False,legacy_postcode_candidate="BB22BB",legacy_postcode_valid=True,postcode_resolution="LEGACY_VALID_FALLBACK_CANONICAL_MISSING",postcode_conflict=False,invalid_postcode_candidates=[],status=module.LEGACY,internet_match_method="LEGACY_POSTCODE_PROXY",internet_match_confidence=.70),
      dict(common(3),postcode="BB22BB",canonical_postcode_candidate="BAD",canonical_postcode_valid=False,legacy_postcode_candidate="BB22BB",legacy_postcode_valid=True,postcode_resolution="LEGACY_VALID_FALLBACK_CANONICAL_INVALID",postcode_conflict=False,invalid_postcode_candidates=["BAD"],status=module.LEGACY,internet_match_method="LEGACY_POSTCODE_PROXY",internet_match_confidence=.70),
      dict(common(4),postcode="AA11AA",canonical_postcode_candidate="AA11AA",canonical_postcode_valid=True,legacy_postcode_candidate="BB22BB",legacy_postcode_valid=True,postcode_resolution="CANONICAL_VALID_LEGACY_CONFLICT_IGNORED",postcode_conflict=True,invalid_postcode_candidates=[],status=module.DIRECT,internet_match_method="CANONICAL_POSTCODE",internet_match_confidence=.95),
      dict(common(5),postcode=None,canonical_postcode_candidate="BAD",canonical_postcode_valid=False,legacy_postcode_candidate=None,legacy_postcode_valid=False,postcode_resolution="NO_VALID_POSTCODE",postcode_conflict=False,invalid_postcode_candidates=["BAD"],status=module.NO_DATA,internet_match_method="NO_POSTCODE",internet_match_confidence=0),
    ]

with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp); rows_path=root/"rows.jsonl"; audit_path=root/"audit.json"
    rows_path.write_text("".join(json.dumps(r)+"\n" for r in base_rows()),encoding="utf-8")
    result=module.audit(rows_path,audit_path)
    for name,ok in [
      ("status",result["status"]=="PASS_CANDIDATE_POSTCODE_RESOLUTION_AUDITED_REVIEW_ONLY"),
      ("exact_rows",result["canonical_rows"]==5),
      ("resolution_counts",sum(result["resolution_counts"].values())==5),
      ("fallback_count",result["legacy_fallback_rows"]==2),
      ("conflict_count",result["canonical_legacy_conflict_rows"]==1),
      ("invalid_count",result["invalid_postcode_candidate_rows"]==2),
      ("audit_written",audit_path.is_file()),
      ("no_business",result["actual_business_data_rows_written"]==0),
      ("not_final",result["final_ready"] is False),
    ]: check(name,ok)

expect_fail("validity_flag_rejected",lambda r:r[0].update(canonical_postcode_valid=False),"validity flag")
expect_fail("invalid_selected_rejected",lambda r:r[4].update(postcode="BAD"),"invalid postcode leaked")
expect_fail("conflict_flag_rejected",lambda r:r[3].update(postcode_conflict=False),"conflict flag")
expect_fail("direct_resolution_rejected",lambda r:r[0].update(postcode_resolution="NO_VALID_POSTCODE"),"resolution reason")
expect_fail("legacy_resolution_rejected",lambda r:r[2].update(postcode_resolution="CANONICAL_VALID"),"resolution reason")
expect_fail("invalid_list_rejected",lambda r:r[2].update(invalid_postcode_candidates=[]),"invalid postcode candidate list")
expect_fail("duplicate_parcel_rejected",lambda r:r[1].update(canonical_program_parcel_id="parcel_1"),"duplicate")
expect_fail("score_rejected",lambda r:r[0].update(internet_availability_quality_percent=50),"score unexpectedly")
expect_fail("business_write_rejected",lambda r:r[0].update(business_row_written=True),"review-only write")

expected=18
if len(passed)!=expected: raise AssertionError(f"{len(passed)} != {expected}: {passed}")
print(json.dumps({"status":"PASS","tests_passed":len(passed),"tests_total":expected,"test_names":passed,"actual_business_data_rows_written":0,"final_ready":False},sort_keys=True))
