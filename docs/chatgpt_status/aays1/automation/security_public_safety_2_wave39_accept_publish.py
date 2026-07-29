from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()
SOURCE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_wave32_accept_publish.py"

if not SOURCE.is_file():
    raise SystemExit(f"SOURCE_SCRIPT_MISSING: {SOURCE}")

text = SOURCE.read_text(encoding="utf-8")
replacements = [
    ("0007_security_public_safety_2_priority_590row_incremental_evidence_expansion_20260729.v3.task.json", "0014_security_public_safety_2_priority_1360row_incremental_evidence_expansion_20260729.v3.task.json"),
    ("2462ad1cf05576bed958c18cc4a01d7cde54d2c566f5a480c235066eb48012ae", "fb0a0130b93f3d4a7f54d3e6efd6bbe57e1abdef9d919896cf9070c373d57cf6"),
    ("github-actions-security-public-safety-2-wave32", "github-actions-security-public-safety-2-wave39"),
    ("wave32", "wave39"),
    ("590", "1360"),
    ("range(30762, 31352)", "range(30762, 32122)"),
    ("parcel_31351", "parcel_32121"),
    ("MIN_QUALITY = 561", "MIN_QUALITY = 1292"),
    ('"progress_delta_percentage_points": 11.86', '"progress_delta_percentage_points": 10.29'),
    ('"accepted_base_candidate_rows": 520', '"accepted_base_candidate_rows": 1220'),
    ('"incremental_rows_target": 70', '"incremental_rows_target": 140'),
    ('"incremental_rows_completed": 70', '"incremental_rows_completed": 140'),
]

for old, new in replacements[:4]:
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

if "590" not in text:
    raise SystemExit("EXPECTED_590_TARGET_FRAGMENTS_MISSING")
text = text.replace("590", "1360")

for old, new in replacements[5:]:
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)
