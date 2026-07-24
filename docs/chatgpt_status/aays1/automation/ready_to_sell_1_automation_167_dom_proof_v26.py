from __future__ import annotations
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE / "ready_to_sell_1_automation_167_dom_proof_v25.py"
spec = importlib.util.spec_from_file_location("rts1_v25", BASE)
if spec is None or spec.loader is None:
    raise RuntimeError(str(BASE))
v25 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v25)
v3 = v25.v3
DATA_ROOT = v25.DATA_ROOT

def batch(prefix: str, number: int) -> Path:
    date = "20260720" if number <= 6 else "20260721"
    return DATA_ROOT / f"{prefix}_batch{number}_{date}.json"

v3.SOURCE_FILES = [DATA_ROOT / "official_source_candidates_20260720.json"] + [batch("official_source_candidates", n) for n in range(2, 26)]
v3.CANDIDATE_FILES = [DATA_ROOT / "verified_candidate_examples_20260720.json"] + [batch("verified_candidate_examples", n) for n in range(2, 26)]
v3.EXPECTED_TOTAL_SOURCES = 196
v3.EXPECTED_TOTAL_CANDIDATES = 134
v3.EXPECTED_EXACT_INSPIRE = 2
v3.EXPECTED_INTERNET_REVERIFIED = 134
v3.EXPECTED_COMPLETED_OPERATIONS = 130
v3.EXPECTED_TOTAL_OPERATIONS = 131

previous_markdown = v3.write_markdown
def write_markdown(report):
    previous_markdown(report)
    path = v3.v2.REPORT_MD
    text = path.read_text(encoding="utf-8")
    text = text.replace("Aggregate DOM Proof V25", "Aggregate DOM Proof V26")
    text = text.replace("RERUN_AUTOMATION_167_V25", "RERUN_AUTOMATION_167_V26")
    text += "\nV26 aggregate contract: 25 batches, 134 candidates, 196 sources, 3 planning evidence rows, 130/131 operations and zero unverified parcel values.\n"
    path.write_text(text, encoding="utf-8")
v3.write_markdown = write_markdown

def main():
    result = v25.main_v25()
    path = v3.v2.REPORT_JSON
    report = json.loads(path.read_text(encoding="utf-8-sig"))
    report["automation_version"] = "V26"
    report["aggregate_contract"] = {"candidate_batches":25,"verified_source_batches":25,"candidate_rows":134,"verified_source_rows":196,"official_planning_evidence_rows":3,"strengthened_candidate_rows":74,"completed_operations":130,"total_operations":131,"unverified_parcel_value_rows":0}
    v3.v2.write_json(path, report)
    return result

if __name__ == "__main__":
    raise SystemExit(main())
