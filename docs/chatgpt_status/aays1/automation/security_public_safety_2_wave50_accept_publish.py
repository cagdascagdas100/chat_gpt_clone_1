from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()
SOURCE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_wave32_accept_publish.py"

if not SOURCE.is_file():
    raise SystemExit(f"SOURCE_SCRIPT_MISSING: {SOURCE}")

text = SOURCE.read_text(encoding="utf-8")
replacements = [
    ("0007_security_public_safety_2_priority_590row_incremental_evidence_expansion_20260729.v3.task.json", "0025_security_public_safety_2_priority_3560row_incremental_evidence_expansion_20260730.v3.task.json"),
    ("2462ad1cf05576bed958c18cc4a01d7cde54d2c566f5a480c235066eb48012ae", "0de828f504b2c74701e50d2415d3c715d110c46495c45a36c7489525c8694e11"),
    ("github-actions-security-public-safety-2-wave32", "github-actions-security-public-safety-2-wave50"),
    ("wave32", "wave50"),
    ("590", "3560"),
    ("range(30762, 31352)", "range(30762, 34322)"),
    ("parcel_31351", "parcel_34321"),
    ("MIN_QUALITY = 561", "MIN_QUALITY = 3382"),
    ('"progress_delta_percentage_points": 11.86', '"progress_delta_percentage_points": 7.02'),
    ('"accepted_base_candidate_rows": 520', '"accepted_base_candidate_rows": 3310'),
    ('"incremental_rows_target": 70', '"incremental_rows_target": 250'),
    ('"incremental_rows_completed": 70', '"incremental_rows_completed": 250'),
    ("security_public_safety_2_priority_3560row_incremental_evidence_expansion_20260729", "security_public_safety_2_priority_3560row_incremental_evidence_expansion_20260730"),
    ("priority_3560row_browser_acceptance_wave50_receipt_20260729.json", "priority_3560row_browser_acceptance_wave50_receipt_20260730.json"),
    ("priority_3560row_targeted_retry_wave50_diagnostic_20260729.json", "priority_3560row_targeted_retry_wave50_diagnostic_20260730.json"),
]

for old, new in replacements[:4]:
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

if "590" not in text:
    raise SystemExit("EXPECTED_590_TARGET_FRAGMENTS_MISSING")
text = text.replace("590", "3560")

for old, new in replacements[5:]:
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)
