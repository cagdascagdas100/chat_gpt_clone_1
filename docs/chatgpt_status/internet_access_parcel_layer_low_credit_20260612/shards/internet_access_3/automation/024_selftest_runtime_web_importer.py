#!/usr/bin/env python3
"""Deterministic network-free tests for 023_import_validated_runtime_bundle_to_web.py."""
from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).parent


def load() -> Any:
    spec = importlib.util.spec_from_file_location("importer023", ROOT / "023_import_validated_runtime_bundle_to_web.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load importer023")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(seed: str) -> str:
    return (seed * 64)[:64]


def fixture() -> dict[str, Any]:
    samples = [
        {"slot_id":"internet_access_3","canonical_row_no":10,"canonical_program_parcel_id":"parcel_10","status":"CURRENT_R2_POSTCODE_PROXY_READY_FOR_REVIEW","business_row_written":False,"internet_availability_quality_percent":None},
        {"slot_id":"internet_access_3","canonical_row_no":11,"canonical_program_parcel_id":"parcel_11","status":"IDENTITY_CONFLICT_NO_DATA","business_row_written":False,"internet_availability_quality_percent":None},
    ]
    return {
        "schema_version":1,"slot_id":"internet_access_3","state":"PASS_VALIDATED_RUNTIME_BUNDLE_REVIEW_ONLY",
        "row_partition":{"start":10,"end":12,"rows":3},
        "gates":[{"gate_no":n,"name":f"G{n}","state":"PASS"} for n in range(1,9)],
        "counts":{"canonical_rows":3,"current_r2_postcode_proxy_rows":1,"identity_conflict_rows":1,"postcode_not_found_in_current_r2_rows":0,"no_verified_postcode_rows":1,"no_data_rows":2,"ofcom_postcodes_scanned":3,"postcode_area_members":2},
        "hashes":{"candidate_manifest_sha256":sha("a"),"candidates_jsonl_sha256":sha("b"),"slice_manifest_sha256":sha("c"),"ofcom_zip_sha256":sha("d"),"canonical_slice_sha256":sha("e"),"legacy_slice_sha256":sha("f")},
        "samples":samples,"actual_business_data_rows_written":0,"scores_written":0,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False,"final_ready":False,
    }


def expect_fail(fn: Callable[[], None]) -> None:
    try:
        fn()
    except Exception:
        return
    raise AssertionError("expected failure")


def main() -> int:
    module = load(); results: list[str] = []; base = fixture()
    value = module.validate_runtime_gate(copy.deepcopy(base), start=10, end=12, rows=3)
    assert value["counts"]["canonical_rows"] == 3; results.append("valid_gate")
    cases: list[tuple[str, Callable[[dict[str, Any]], None]]] = [
        ("wrong_slot", lambda x:x.update(slot_id="wrong")),
        ("wrong_state", lambda x:x.update(state="WAITING")),
        ("wrong_partition", lambda x:x["row_partition"].update(start=11)),
        ("failed_gate", lambda x:x["gates"][0].update(state="FAILED")),
        ("duplicate_gate", lambda x:x["gates"][1].update(gate_no=1)),
        ("count_partition", lambda x:x["counts"].update(no_verified_postcode_rows=0)),
        ("no_data_count", lambda x:x["counts"].update(no_data_rows=1)),
        ("bad_hash", lambda x:x["hashes"].update(ofcom_zip_sha256="bad")),
        ("sample_outside", lambda x:x["samples"][0].update(canonical_row_no=99,canonical_program_parcel_id="parcel_99")),
        ("sample_duplicate", lambda x:x["samples"][1].update(canonical_row_no=10,canonical_program_parcel_id="parcel_10")),
        ("sample_score", lambda x:x["samples"][0].update(internet_availability_quality_percent=50)),
        ("sample_write", lambda x:x["samples"][0].update(business_row_written=True)),
        ("truth_flag", lambda x:x.update(migration=True)),
        ("business_rows", lambda x:x.update(actual_business_data_rows_written=1)),
    ]
    for name, change in cases:
        broken = copy.deepcopy(base); change(broken)
        expect_fail(lambda broken=broken: module.validate_runtime_gate(broken,start=10,end=12,rows=3)); results.append(name)
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp); source=root/"gate.json"; output=root/"runtime_results_latest.json"; source.write_text(json.dumps(base),encoding="utf-8")
        payload=module.build_web_payload(module.validate_runtime_gate(base,start=10,end=12,rows=3),source); module.atomic_write_json(output,payload)
        written=json.loads(output.read_text(encoding="utf-8")); assert written["status"]=="REAL_RUNTIME_BUNDLE_VALIDATED_REVIEW_ONLY" and written["actual_business_data_rows_written"]==0; results.append("atomic_web_write")
    print(json.dumps({"passed":len(results),"total":len(results),"results":[{"test":x,"state":"PASS"} for x in results]},sort_keys=True)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
