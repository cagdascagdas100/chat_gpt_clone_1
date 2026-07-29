from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()
SOURCE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_wave32_accept_publish.py"

if not SOURCE.is_file():
    raise SystemExit(f"SOURCE_SCRIPT_MISSING: {SOURCE}")

text = SOURCE.read_text(encoding="utf-8")
replacements = [
    ("0007_security_public_safety_2_priority_590row_incremental_evidence_expansion_20260729.v3.task.json", "0022_security_public_safety_2_priority_2840row_incremental_evidence_expansion_20260730.v3.task.json"),
    ("2462ad1cf05576bed958c18cc4a01d7cde54d2c566f5a480c235066eb48012ae", "8f70543b3bb9e09eabe14fa6e19eba264710575217d1f9f2d4af27601cfa5c87"),
    ("github-actions-security-public-safety-2-wave32", "github-actions-security-public-safety-2-wave47"),
    ("wave32", "wave47"),
    ("590", "2840"),
    ("range(30762, 31352)", "range(30762, 33602)"),
    ("parcel_31351", "parcel_33601"),
    ("MIN_QUALITY = 561", "MIN_QUALITY = 2698"),
    ('"progress_delta_percentage_points": 11.86', '"progress_delta_percentage_points": 7.75'),
    ('"accepted_base_candidate_rows": 520', '"accepted_base_candidate_rows": 2620'),
    ('"incremental_rows_target": 70', '"incremental_rows_target": 220'),
    ('"incremental_rows_completed": 70', '"incremental_rows_completed": 220'),
    ("priority_2840row_browser_acceptance_wave47_receipt_20260729.json", "priority_2840row_browser_acceptance_wave47_receipt_20260730.json"),
    ("priority_2840row_targeted_retry_wave47_diagnostic_20260729.json", "priority_2840row_targeted_retry_wave47_diagnostic_20260730.json"),
]

for old, new in replacements[:4]:
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

if "590" not in text:
    raise SystemExit("EXPECTED_590_TARGET_FRAGMENTS_MISSING")
text = text.replace("590", "2840")

for old, new in replacements[5:]:
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)
