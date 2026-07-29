from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()
SOURCE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_wave32_accept_publish.py"

if not SOURCE.is_file():
    raise SystemExit(f"SOURCE_SCRIPT_MISSING: {SOURCE}")

text = SOURCE.read_text(encoding="utf-8")
replacements = [
    ("0007_security_public_safety_2_priority_590row_incremental_evidence_expansion_20260729.v3.task.json", "0021_security_public_safety_2_priority_2620row_incremental_evidence_expansion_20260730.v3.task.json"),
    ("2462ad1cf05576bed958c18cc4a01d7cde54d2c566f5a480c235066eb48012ae", "782cce1b0b9da6131c5d7179996badd7be23eee2322bf036ab9ee541dba713ef"),
    ("github-actions-security-public-safety-2-wave32", "github-actions-security-public-safety-2-wave46"),
    ("wave32", "wave46"),
    ("590", "2620"),
    ("range(30762, 31352)", "range(30762, 33382)"),
    ("parcel_31351", "parcel_33381"),
    ("MIN_QUALITY = 561", "MIN_QUALITY = 2489"),
    ('"progress_delta_percentage_points": 11.86', '"progress_delta_percentage_points": 8.02'),
    ('"accepted_base_candidate_rows": 520', '"accepted_base_candidate_rows": 2410'),
    ('"incremental_rows_target": 70', '"incremental_rows_target": 210'),
    ('"incremental_rows_completed": 70', '"incremental_rows_completed": 210'),
    ("priority_2620row_browser_acceptance_wave46_receipt_20260729.json", "priority_2620row_browser_acceptance_wave46_receipt_20260730.json"),
    ("priority_2620row_targeted_retry_wave46_diagnostic_20260729.json", "priority_2620row_targeted_retry_wave46_diagnostic_20260730.json"),
]

for old, new in replacements[:4]:
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

if "590" not in text:
    raise SystemExit("EXPECTED_590_TARGET_FRAGMENTS_MISSING")
text = text.replace("590", "2620")

for old, new in replacements[5:]:
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)
