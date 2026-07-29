from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()
SOURCE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_wave32_accept_publish.py"

if not SOURCE.is_file():
    raise SystemExit(f"SOURCE_SCRIPT_MISSING: {SOURCE}")

text = SOURCE.read_text(encoding="utf-8")
replacements = [
    ("0007_security_public_safety_2_priority_590row_incremental_evidence_expansion_20260729.v3.task.json", "0024_security_public_safety_2_priority_3310row_incremental_evidence_expansion_20260730.v3.task.json"),
    ("2462ad1cf05576bed958c18cc4a01d7cde54d2c566f5a480c235066eb48012ae", "365e340bc9f7e40a9c960abf4299d7036ddeb8e618ef21d09a0ab0b2bcb2a5ea"),
    ("github-actions-security-public-safety-2-wave32", "github-actions-security-public-safety-2-wave49"),
    ("wave32", "wave49"),
    ("590", "3310"),
    ("range(30762, 31352)", "range(30762, 34072)"),
    ("parcel_31351", "parcel_34071"),
    ("MIN_QUALITY = 561", "MIN_QUALITY = 3145"),
    ('"progress_delta_percentage_points": 11.86', '"progress_delta_percentage_points": 7.25'),
    ('"accepted_base_candidate_rows": 520', '"accepted_base_candidate_rows": 3070'),
    ('"incremental_rows_target": 70', '"incremental_rows_target": 240'),
    ('"incremental_rows_completed": 70', '"incremental_rows_completed": 240'),
    ("security_public_safety_2_priority_3310row_incremental_evidence_expansion_20260729", "security_public_safety_2_priority_3310row_incremental_evidence_expansion_20260730"),
    ("priority_3310row_browser_acceptance_wave49_receipt_20260729.json", "priority_3310row_browser_acceptance_wave49_receipt_20260730.json"),
    ("priority_3310row_targeted_retry_wave49_diagnostic_20260729.json", "priority_3310row_targeted_retry_wave49_diagnostic_20260730.json"),
]

for old, new in replacements[:4]:
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

if "590" not in text:
    raise SystemExit("EXPECTED_590_TARGET_FRAGMENTS_MISSING")
text = text.replace("590", "3310")

for old, new in replacements[5:]:
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)
