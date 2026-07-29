from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()
SOURCE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_wave32_accept_publish.py"

if not SOURCE.is_file():
    raise SystemExit(f"SOURCE_SCRIPT_MISSING: {SOURCE}")

text = SOURCE.read_text(encoding="utf-8")
replacements = [
    ("0007_security_public_safety_2_priority_590row_incremental_evidence_expansion_20260729.v3.task.json", "0018_security_public_safety_2_priority_2020row_incremental_evidence_expansion_20260729.v3.task.json"),
    ("2462ad1cf05576bed958c18cc4a01d7cde54d2c566f5a480c235066eb48012ae", "1bdfb90c6111418ed5bdcace82662e50ae4d7d4e956a0e134c7fb2701f85f8d5"),
    ("github-actions-security-public-safety-2-wave32", "github-actions-security-public-safety-2-wave43"),
    ("wave32", "wave43"),
    ("590", "2020"),
    ("range(30762, 31352)", "range(30762, 32782)"),
    ("parcel_31351", "parcel_32781"),
    ("MIN_QUALITY = 561", "MIN_QUALITY = 1919"),
    ('"progress_delta_percentage_points": 11.86', '"progress_delta_percentage_points": 8.91'),
    ('"accepted_base_candidate_rows": 520', '"accepted_base_candidate_rows": 1840'),
    ('"incremental_rows_target": 70', '"incremental_rows_target": 180'),
    ('"incremental_rows_completed": 70', '"incremental_rows_completed": 180'),
]

for old, new in replacements[:4]:
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

if "590" not in text:
    raise SystemExit("EXPECTED_590_TARGET_FRAGMENTS_MISSING")
text = text.replace("590", "2020")

for old, new in replacements[5:]:
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)
