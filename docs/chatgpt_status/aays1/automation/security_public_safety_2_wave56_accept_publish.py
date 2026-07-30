from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()
SOURCE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_wave32_accept_publish.py"

if not SOURCE.is_file():
    raise SystemExit(f"SOURCE_SCRIPT_MISSING: {SOURCE}")

text = SOURCE.read_text(encoding="utf-8")
replacements = [
    ("0007_security_public_safety_2_priority_590row_incremental_evidence_expansion_20260729.v3.task.json", "0031_security_public_safety_2_priority_5270row_incremental_evidence_expansion_20260730.v3.task.json"),
    ("2462ad1cf05576bed958c18cc4a01d7cde54d2c566f5a480c235066eb48012ae", "7cbe62758c9f770da0a6a4c21f0ec4183364cd077caf8dea8c952721b118be38"),
    ("github-actions-security-public-safety-2-wave32", "github-actions-security-public-safety-2-wave56"),
    ("wave32", "wave56"),
    ("590", "5270"),
    ("range(30762, 31352)", "range(30762, 36032)"),
    ("parcel_31351", "parcel_36031"),
    ("MIN_QUALITY = 561", "MIN_QUALITY = 5007"),
    ('"progress_delta_percentage_points": 11.86', '"progress_delta_percentage_points": 5.88'),
    ('"accepted_base_candidate_rows": 520', '"accepted_base_candidate_rows": 4960'),
    ('"incremental_rows_target": 70', '"incremental_rows_target": 310'),
    ('"incremental_rows_completed": 70', '"incremental_rows_completed": 310'),
    ("security_public_safety_2_priority_5270row_incremental_evidence_expansion_20260729", "security_public_safety_2_priority_5270row_incremental_evidence_expansion_20260730"),
    ("priority_5270row_browser_acceptance_wave56_receipt_20260729.json", "priority_5270row_browser_acceptance_wave56_receipt_20260730.json"),
    ("priority_5270row_targeted_retry_wave56_diagnostic_20260729.json", "priority_5270row_targeted_retry_wave56_diagnostic_20260730.json"),
]

for old, new in replacements[:4]:
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

if "590" not in text:
    raise SystemExit("EXPECTED_590_TARGET_FRAGMENTS_MISSING")
text = text.replace("590", "5270")

for old, new in replacements[5:]:
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)

old_gate = '    if any(gate.get("state") != "PASS" for gate in gates[:12]):\n        raise SystemExit("PRE_BROWSER_GATES_FAILED")'
new_gate = '    failed_gates = [gate for gate in gates[:12] if gate.get("state") != "PASS"]\n    if failed_gates:\n        print("PRE_BROWSER_FAILED_GATES=" + __import__("json").dumps(failed_gates, ensure_ascii=False, sort_keys=True))\n        raise SystemExit("PRE_BROWSER_GATES_FAILED")'
if old_gate not in text:
    raise SystemExit("PRE_BROWSER_GATE_FRAGMENT_MISSING")
text = text.replace(old_gate, new_gate)

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)
