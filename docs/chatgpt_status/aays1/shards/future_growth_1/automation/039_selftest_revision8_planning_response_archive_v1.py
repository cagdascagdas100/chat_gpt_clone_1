#!/usr/bin/env python3
"""Offline fixtures for revision-8 Planning Data response archive validator."""
from __future__ import annotations
import hashlib, importlib.util, json, tempfile
from pathlib import Path
from urllib.parse import urlencode

HERE=Path(__file__).resolve().parent
TARGET=HERE/"038_validate_revision8_planning_response_archive_v1.py"
spec=importlib.util.spec_from_file_location("validator",TARGET)
mod=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(mod)

def sha(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def url(i:int)->str:
    pairs=[("latitude",f"51.{530000+i}"),("longitude",f"0.{70000+i}"),("period","current"),("limit","100")]
    for d in sorted(mod.ALLOWED_DATASETS): pairs.append(("dataset",d))
    for f in sorted(mod.REQUIRED_FIELDS): pairs.append(("field",f))
    return "https://www.planning.data.gov.uk/entity.json?"+urlencode(pairs)

def build(root:Path):
    outdir=root/mod.OUTPUT_DIR_SUFFIX; outdir.mkdir(parents=True,exist_ok=True)
    manifest_rows=[]; evidence_rows=[]; total_entities=0
    for i in range(1,20):
        request=url(i)
        manifest_rows.append({"row_no":i,"parcel_id":f"parcel_{i}","hmlr_inspire_id":f"id-{i}","request_url":request})
        entities=[] if i%3==0 else [{"entity":1000+i,"dataset":"brownfield-land","reference":f"R{i}","name":f"N{i}","start-date":"2020-01-01","end-date":"","geometry":"","point":f"POINT (0.{i} 51.{i})","quality":"authoritative"}]
        body=json.dumps({"entities":entities},sort_keys=True).encode()
        path=outdir/f"row_{i:05d}.json"; path.write_bytes(body)
        evidence_rows.append({"row_no":i,"request_url":request,"response_path":str(path),"response_sha256":hashlib.sha256(body).hexdigest(),"entity_count":len(entities),"zero_result_semantics":"NO_DATA_COVERAGE_NOT_PROOF" if not entities else None,"promotion_eligible":False,"score":None})
        total_entities+=len(entities)
    manifest={"slot_id":mod.SLOT_ID,"rows":manifest_rows}
    mpath=root/"england_map_web/data/aays_21_slots/future_growth_1/planning_constraint_query_manifest_rows_1_19_latest.json"
    mpath.parent.mkdir(parents=True,exist_ok=True); mpath.write_text(json.dumps(manifest,sort_keys=True),encoding="utf-8")
    evidence={"schema_version":1,"slot_id":mod.SLOT_ID,"manifest_sha256":sha(mpath),"request_count":19,"dataset_screens":133,"dry_run":False,"network_requests_executed":19,"rows_completed":19,"entities_read":total_entities,"rows":evidence_rows,"promotion_eligible_rows":0,"scores_emitted":0,"final_ready":False}
    epath=outdir/"execution_evidence_manifest.json"; epath.write_text(json.dumps(evidence,sort_keys=True),encoding="utf-8")
    qv={"slot_id":mod.SLOT_ID,"result":"PASS","rows_validated":19,"polygon_relation_claimed":False}
    qvpath=root/mod.QUERY_VALIDATION_REL; qvpath.parent.mkdir(parents=True,exist_ok=True); qvpath.write_text(json.dumps(qv,sort_keys=True),encoding="utf-8")
    queue={"slot_id":mod.SLOT_ID,"task_id":mod.TASK_ID,"attempt_id":mod.ATTEMPT_ID,"contract_revision":8,"planning_query_manifest_path":str(mpath.relative_to(root))}
    runner={"slot_id":mod.SLOT_ID,"workstream_id":mod.WORKSTREAM_ID,"task_id":mod.TASK_ID,"attempt_id":mod.ATTEMPT_ID,"contract_revision":8,"state":"COMPLETED_SLOT_LOCAL_GEOMETRY_AND_PLANNING_QUERY_SAMPLE","planning_query_evidence":evidence,"source_sha256":{"query_evidence":sha(epath),"query_validation":sha(qvpath)},"actual_business_data_rows_written":0,"fake_data":False,"db_write":False,"migration":False,"production_deploy":False,"final_ready":False}
    return queue,runner

def run_case(name,mutate,expected):
    with tempfile.TemporaryDirectory() as td:
        root=Path(td); q,r=build(root); mutate(root,q,r)
        actual=mod.validate(root,q,r)["result"]
        return {"name":name,"expected":expected,"actual":actual,"pass":actual==expected}

def main():
    def response(root,r,i): return root/mod.OUTPUT_DIR_SUFFIX/f"row_{i:05d}.json"
    cases=[
      run_case("exact_archive",lambda root,q,r:None,"PASS"),
      run_case("missing_response",lambda root,q,r:response(root,r,1).unlink(),"FAIL"),
      run_case("sha_mismatch",lambda root,q,r:r["planning_query_evidence"]["rows"][0].__setitem__("response_sha256","0"*64),"FAIL"),
      run_case("entity_count_mismatch",lambda root,q,r:r["planning_query_evidence"]["rows"][0].__setitem__("entity_count",99),"FAIL"),
      run_case("duplicate_entity",lambda root,q,r:response(root,r,1).write_text(json.dumps({"entities":[{"entity":1,"dataset":"brownfield-land","reference":"x","name":"x","start-date":"","end-date":"","geometry":"","point":"","quality":"authoritative"},{"entity":1,"dataset":"brownfield-land","reference":"y","name":"y","start-date":"","end-date":"","geometry":"","point":"","quality":"authoritative"}]},sort_keys=True),encoding="utf-8"),"FAIL"),
      run_case("historical_entity",lambda root,q,r:response(root,r,1).write_text(json.dumps({"entities":[{"entity":1,"dataset":"brownfield-land","reference":"x","name":"x","start-date":"","end-date":"2020-01-01","geometry":"","point":"","quality":"authoritative"}]},sort_keys=True),encoding="utf-8"),"FAIL"),
      run_case("missing_required_field",lambda root,q,r:response(root,r,1).write_text(json.dumps({"entities":[{"entity":1,"dataset":"brownfield-land"}]},sort_keys=True),encoding="utf-8"),"FAIL"),
      run_case("wrong_dataset",lambda root,q,r:response(root,r,1).write_text(json.dumps({"entities":[{"entity":1,"dataset":"not-allowed","reference":"x","name":"x","start-date":"","end-date":"","geometry":"","point":"","quality":"authoritative"}]},sort_keys=True),encoding="utf-8"),"FAIL"),
      run_case("wrong_response_name",lambda root,q,r:r["planning_query_evidence"]["rows"][0].__setitem__("response_path",str(response(root,r,2))),"FAIL"),
      run_case("duplicate_response_path",lambda root,q,r:r["planning_query_evidence"]["rows"][1].__setitem__("response_path",r["planning_query_evidence"]["rows"][0]["response_path"]),"FAIL"),
      run_case("request_mismatch",lambda root,q,r:r["planning_query_evidence"]["rows"][0].__setitem__("request_url",url(19)),"FAIL"),
      run_case("manifest_sha_mismatch",lambda root,q,r:r["planning_query_evidence"].__setitem__("manifest_sha256","0"*64),"FAIL"),
      run_case("evidence_manifest_mismatch",lambda root,q,r:r["planning_query_evidence"].__setitem__("entities_read",999),"FAIL"),
      run_case("query_validation_sha_mismatch",lambda root,q,r:r["source_sha256"].__setitem__("query_validation","0"*64),"FAIL"),
      run_case("business_claim",lambda root,q,r:r.__setitem__("actual_business_data_rows_written",1),"FAIL"),
      run_case("cross_slot_path",lambda root,q,r:r["planning_query_evidence"]["rows"][0].__setitem__("response_path",str(root/"docs/chatgpt_status/aays1/shards/future_growth_2/x.json")),"FAIL"),
    ]
    passed=sum(c["pass"] for c in cases)
    out={"schema_version":1,"slot_id":mod.SLOT_ID,"selftest_kind":"REVISION8_PLANNING_RESPONSE_ARCHIVE","result":f"{passed}/{len(cases)} PASS","passed":passed,"total":len(cases),"cases":cases,"runner_execution_claimed":False,"business_progress_claimed":False,"final_ready":False}
    print(json.dumps(out,ensure_ascii=False,indent=2)); return 0 if passed==len(cases) else 2
if __name__=="__main__": raise SystemExit(main())
