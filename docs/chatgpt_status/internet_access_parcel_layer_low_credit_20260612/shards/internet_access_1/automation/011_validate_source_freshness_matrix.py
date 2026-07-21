#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

REQUIRED_CENTROID_FIELDS = {"PCDS", "LAT", "LONG", "LAD25CD"}

def validate(payload: dict) -> dict:
    sources = payload.get("sources")
    checks = []
    def check(name, condition):
        checks.append({"name": name, "pass": bool(condition)})
    check("slot_id", payload.get("slot_id") == "internet_access_1")
    check("eight_sources", isinstance(sources, list) and len(sources) == 8)
    if not isinstance(sources, list):
        sources = []
    check("all_source_types_guarded", all(s.get("source_type") in {"official", "official_derivative"} for s in sources))
    check("all_confidence_ge_90", all(int(s.get("confidence_percent", 0)) >= 90 for s in sources))
    value_sources = [s for s in sources if s.get("broadband_value_allowed")]
    check("single_broadband_value_source", len(value_sources) == 1)
    check("value_source_is_ofcom_release", len(value_sources) == 1 and value_sources[0].get("name") == "Ofcom Connected Nations Spring 2026")
    check("ofcom_requires_r2", len(value_sources) == 1 and value_sources[0].get("requires_corrected_r2_row") is True)
    check("non_value_sources_blocked", all(s.get("broadband_value_allowed") is False for s in sources if s not in value_sources))
    centroid = next((s for s in sources if s.get("name") == "ONSPD Online latest Postcode Centroids"), {})
    check("centroid_fields_present", REQUIRED_CENTROID_FIELDS.issubset(set(centroid.get("required_fields", []))))
    check("centroid_period_may_2026", centroid.get("dataset_period") == "2026-05")
    nhspd = next((s for s in sources if s.get("name") == "NHS Postcode Directory May 2026"), {})
    check("nhspd_quarterly", nhspd.get("release_frequency") == "quarterly")
    check("nhspd_no_broadband", nhspd.get("broadband_value_allowed") is False)
    check("direct_rows_zero", sum(int(s.get("direct_rows_read", 0)) for s in sources) == 0)
    check("accuracy_upgrade_zero", payload.get("summary", {}).get("internet_accuracy_upgraded_rows") == 0)
    check("business_rows_zero", payload.get("summary", {}).get("business_rows_written") == 0)
    check("final_ready_false", payload.get("final_ready") is False)
    passed = sum(c["pass"] for c in checks)
    return {"schema_version":1,"slot_id":"internet_access_1","status":"PASS" if passed == len(checks) else "FAIL","checks_passed":passed,"checks_failed":len(checks)-passed,"checks_total":len(checks),"checks":checks,"business_rows_written":0,"fake_data":False,"final_ready":False}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--input',type=Path,required=True); p.add_argument('--output',type=Path,required=True); a=p.parse_args()
    out=validate(json.loads(a.input.read_text(encoding='utf-8')))
    a.output.write_text(json.dumps(out,indent=2)+"\n",encoding='utf-8')
    print(json.dumps({k:out[k] for k in ('status','checks_passed','checks_failed','checks_total')}))
    raise SystemExit(0 if out['status']=='PASS' else 1)
if __name__=='__main__': main()
