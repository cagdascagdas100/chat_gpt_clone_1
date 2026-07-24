#!/usr/bin/env python3
"""Validate exact future_growth_1 rows 1-6 candidate-to-site pair identities."""
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path
from typing import Any

SLOT_ID="future_growth_1"
CONTRACT_REVISION=8


def read(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value,dict): raise ValueError("JSON object required")
    return value


def key(row:dict[str,Any])->tuple[Any,...]:
    return (int(row.get("row_no")),str(row.get("parcel_id") or ""),str(row.get("hmlr_inspire_id") or ""),str(row.get("source_reference") or ""),int(row.get("source_entity")),bool(row.get("source_current")))


def validate(manifest:dict[str,Any],candidate_payload:dict[str,Any])->dict[str,Any]:
    expected=manifest.get("pairs")
    actual=candidate_payload.get("candidates")
    checks={}
    checks["slot_exact"]=manifest.get("slot_id")==SLOT_ID
    checks["revision_exact"]=manifest.get("contract_revision")==CONTRACT_REVISION
    checks["semantics_exact"]=manifest.get("output_semantics")=="EXACT_RELATION_PAIR_INPUT_CONTRACT_NOT_POLYGON_EXECUTION_NOT_SCORE"
    checks["expected_pairs_15"]=isinstance(expected,list) and len(expected)==15
    checks["actual_pairs_15"]=isinstance(actual,list) and len(actual)==15
    expected_keys=[key(row) for row in expected] if isinstance(expected,list) else []
    actual_keys=[key(row) for row in actual] if isinstance(actual,list) else []
    checks["expected_unique"]=len(expected_keys)==len(set(expected_keys))==15
    checks["actual_unique"]=len(actual_keys)==len(set(actual_keys))==15
    checks["exact_pair_set"]=set(expected_keys)==set(actual_keys) and len(actual_keys)==15
    expected_by_key={key(row):row for row in expected or []}
    checks["distance_exact"]=isinstance(actual,list) and all(item_key in expected_by_key and isinstance(row.get("point_distance_m"),(int,float)) and math.isfinite(float(row["point_distance_m"])) and abs(float(row["point_distance_m"])-float(expected_by_key[item_key]["point_distance_m"]))<=1e-9 for row in actual for item_key in [key(row)])
    checks["row_parcel_identity"]=isinstance(actual,list) and all(row.get("parcel_id")==f"parcel_{int(row.get('row_no'))}" for row in actual)
    checks["current_partition_14"]=isinstance(actual,list) and sum(bool(row.get("source_current")) for row in actual)==14
    checks["stale_partition_1"]=isinstance(actual,list) and sum(not bool(row.get("source_current")) for row in actual)==1
    checks["current_refs_exact"]=isinstance(actual,list) and {str(row.get("source_reference")) for row in actual if row.get("source_current")}=={"LBBD49/XJ","LBBD64/XE","LBBD72/ZZ","LBBD91/DI"}
    checks["stale_ref_exact"]=isinstance(actual,list) and {str(row.get("source_reference")) for row in actual if not row.get("source_current")}=={"LBBD23"}
    checks["six_hmlr_ids_exact"]=isinstance(actual,list) and {str(row.get("hmlr_inspire_id")) for row in actual}==set(manifest.get("expected_hmlr_ids") or [])
    checks["no_scores"]=isinstance(actual,list) and all(row.get("future_growth_score") is None and not bool(row.get("scorable")) for row in actual)
    checks["input_polygons_unverified"]=isinstance(actual,list) and all(row.get("site_geometry_verified") is False and row.get("parcel_polygon_verified") is False for row in actual)
    checks["business_zero"]=manifest.get("quality_gates",{}).get("actual_business_data_rows_written")==0
    failed=[name for name,value in checks.items() if not value]
    return {"schema_version":1,"slot_id":SLOT_ID,"validation_kind":"REVISION8_EXACT_RELATION_PAIR_INPUT_CONTRACT","result":"PASS" if not failed else "FAIL","checks_passed":sum(checks.values()),"checks_total":len(checks),"checks":checks,"failed_checks":failed,"pair_rows_validated":15 if not failed else 0,"current_pairs":14 if not failed else 0,"stale_pairs":1 if not failed else 0,"polygon_relation_claimed":False,"business_progress_claimed":False,"actual_business_data_rows_written":0,"final_ready":False}


def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("manifest",type=Path); p.add_argument("candidate_json",type=Path); p.add_argument("--output",type=Path); a=p.parse_args()
    try: result=validate(read(a.manifest),read(a.candidate_json))
    except Exception as exc: result={"schema_version":1,"slot_id":SLOT_ID,"validation_kind":"REVISION8_EXACT_RELATION_PAIR_INPUT_CONTRACT","result":"FAIL","checks_passed":0,"checks_total":1,"checks":{"json_load":False},"failed_checks":[f"{type(exc).__name__}:{exc}"],"polygon_relation_claimed":False,"business_progress_claimed":False,"actual_business_data_rows_written":0,"final_ready":False}
    text=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
    if a.output: a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(text,encoding="utf-8")
    else: sys.stdout.write(text)
    return 0 if result["result"]=="PASS" else 2


if __name__=="__main__": raise SystemExit(main())
