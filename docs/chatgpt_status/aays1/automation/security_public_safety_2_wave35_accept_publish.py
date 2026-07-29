from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()
SOURCE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_wave32_accept_publish.py"

if not SOURCE.is_file():
    raise SystemExit(f"SOURCE_SCRIPT_MISSING: {SOURCE}")

text = SOURCE.read_text(encoding="utf-8")
replacements = [
    ("0007_security_public_safety_2_priority_590row_incremental_evidence_expansion_20260729.v3.task.json", "0010_security_public_safety_2_priority_860row_incremental_evidence_expansion_20260729.v3.task.json"),
    ("2462ad1cf05576bed958c18cc4a01d7cde54d2c566f5a480c235066eb48012ae", "187a9cc6667f2e934790c99a6d810be21ed9b2cc2e478b687276f5a4be205c67"),
    ("github-actions-security-public-safety-2-wave32", "github-actions-security-public-safety-2-wave35"),
    ("wave32", "wave35"),
    ("590", "860"),
    ("range(30762, 31352)", "range(30762, 31622)"),
    ("parcel_31351", "parcel_31621"),
    ("MIN_QUALITY = 561", "MIN_QUALITY = 817"),
    ('"progress_delta_percentage_points": 11.86', '"progress_delta_percentage_points": 11.63'),
    ('"accepted_base_candidate_rows": 520', '"accepted_base_candidate_rows": 760'),
    ('"incremental_rows_target": 70', '"incremental_rows_target": 100'),
    ('"incremental_rows_completed": 70', '"incremental_rows_completed": 100'),
]

for old, new in replacements[:4]:
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

if "590" not in text:
    raise SystemExit("EXPECTED_590_TARGET_FRAGMENTS_MISSING")
text = text.replace("590", "860")

for old, new in replacements[5:]:
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)
