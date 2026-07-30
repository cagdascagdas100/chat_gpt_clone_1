from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()
SOURCE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_wave32_accept_publish.py"

if not SOURCE.is_file():
    raise SystemExit(f"SOURCE_SCRIPT_MISSING: {SOURCE}")

text = SOURCE.read_text(encoding="utf-8")
replacements = [
    ("0007_security_public_safety_2_priority_590row_incremental_evidence_expansion_20260729.v3.task.json", "0037_security_public_safety_2_priority_7340row_incremental_evidence_expansion_20260730.v3.task.json"),
    ("2462ad1cf05576bed958c18cc4a01d7cde54d2c566f5a480c235066eb48012ae", "6caf87b26dd9c91bae533642684b4d4e4db47145de0ef5ed36a8d9a392cecd4d"),
    ("github-actions-security-public-safety-2-wave32", "github-actions-security-public-safety-2-wave62"),
    ("wave32", "wave62"),
]
for old, new in replacements:
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

if "590" not in text:
    raise SystemExit("EXPECTED_590_TARGET_FRAGMENTS_MISSING")
text = text.replace("590", "7340")

required_replacements = [
    ("range(30762, 31352)", "range(30762, 38102)"),
    ("parcel_31351", "parcel_38101"),
    ("MIN_QUALITY = 561", "MIN_QUALITY = 6973"),
    ('"progress_delta_percentage_points": 11.86', '"progress_delta_percentage_points": 5.04'),
    ('"accepted_base_candidate_rows": 520', '"accepted_base_candidate_rows": 6970'),
    ('"incremental_rows_target": 70', '"incremental_rows_target": 370'),
    ('"incremental_rows_completed": 70', '"incremental_rows_completed": 370'),
    ("security_public_safety_2_priority_7340row_incremental_evidence_expansion_20260729", "security_public_safety_2_priority_7340row_incremental_evidence_expansion_20260730"),
    ("priority_7340row_browser_acceptance_wave62_receipt_20260729.json", "priority_7340row_browser_acceptance_wave62_receipt_20260730.json"),
    ("priority_7340row_targeted_retry_wave62_diagnostic_20260729.json", "priority_7340row_targeted_retry_wave62_diagnostic_20260730.json"),
]
for old, new in required_replacements:
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

old_gate = '    if any(gate.get("state") != "PASS" for gate in gates[:12]):\n        raise SystemExit("PRE_BROWSER_GATES_FAILED")'
new_gate = '    failed_gates = [gate for gate in gates[:12] if gate.get("state") != "PASS"]\n    if failed_gates:\n        print("PRE_BROWSER_FAILED_GATES=" + __import__("json").dumps(failed_gates, ensure_ascii=False, sort_keys=True))\n        raise SystemExit("PRE_BROWSER_GATES_FAILED")'
if old_gate in text:
    text = text.replace(old_gate, new_gate)

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)
