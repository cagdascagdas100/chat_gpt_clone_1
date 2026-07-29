from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()
SOURCE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_wave32_accept_publish.py"

if not SOURCE.is_file():
    raise SystemExit(f"SOURCE_SCRIPT_MISSING: {SOURCE}")

text = SOURCE.read_text(encoding="utf-8")
replacements = [
    ("0007_security_public_safety_2_priority_590row_incremental_evidence_expansion_20260729.v3.task.json", "0015_security_public_safety_2_priority_1510row_incremental_evidence_expansion_20260729.v3.task.json"),
    ("2462ad1cf05576bed958c18cc4a01d7cde54d2c566f5a480c235066eb48012ae", "21b1f8638e05ea789709fba734926a907073903f7924f0ea457962c38e69d112"),
    ("github-actions-security-public-safety-2-wave32", "github-actions-security-public-safety-2-wave40"),
    ("wave32", "wave40"),
    ("590", "1510"),
    ("range(30762, 31352)", "range(30762, 32272)"),
    ("parcel_31351", "parcel_32271"),
    ("MIN_QUALITY = 561", "MIN_QUALITY = 1435"),
    ('"progress_delta_percentage_points": 11.86', '"progress_delta_percentage_points": 9.93'),
    ('"accepted_base_candidate_rows": 520', '"accepted_base_candidate_rows": 1360'),
    ('"incremental_rows_target": 70', '"incremental_rows_target": 150'),
    ('"incremental_rows_completed": 70', '"incremental_rows_completed": 150'),
]

for old, new in replacements[:4]:
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

if "590" not in text:
    raise SystemExit("EXPECTED_590_TARGET_FRAGMENTS_MISSING")
text = text.replace("590", "1510")

for old, new in replacements[5:]:
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)
