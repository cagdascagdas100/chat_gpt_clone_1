from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()
SOURCE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_wave33_accept_publish.py"

if not SOURCE.is_file():
    raise SystemExit(f"SOURCE_SCRIPT_MISSING: {SOURCE}")

text = SOURCE.read_text(encoding="utf-8")
replacements = [
    ("0008_security_public_safety_2_priority_670row_incremental_evidence_expansion_20260729.v3.task.json", "0009_security_public_safety_2_priority_760row_incremental_evidence_expansion_20260729.v3.task.json"),
    ("c08dea96cbbf1bac2cc47fc5442ba9c6e8a62844bd718b1fa41b5c04bffdc9bf", "ed5b25961f01d25aa1b94a3e5339d7a1a6203d60029fbf0db4bc9cc56d12c565"),
    ("github-actions-security-public-safety-2-wave33", "github-actions-security-public-safety-2-wave34"),
    ("wave33", "wave34"),
    ("670", "760"),
    ("range(30762, 31432)", "range(30762, 31522)"),
    ("parcel_31431", "parcel_31521"),
    ("MIN_QUALITY = 637", "MIN_QUALITY = 722"),
    ('"progress_delta_percentage_points": 11.94', '"progress_delta_percentage_points": 11.84'),
    ('"accepted_base_candidate_rows": 590', '"accepted_base_candidate_rows": 670'),
    ('"incremental_rows_target": 80', '"incremental_rows_target": 90'),
    ('"incremental_rows_completed": 80', '"incremental_rows_completed": 90'),
]

for old, new in replacements[:4]:
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

if "670" not in text:
    raise SystemExit("EXPECTED_670_TARGET_FRAGMENTS_MISSING")
text = text.replace("670", "760")

for old, new in replacements[5:]:
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)
