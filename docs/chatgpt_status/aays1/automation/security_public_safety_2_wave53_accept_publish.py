from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()
SOURCE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_wave32_accept_publish.py"

if not SOURCE.is_file():
    raise SystemExit(f"SOURCE_SCRIPT_MISSING: {SOURCE}")

text = SOURCE.read_text(encoding="utf-8")
replacements = [
    ("0007_security_public_safety_2_priority_590row_incremental_evidence_expansion_20260729.v3.task.json", "0028_security_public_safety_2_priority_4370row_incremental_evidence_expansion_20260730.v3.task.json"),
    ("2462ad1cf05576bed958c18cc4a01d7cde54d2c566f5a480c235066eb48012ae", "039acbc2259f7715359cf1f7f2438983e0498abd7ca929f8bc9ad6c34367b40c"),
    ("github-actions-security-public-safety-2-wave32", "github-actions-security-public-safety-2-wave53"),
    ("wave32", "wave53"),
    ("590", "4370"),
    ("range(30762, 31352)", "range(30762, 35132)"),
    ("parcel_31351", "parcel_35131"),
    ("MIN_QUALITY = 561", "MIN_QUALITY = 4152"),
    ('"progress_delta_percentage_points": 11.86', '"progress_delta_percentage_points": 6.41'),
    ('"accepted_base_candidate_rows": 520', '"accepted_base_candidate_rows": 4090'),
    ('"incremental_rows_target": 70', '"incremental_rows_target": 280'),
    ('"incremental_rows_completed": 70', '"incremental_rows_completed": 280'),
    ("security_public_safety_2_priority_4370row_incremental_evidence_expansion_20260729", "security_public_safety_2_priority_4370row_incremental_evidence_expansion_20260730"),
    ("priority_4370row_browser_acceptance_wave53_receipt_20260729.json", "priority_4370row_browser_acceptance_wave53_receipt_20260730.json"),
    ("priority_4370row_targeted_retry_wave53_diagnostic_20260729.json", "priority_4370row_targeted_retry_wave53_diagnostic_20260730.json"),
]

for old, new in replacements[:4]:
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

if "590" not in text:
    raise SystemExit("EXPECTED_590_TARGET_FRAGMENTS_MISSING")
text = text.replace("590", "4370")

for old, new in replacements[5:]:
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)
