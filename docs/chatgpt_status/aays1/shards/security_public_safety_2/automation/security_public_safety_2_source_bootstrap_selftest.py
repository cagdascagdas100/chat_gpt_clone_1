from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT / "security_public_safety_2_official_source_bootstrap.py"
spec = importlib.util.spec_from_file_location("bootstrap", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

cases = []

def record(name, value):
    cases.append({"name": name, "pass": bool(value)})

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    iod = tmp / "File_7_IoD2025_All_Ranks_Scores_Deciles_Population_Denominators_v2.csv"
    with iod.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["LSOA code (2021)", "Crime Score", "Crime Rank (where 1 is most deprived)", "Crime Decile (where 1 is most deprived 10% of LSOAs)"])
        writer.writeheader()
        writer.writerow({"LSOA code (2021)": "E01000001", "Crime Score": "0.2", "Crime Rank (where 1 is most deprived)": "1", "Crime Decile (where 1 is most deprived 10% of LSOAs)": "1"})
    iod_check = mod.inspect_csv(iod, "iod25_file7_v2")
    record("iod_good_pass", iod_check["pass"])
    record("iod_sha_present", bool(iod_check["sha256"]))
    record("iod_rows_sampled", iod_check["rows_sampled"] == 1)
    record("iod_no_failures", not iod_check["failures"])

    iod_bad = tmp / "bad.csv"
    iod_bad.write_text("LSOA code (2021),Crime Score\nE01000001,0.2\n", encoding="utf-8")
    iod_bad_check = mod.inspect_csv(iod_bad, "iod25_file7_v2")
    record("iod_bad_rejected", not iod_bad_check["pass"])
    record("iod_bad_rank_missing", "MISSING_RANK_HEADER" in iod_bad_check["failures"])
    record("iod_bad_decile_missing", "MISSING_DECILE_HEADER" in iod_bad_check["failures"])

    mps = tmp / "MPS_LSOA_Level_Crime_latest.csv"
    mps.write_text("LSOA Code,2026-05,2026-06\nE01000001,2,3\n", encoding="utf-8")
    mps_check = mod.inspect_csv(mps, "mps_lsoa")
    record("mps_good_pass", mps_check["pass"])
    record("mps_sha_present", bool(mps_check["sha256"]))
    record("mps_rows_sampled", mps_check["rows_sampled"] == 1)

    mps_bad = tmp / "mps_bad.csv"
    mps_bad.write_text("LSOA Code,Name\nE01000001,A\n", encoding="utf-8")
    mps_bad_check = mod.inspect_csv(mps_bad, "mps_lsoa")
    record("mps_bad_rejected", not mps_bad_check["pass"])
    record("mps_bad_count_missing", "MISSING_MONTH_OR_COUNT_HEADER" in mps_bad_check["failures"])

    page = '''<script>{"name":"MPS LSOA Level Crime.csv","download_url":"https:\\/\\/example.gov.uk\\/MPS_LSOA_Level_Crime_Jul_2024_Jun_2026.csv"}</script>
    <a href="/older/MPS_LSOA_Level_Crime_Jun_2024_May_2026.csv">MPS LSOA Level Crime.csv</a>'''
    discovery = mod.discover_mps_lsoa_url(page, "https://data.london.gov.uk/dataset/x/")
    record("discovery_pass", discovery["pass"])
    record("discovery_two_candidates", len(discovery["candidates"]) == 2)
    record("discovery_lsoa_filter", all("lsoa" in value.lower() for value in discovery["candidates"]))
    record("discovery_csv_filter", all(".csv" in value.lower() for value in discovery["candidates"]))
    record("discovery_prefers_2026", "2026" in discovery["selected_url"])

    materialized = mod.materialize_source(source="iod25_file7_v2", explicit_path=str(iod), explicit_url=None, default_url=None, output_path=tmp / "unused.csv", timeout=1)
    record("explicit_path_reused", materialized["pass"] and materialized["method"] == "explicit_path")
    record("explicit_path_exact", materialized["path"] == str(iod))
    unknown = mod.inspect_csv(iod, "unknown")
    record("unknown_source_rejected", not unknown["pass"])
    record("slot_constant_exact", mod.SLOT_ID == "security_public_safety_2")
    record("branch_constant_exact", mod.TARGET_BRANCH == "codex/aays-single-runner-v5-20260706")
    record("iod_official_https", mod.IOD25_FILE7_V2_URL.startswith("https://assets.publishing.service.gov.uk/"))
    record("mps_official_https", mod.MPS_DATASET_PAGE.startswith("https://data.london.gov.uk/"))

passed = sum(case["pass"] for case in cases)
payload = {"schema_version": 1, "slot_id": "security_public_safety_2", "test_type": "OFFICIAL_SOURCE_BOOTSTRAP_FAIL_CLOSED_SELFTEST", "cases": cases, "passed": passed, "total": len(cases), "pass": passed == len(cases), "actual_business_rows_written": 0, "fake_data": False, "final_ready": False}
print(json.dumps(payload, ensure_ascii=False, indent=2))
raise SystemExit(0 if payload["pass"] else 1)
