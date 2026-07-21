#!/usr/bin/env python3
from __future__ import annotations
import copy, importlib.util, json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path); assert spec and spec.loader
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
gate=load("repro",HERE/"040_runtime_reproducibility_gate.py")
imp=load("imp",HERE/"023_import_validated_runtime_bundle_to_web.py")
START=10; END=13; ROWS=4; STAT=imp.EXPECTED_STATUSES
def h(ch): return ch*64
def sample(row,status,postcode=None):
    return {"slot_id":"internet_access_3","canonical_row_no":row,"canonical_program_parcel_id":f"parcel_{row}","status":status,"postcode":postcode,"source_level":"POSTCODE_PROXY" if status==STAT[0] else "NO_DATA","internet_match_confidence":0.9 if status==STAT[0] else 0.0,"business_row_written":False,"internet_availability_quality_percent":None}
def receipt():
    return {"schema_version":1,"slot_id":"internet_access_3","state":"PASS_VALIDATED_RUNTIME_BUNDLE_REVIEW_ONLY","row_partition":{"start":START,"end":END,"rows":ROWS},"gates":[{"gate_no":i,"name":f"G{i}","state":"PASS"} for i in range(1,9)],"counts":{"canonical_rows":4,"current_r2_postcode_proxy_rows":1,"identity_conflict_rows":1,"postcode_not_found_in_current_r2_rows":1,"no_verified_postcode_rows":1,"no_data_rows":3,"ofcom_postcodes_scanned":1741096,"postcode_area_members":121},"hashes":{"candidate_manifest_sha256":h("a"),"candidates_jsonl_sha256":h("b"),"slice_manifest_sha256":h("c"),"ofcom_zip_sha256":h("d"),"canonical_slice_sha256":h("e"),"legacy_slice_sha256":h("f")},"samples":[sample(10,STAT[0],"AB12CD"),sample(11,STAT[1]),sample(12,STAT[2]),sample(13,STAT[3])],"actual_business_data_rows_written":0,"scores_written":0,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False,"final_ready":False}
tests=[]
def check(name,fn):
    try: fn(); tests.append((name,True,""))
    except Exception as e: tests.append((name,False,str(e)))
def compare(a,b): return gate.compare_values(a,b,importer_module=imp,start=START,end=END,rows=ROWS)
def expect_status(mutator,expected):
    a=receipt(); b=copy.deepcopy(a); mutator(b); r=compare(a,b)
    assert r["status"]==expected,(r["status"],expected)
    assert r["automatic_acceptance"] is False
    assert r["actual_business_data_rows_written"]==0 and r["final_ready"] is False
def expect_reject(mutator):
    a=receipt(); b=copy.deepcopy(a); mutator(b)
    try: compare(a,b)
    except gate.GateError: return
    raise AssertionError("expected GateError")
check("exact_status",lambda:expect_status(lambda x:None,gate.PASS_EXACT))
check("exact_flag",lambda: (_ for _ in ()).throw(AssertionError()) if not compare(receipt(),receipt())["exact_reproducibility_pass"] else None)
check("metadata_candidate_manifest",lambda:expect_status(lambda x:x["hashes"].__setitem__("candidate_manifest_sha256",h("9")),gate.REVIEW_METADATA))
check("metadata_slice_manifest",lambda:expect_status(lambda x:x["hashes"].__setitem__("slice_manifest_sha256",h("8")),gate.REVIEW_METADATA))
check("ofcom_input_drift",lambda:expect_status(lambda x:x["hashes"].__setitem__("ofcom_zip_sha256",h("7")),gate.BLOCK_SOURCE))
check("canonical_input_drift",lambda:expect_status(lambda x:x["hashes"].__setitem__("canonical_slice_sha256",h("6")),gate.BLOCK_SOURCE))
check("legacy_input_drift",lambda:expect_status(lambda x:x["hashes"].__setitem__("legacy_slice_sha256",h("5")),gate.BLOCK_SOURCE))
check("jsonl_nondeterminism",lambda:expect_status(lambda x:x["hashes"].__setitem__("candidates_jsonl_sha256",h("4")),gate.BLOCK_OUTPUT))
def mutate_counts(x):
    x["counts"]["current_r2_postcode_proxy_rows"]=2; x["counts"]["no_verified_postcode_rows"]=0; x["counts"]["no_data_rows"]=2
check("count_nondeterminism",lambda:expect_status(mutate_counts,gate.BLOCK_OUTPUT))
check("sample_receipt_drift",lambda:expect_status(lambda x:x["samples"][0].__setitem__("postcode","ZZ99ZZ"),gate.BLOCK_RECEIPT))
check("gate_name_drift",lambda:expect_status(lambda x:x["gates"][0].__setitem__("name","ALTERED"),gate.BLOCK_RECEIPT))
check("wrong_slot_rejected",lambda:expect_reject(lambda x:x.__setitem__("slot_id","internet_access_2")))
check("wrong_state_rejected",lambda:expect_reject(lambda x:x.__setitem__("state","WAITING")))
check("wrong_partition_rejected",lambda:expect_reject(lambda x:x["row_partition"].__setitem__("rows",5)))
check("invalid_hash_rejected",lambda:expect_reject(lambda x:x["hashes"].__setitem__("ofcom_zip_sha256","bad")))
check("truth_fake_rejected",lambda:expect_reject(lambda x:x.__setitem__("fake_data",True)))
check("business_write_rejected",lambda:expect_reject(lambda x:x.__setitem__("actual_business_data_rows_written",1)))
check("score_write_rejected",lambda:expect_reject(lambda x:x.__setitem__("scores_written",1)))
check("sample_duplicate_rejected",lambda:expect_reject(lambda x:x["samples"].__setitem__(1,copy.deepcopy(x["samples"][0]))))
check("sample_identity_rejected",lambda:expect_reject(lambda x:x["samples"][0].__setitem__("canonical_program_parcel_id","parcel_99")))
check("gate_nonpass_rejected",lambda:expect_reject(lambda x:x["gates"][0].__setitem__("state","FAILED")))
check("comparison_rows_six",lambda: (_ for _ in ()).throw(AssertionError()) if len(compare(receipt(),receipt())["comparisons"])!=6 else None)
check("manual_review_false_exact",lambda: (_ for _ in ()).throw(AssertionError()) if compare(receipt(),receipt())["manual_review_required"] else None)
def drifted():
    x=receipt(); x["hashes"]["ofcom_zip_sha256"]=h("1"); return x
check("manual_review_true_drift",lambda: (_ for _ in ()).throw(AssertionError()) if not compare(receipt(),drifted())["manual_review_required"] else None)
check("truth_flags_output",lambda: (_ for _ in ()).throw(AssertionError()) if not all(compare(receipt(),receipt())[k] is False for k in ("fake_data","db_write","migration","production_deploy","final_ready")) else None)
failed=[t for t in tests if not t[1]]
for name,ok,detail in tests: print("PASS" if ok else "FAIL",name,detail)
print(json.dumps({"passed":len(tests)-len(failed),"total":len(tests),"failed":len(failed)}))
raise SystemExit(1 if failed else 0)
