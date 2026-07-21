#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
def load(path): return json.loads(path.read_text(encoding="utf-8"))
def main():
    p=argparse.ArgumentParser();p.add_argument("--repo-root",required=True,type=Path);a=p.parse_args();r=a.repo_root
    shard=r/"docs/chatgpt_status/internet_access_parcel_layer_low_credit_20260612/shards/internet_access_3"
    web=r/"england_map_web/data/aays_18_slots/internet_access_3"
    progress=load(web/"progress_latest.json");ops=load(web/"operations_latest.json");examples=load(web/"examples_latest.json");rep=load(web/"runtime_reproducibility_latest.json");runner=load(web/"runner_task_latest.json");task=load(shard/"runner_tasks/001_ofcom_r2_bounded_join.task.json");research=load(shard/"research/013_ofcom_methodology_qa_20260721.json");validation=load(shard/"validation/013_runtime_reproducibility_local_validation_20260721.json");html=(web/"index.html").read_text(encoding="utf-8");http=(shard/"automation/025_http_8012_acceptance.py").read_text(encoding="utf-8")
    rows=ops["operations"]
    checks=[
    ("slot_progress",progress["slot_id"]=="internet_access_3"),
    ("progress_percent",progress["overall_progress_percent"]==77.08),
    ("progress_delta",progress["progress_delta_percent"]==0.52),
    ("ops_counts",(progress["completed_operations"],progress["partial_operations"],progress["total_operations"])==(7,4,12)),
    ("test_total",progress["extractor_selftest_passed"]==progress["extractor_selftest_total"]==351),
    ("compile_total",progress["python_compile_passed"]==progress["python_compile_total"]==21),
    ("qa_count",progress["official_aggregate_qa_examples"]==16),
    ("product_zero",progress["verified_product_rows"]==0 and progress["actual_business_data_rows_written"]==0),
    ("ops_rows",len(rows)==12),
    ("ops_sequence",[x["operation_no"] for x in rows]==list(range(1,13))),
    ("ops_weight",abs(sum(float(x["progress_weight"]) for x in rows)-9.25)<1e-9),
    ("op10_repro",rows[9]["progress_weight"]==0.1875 and "040" in rows[9]["evidence"]),
    ("examples_count",examples["example_count"]==len(examples["examples"])==21),
    ("official_examples",examples["official_aggregate_qa_examples"]==16),
    ("examples_no_product",examples["verified_product_example_rows"]==0 and examples["actual_business_data_rows_written"]==0),
    ("provider_example",examples["examples"][-2]["example_no"]==20 and "52 fixed" in examples["examples"][-2]["condition"]),
    ("confidence_example",examples["examples"][-1]["example_no"]==21 and "funding is committed" in examples["examples"][-1]["condition"]),
    ("research_sources",research["source_count"]==research["promoted_for_qa_count"]==2),
    ("research_confidence",research["source_confidence_ge_95_count"]==2 and all(x["source_confidence_score"]>=95 for x in research["sources"])),
    ("repro_waiting",rep["status"]=="WAITING_TWO_REAL_VALIDATED_RUNTIME_RECEIPTS" and rep["real_validated_receipts_available"]==0 and rep["required_receipts"]==2),
    ("repro_no_auto",rep["automatic_acceptance"] is False and rep["exact_reproducibility_pass"] is False),
    ("repro_gates",len(rep["gates"])==6 and [x["gate_no"] for x in rep["gates"]]==list(range(1,7))),
    ("runner_stages",len(runner["stages"])==33),
    ("runner_validation",runner["local_validation_passed"]==runner["local_validation_total"]==351),
    ("runner_compile",runner["python_compile_passed"]==runner["python_compile_total"]==21),
    ("runner_no_claim",runner["auto_claim"] is False and runner["queue_submission"] is False and runner["create_new_runner"] is False),
    ("task_repro_command","040_runtime_reproducibility_gate.py" in task["reproducibility_command"]),
    ("task_two_receipts","runtime_gate_baseline" in task["output_contract"] and "runtime_gate_candidate" in task["output_contract"]),
    ("index_visibility",'id="reproducibility"' in html and "runtime_reproducibility_latest.json" in html and "rep.gates.forEach" in html),
    ("http_required","runtime_reproducibility_latest.json" in http and 'id="reproducibility"' in http),
    ("validation_totals",validation["cumulative_tests_passed"]==validation["cumulative_tests_total"]==351),
    ("truth_flags",all(doc.get(k) is False for doc in (progress,ops,examples,rep,runner,task,research,validation) for k in ("final_ready",)) and all(doc.get("actual_business_data_rows_written",0)==0 for doc in (progress,ops,examples,rep,runner,research,validation)))
    ]
    for name,ok in checks: print("PASS" if ok else "FAIL",name)
    print(json.dumps({"passed":sum(ok for _,ok in checks),"total":len(checks)}))
    return 0 if all(ok for _,ok in checks) else 1
if __name__=="__main__": raise SystemExit(main())
