from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path.cwd()
SOURCE_REL = "docs/chatgpt_status/aays1/automation/security_public_safety_2_geometry_lsoa_police_sample_wave1_retry5_candidate_join_20260723.py"
SOURCE_PATH = ROOT / SOURCE_REL
EXPECTED_SOURCE_BLOB = "3e9a4d57754e13d68429cedfb0a0b271fda822eb"


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def replace_exact(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"CANDIDATE_V2_PATCH_{label}_COUNT={count}")
    return text.replace(old, new, 1)


if not SOURCE_PATH.is_file():
    raise SystemExit(f"CANDIDATE_V1_ENTRY_MISSING={SOURCE_REL}")
actual_blob = git_blob_sha(SOURCE_PATH)
if actual_blob != EXPECTED_SOURCE_BLOB:
    raise SystemExit(f"CANDIDATE_V1_ENTRY_BLOB_MISMATCH={actual_blob}")

code = SOURCE_PATH.read_text(encoding="utf-8")
code = replace_exact(
    code,
    '''join_block = \'\'\'id_continuity_pass = set(target_features) == set(TARGET_IDS)
feature_count_pass = actual_feature_count == 92283

for row in rows:''',
    '''join_block = \'\'\'id_continuity_pass = set(target_features) == set(TARGET_IDS)
feature_count_pass = actual_feature_count == 92283
iod25_expected_final_url = IOD_FILE7_URL.rstrip("/")
iod25_current_v2_url_match = str(iod_download.get("final_url") or "").rstrip("/") == iod25_expected_final_url
iod_download["current_v2_url_match"] = iod25_current_v2_url_match
iod_download["expected_current_v2_url"] = IOD_FILE7_URL

for row in rows:''',
    "URL_IDENTITY",
)
code = replace_exact(
    code,
    '''        and iod_download.get("reachable")
        and iod_download.get("sha256")
        and method_preregistered''',
    '''        and iod_download.get("reachable")
        and iod_download.get("sha256")
        and iod25_current_v2_url_match
        and method_preregistered''',
    "JOIN_READY_URL",
)
code = replace_exact(
    code,
    '''    candidate_integrity = 0
    candidate_integrity += 25 if id_continuity_pass else 0
    candidate_integrity += 20 if row.get("geometry_type") == "Point" and row.get("longitude") is not None else 0
    candidate_integrity += 25 if (row.get("ons_query") or {}).get("feature_count") == 1 else 0
    candidate_integrity += 20 if iod_row and iod_schema.get("schema_gate_pass") and iod_download.get("sha256") else 0
    candidate_integrity += 10 if method_preregistered else 0''',
    '''    candidate_integrity = 0
    candidate_integrity += 15 if id_continuity_pass else 0
    candidate_integrity += 15 if source_blob == "bb48164e7a0af78df875f30421a6a3068c43edb8" and feature_count_pass else 0
    candidate_integrity += 20 if row.get("geometry_type") == "Point" and row.get("longitude") is not None else 0
    candidate_integrity += 20 if (row.get("ons_query") or {}).get("feature_count") == 1 else 0
    candidate_integrity += 20 if iod_row and iod_schema.get("schema_gate_pass") and iod_download.get("sha256") and iod25_current_v2_url_match else 0
    candidate_integrity += 10 if method_preregistered else 0''',
    "INTEGRITY_FORMULA",
)
code = replace_exact(
    code,
    '''accuracy_ge_95_candidate_rows = sum(int(item.get("candidate_evidence_integrity_percent") or 0) >= 95 for item in rows)''',
    '''accuracy_ge_95_candidate_rows = sum(
    item.get("candidate_value") is not None
    and int(item.get("candidate_evidence_integrity_percent") or 0) >= 95
    for item in rows
)''',
    "HIGH_CONFIDENCE_COUNT",
)
namespace = {"__name__": "__main__", "__file__": str(SOURCE_PATH), "__package__": None}
exec(compile(code, str(SOURCE_PATH), "exec"), namespace, namespace)
