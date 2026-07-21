from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGET = HERE / "security_public_safety_2_official_source_bootstrap_v2.py"
spec = importlib.util.spec_from_file_location("bootstrap_v2", TARGET)
assert spec and spec.loader
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

cases: list[dict[str, object]] = []

class FakeBaseNoDirect:
    @staticmethod
    def discover_mps_lsoa_url(page_text, base_url):
        return {"pass": False, "selected_url": None, "candidates": []}

class FakeBaseDirect:
    @staticmethod
    def discover_mps_lsoa_url(page_text, base_url):
        return {"pass": True, "selected_url": "https://files.example.org/MPS_LSOA_Level_Crime.csv", "candidates": ["https://files.example.org/MPS_LSOA_Level_Crime.csv"]}
def check(name: str, value: bool) -> None:
    cases.append({"name": name, "pass": bool(value)})

check("exact_slot", m.SLOT_ID == "security_public_safety_2")
check("exact_branch", m.TARGET_BRANCH == "codex/aays-single-runner-v5-20260706")
check("police_official_https", m.validate_public_https_url(m.POLICE_LATEST_URL)["pass"])
check("mps_official_https", m.validate_public_https_url(m.MPS_DATASET_PAGE)["pass"])
check("reject_http", not m.validate_public_https_url("http://data.london.gov.uk/a.csv")["pass"])
check("reject_localhost", not m.validate_public_https_url("https://localhost/a.csv")["pass"])
check("reject_ipv4_loopback", not m.validate_public_https_url("https://127.0.0.1/a.csv")["pass"])
check("reject_ipv4_private", not m.validate_public_https_url("https://10.0.0.1/a.csv")["pass"])
check("reject_ipv6_loopback", not m.validate_public_https_url("https://[::1]/a.csv")["pass"])
check("reject_credentials", not m.validate_public_https_url("https://user:pw@data.london.gov.uk/a.csv")["pass"])
check("accept_public_https", m.validate_public_https_url("https://files.example.org/a.csv")["pass"])

resource_a = "https://data.london.gov.uk/dataset/x/resource/11111111-1111-1111-1111-111111111111"
resource_b = "https://data.london.gov.uk/dataset/x/resource/22222222-2222-2222-2222-222222222222"
dataset_html = f'<a href="{resource_a}">old</a><a href="{resource_b}">new</a>'
resources = m.extract_resource_page_urls(dataset_html)
check("resource_two", len(resources) == 2)
check("resource_order", resources == [resource_a, resource_b])
check("resource_public", all(m.validate_public_https_url(v)["pass"] for v in resources))

old_page = '<h1>MPS LSOA Level Crime.csv</h1><p>Jul 2024 – May 2026</p><a href="https://files.example.org/MPS_LSOA_Level_Crime_May_2026.csv">Download</a>'
new_page = '<h1>MPS LSOA Level Crime.csv</h1><p>Jul 2024 – Jun 2026</p><a href="https://files.example.org/MPS_LSOA_Level_Crime_Jun_2026.csv">Download</a>'
historical_page = '<h1>MPS LSOA Level Crime (Historical).csv</h1><p>Mar 2019 – Jun 2024</p><a href="https://files.example.org/historical.csv">Download</a>'
parsed_old = m.parse_resource_page(resource_a, old_page)
parsed_new = m.parse_resource_page(resource_b, new_page)
parsed_historical = m.parse_resource_page(resource_a, historical_page)
check("parse_old_title", parsed_old["title"] == "MPS LSOA Level Crime.csv")
check("parse_old_period", parsed_old["period_end"] == "2026-05-31")
check("parse_new_period", parsed_new["period_end"] == "2026-06-30")
check("parse_download", str(parsed_new["selected_url"]).endswith("Jun_2026.csv"))
check("historical_rejected", not parsed_historical["pass"])

pages = {resource_a: old_page.encode(), resource_b: new_page.encode()}
def fetcher(url: str):
    return pages[url], {"http_status": 200, "final_url": url}

m.load_base = lambda: FakeBaseNoDirect
discovery = m.discover_mps_lsoa_url_v2(dataset_html, fetcher=fetcher)
check("fallback_pass", discovery["pass"])
check("fallback_method", discovery["method"] == "OFFICIAL_RESOURCE_PAGE_FALLBACK")
check("fallback_newest", str(discovery["selected_url"]).endswith("Jun_2026.csv"))
check("fallback_period", discovery["period_end"] == "2026-06-30")
check("fallback_resource_count", len(discovery["resource_results"]) == 2)
m.load_base = lambda: FakeBaseDirect
direct = m.discover_mps_lsoa_url_v2("ignored", fetcher=fetcher)
check("direct_pass", direct["pass"])
check("direct_method", direct["method"] == "DIRECT_CSV_ON_OFFICIAL_DATASET_PAGE")
check("direct_url", str(direct["selected_url"]).endswith("MPS_LSOA_Level_Crime.csv"))

police_good = m.parse_police_latest(b'{"date":"2026-05-01"}')
police_bad = m.parse_police_latest(b'{"date":"2026-99-01"}')
police_invalid = m.parse_police_latest(b'not-json')
check("police_good", police_good["pass"])
check("police_date", police_good["date"] == "2026-05-01")
check("police_bad_rejected", not police_bad["pass"])
check("police_invalid_rejected", not police_invalid["pass"])
check("minimum_mps_period", m.MIN_MPS_PERIOD_END == "2026-06-30")

result = {
    "schema_version": 1,
    "slot_id": m.SLOT_ID,
    "test_type": "SOURCE_BOOTSTRAP_V2_PROVENANCE_SELFTEST",
    "cases": cases,
    "passed": sum(1 for case in cases if case["pass"]),
    "total": len(cases),
    "pass": all(case["pass"] for case in cases),
    "actual_business_rows_written": 0,
    "fake_data": False,
    "final_ready": False,
}
print(json.dumps(result, ensure_ascii=False, indent=2))
raise SystemExit(0 if result["pass"] else 1)
