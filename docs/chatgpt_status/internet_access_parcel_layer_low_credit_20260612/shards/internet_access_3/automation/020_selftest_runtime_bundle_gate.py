#!/usr/bin/env python3
"""Deterministic network-free tests for 019_runtime_bundle_gate.py."""
from __future__ import annotations
import copy
import importlib.util
import json
import tempfile
from pathlib import Path
from typing import Any, Callable
ROOT = Path(__file__).parent
def load() -> Any:
    spec = importlib.util.spec_from_file_location("gate019", ROOT / "019_runtime_bundle_gate.py")
    if spec is None or spec.loader is None: raise RuntimeError("cannot load gate019")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module
def sha(seed: str) -> str: return (seed * 64)[:64]
def fixtures(root: Path) -> tuple[Path, Path, Path]:
    members = []
    for area, rows, retained in (("AA", 2, 1), ("BB", 1, 0)):
        members.append({"file": f"202601_fixed_postcode_coverage_r2_{area}.csv","postcode_area": area,"rows": rows,"retained_needed_rows": retained,"sha256": sha(area.lower()),"crc32": "1234abcd"})
    candidate_manifest = {"schema_version":5,"slot_id":"internet_access_3","parcel_start":10,"parcel_end":12,"canonical_rows":3,"current_r2_postcode_proxy_rows":1,"identity_conflict_rows":1,"postcode_not_found_in_current_r2_rows":0,"no_verified_postcode_rows":1,"no_data_rows":2,"ofcom_postcodes_scanned":3,"ofcom_unique_postcodes":3,"needed_postcodes":1,"ofcom_postcodes_retained":1,"needed_postcodes_not_found":0,"ofcom_source_files":members,"ofcom_source_mode":"DIRECT_ZIP_STREAM_NO_CSV_EXTRACTION","ofcom_csv_extracted_to_disk":False,"postcode_uniqueness_strategy":"AREA_PARTITIONED_EXACT_PER_MEMBER_SET","memory_strategy":"AREA_PARTITIONED_EXACT_UNIQUENESS_PLUS_NEEDED_POSTCODE_ROWS_ONLY","postcode_area_member_count":2,"zip_member_stream_sha256_count":2,"zip_member_crc_verified_by_complete_stream_read":True,"ofcom_zip_sha256":sha("f"),"canonical_source_sha256":sha("c"),"legacy_internet_source_sha256":sha("d"),"actual_business_data_rows_written":0,"scores_written":0,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False,"final_ready":False}
    slice_manifest = {"schema_version":3,"slot_id":"internet_access_3","row_partition":{"start":10,"end":12,"expected":3},"canonical":{"rows":3,"unique_row_numbers":3,"unique_parcel_ids":3,"output_sha256":sha("c"),"source_sha256":sha("e"),"first_rows":[{"row_no":10,"parcel_id":"parcel_10","hmlr_inspire_id":"A"},{"row_no":11,"parcel_id":"parcel_11","hmlr_inspire_id":"B"},{"row_no":12,"parcel_id":"parcel_12","hmlr_inspire_id":"C"}]},"legacy_internet":{"rows":2,"unique_row_numbers":2,"unique_parcel_ids":2,"output_sha256":sha("d"),"source_sha256":sha("a")},"output_semantics":"BOUNDED_INPUT_SLICE_ONLY_NO_BUSINESS_VALUES","actual_business_data_rows_written":0,"scores_written":0,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False,"final_ready":False}
    rows = [
        {"slot_id":"internet_access_3","canonical_row_no":10,"canonical_program_parcel_id":"parcel_10","postcode":"AA11AA","source_level":"POSTCODE_PROXY","internet_match_confidence":0.9,"internet_availability_quality_percent":None,"internet_quality_band":None,"calculation_version":None,"status":"CURRENT_R2_POSTCODE_PROXY_READY_FOR_REVIEW","business_row_written":False,"source_revision":"r2","source_snapshot_date":"2026-01","sfbb_30mbps_available_pct":90,"ufbb_100mbps_available_pct":80,"ufbb_300mbps_available_pct":70,"gigabit_available_pct":60,"unable_30mbps_pct":10,"unable_decent_fixed_or_fwa_pct":5},
        {"slot_id":"internet_access_3","canonical_row_no":11,"canonical_program_parcel_id":"parcel_11","postcode":"BB11BB","source_level":"NO_DATA","internet_match_confidence":0.0,"internet_availability_quality_percent":None,"internet_quality_band":None,"calculation_version":None,"status":"IDENTITY_CONFLICT_NO_DATA","business_row_written":False, **{k:None for k in ("sfbb_30mbps_available_pct","ufbb_100mbps_available_pct","ufbb_300mbps_available_pct","gigabit_available_pct","unable_30mbps_pct","unable_decent_fixed_or_fwa_pct")}},
        {"slot_id":"internet_access_3","canonical_row_no":12,"canonical_program_parcel_id":"parcel_12","postcode":None,"source_level":"NO_DATA","internet_match_confidence":0.0,"internet_availability_quality_percent":None,"internet_quality_band":None,"calculation_version":None,"status":"NO_VERIFIED_POSTCODE_NO_DATA","business_row_written":False, **{k:None for k in ("sfbb_30mbps_available_pct","ufbb_100mbps_available_pct","ufbb_300mbps_available_pct","gigabit_available_pct","unable_30mbps_pct","unable_decent_fixed_or_fwa_pct")}}
    ]
    mp=root/"manifest.json"; sp=root/"slice.json"; jp=root/"rows.jsonl"
    mp.write_text(json.dumps(candidate_manifest),encoding="utf-8"); sp.write_text(json.dumps(slice_manifest),encoding="utf-8"); jp.write_text("".join(json.dumps(x)+"\n" for x in rows),encoding="utf-8"); return mp,jp,sp
def expect_fail(fn: Callable[[], None]) -> None:
    try: fn()
    except Exception: return
    raise AssertionError("expected failure")
def main() -> int:
    gate=load(); results=[]
    with tempfile.TemporaryDirectory() as td:
        root=Path(td); mp,jp,sp=fixtures(root); out=root/"out.json"
        value=gate.validate_bundle(mp,jp,sp,out,start=10,end=12,rows=3,ofcom_rows=3,members=2); assert value["state"]=="PASS_VALIDATED_RUNTIME_BUNDLE_REVIEW_ONLY" and value["counts"]["canonical_rows"]==3; results.append("valid_bundle")
        legacy=json.loads(mp.read_text()); legacy["memory_strategy"]="GLOBAL_POSTCODE_UNIQUENESS_SET_PLUS_NEEDED_POSTCODE_ROWS_ONLY"; lp=root/"legacy_memory.json"; lp.write_text(json.dumps(legacy)); legacy_out=gate.validate_bundle(lp,jp,sp,out,start=10,end=12,rows=3,ofcom_rows=3,members=2); assert legacy_out["memory_strategy"]["legacy_label_normalized"] is True; results.append("legacy_memory_label_normalized")
        base_m=json.loads(mp.read_text()); base_s=json.loads(sp.read_text()); base_rows=[json.loads(x) for x in jp.read_text().splitlines()]; cases=[]
        def mcase(name,change):
            m=copy.deepcopy(base_m); change(m); p=root/f"{name}.json"; p.write_text(json.dumps(m)); cases.append((name,lambda p=p:gate.validate_bundle(p,jp,sp,out,start=10,end=12,rows=3,ofcom_rows=3,members=2)))
        def scase(name,change):
            s=copy.deepcopy(base_s); change(s); p=root/f"{name}.json"; p.write_text(json.dumps(s)); cases.append((name,lambda p=p:gate.validate_bundle(mp,jp,p,out,start=10,end=12,rows=3,ofcom_rows=3,members=2)))
        def rcase(name,change):
            r=copy.deepcopy(base_rows); change(r); p=root/f"{name}.jsonl"; p.write_text("".join(json.dumps(x)+"\n" for x in r)); cases.append((name,lambda p=p:gate.validate_bundle(mp,p,sp,out,start=10,end=12,rows=3,ofcom_rows=3,members=2)))
        mcase("slot",lambda m:m.update(slot_id="wrong")); mcase("partition",lambda m:m.update(canonical_rows=2)); mcase("status_sum",lambda m:m.update(no_verified_postcode_rows=0)); mcase("no_data",lambda m:m.update(no_data_rows=1)); mcase("source_mode",lambda m:m.update(ofcom_source_mode="wrong")); mcase("csv_extract",lambda m:m.update(ofcom_csv_extracted_to_disk=True)); mcase("uniqueness",lambda m:m.update(postcode_uniqueness_strategy="wrong")); mcase("memory",lambda m:m.update(memory_strategy="UNKNOWN")); mcase("ofcom_rows",lambda m:m.update(ofcom_postcodes_scanned=2)); mcase("member_count",lambda m:m.update(postcode_area_member_count=1)); mcase("needed_partition",lambda m:m.update(needed_postcodes=2)); mcase("member_duplicate_area",lambda m:m["ofcom_source_files"][1].update(postcode_area="AA",file="202601_fixed_postcode_coverage_r2_AA.csv")); mcase("member_total",lambda m:m["ofcom_source_files"][0].update(rows=1)); mcase("crc",lambda m:m["ofcom_source_files"][0].update(crc32="bad")); mcase("business",lambda m:m.update(actual_business_data_rows_written=1)); mcase("score",lambda m:m.update(scores_written=1))
        scase("slice_partition",lambda s:s["row_partition"].update(start=11)); scase("slice_rows",lambda s:s["canonical"].update(rows=2)); scase("slice_first",lambda s:s["canonical"]["first_rows"][0].update(parcel_id="wrong")); scase("slice_hash",lambda s:s["canonical"].update(output_sha256=sha("x"))); scase("slice_business",lambda s:s.update(actual_business_data_rows_written=1))
        rcase("row_sequence",lambda r:r[1].update(canonical_row_no=12)); rcase("row_parcel",lambda r:r[0].update(canonical_program_parcel_id="wrong")); rcase("row_score",lambda r:r[0].update(internet_availability_quality_percent=50)); rcase("row_percent",lambda r:r[0].update(gigabit_available_pct=101)); rcase("row_no_data_value",lambda r:r[1].update(gigabit_available_pct=10)); rcase("row_status",lambda r:r[2].update(status="WRONG")); rcase("row_count",lambda r:r.pop())
        for name,fn in cases: expect_fail(fn); results.append(name)
    print(json.dumps({"passed":len(results),"total":len(results),"results":[{"test":x,"state":"PASS"} for x in results]},sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
