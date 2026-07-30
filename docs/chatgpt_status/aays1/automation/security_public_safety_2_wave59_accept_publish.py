from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()
SOURCE = ROOT / "docs/chatgpt_status/aays1/automation/security_public_safety_2_wave32_accept_publish.py"

if not SOURCE.is_file():
    raise SystemExit(f"SOURCE_SCRIPT_MISSING: {SOURCE}")

text = SOURCE.read_text(encoding="utf-8")


def replace_required(old: str, new: str) -> None:
    global text
    if old not in text:
        raise SystemExit(f"EXPECTED_SOURCE_FRAGMENT_MISSING: {old}")
    text = text.replace(old, new)


# Replace the generic 590 target before fixing the resulting queue/date paths.
replace_required("590", "6260")
replace_required(
    "0007_security_public_safety_2_priority_6260row_incremental_evidence_expansion_20260729.v3.task.json",
    "0034_security_public_safety_2_priority_6260row_incremental_evidence_expansion_20260730.v3.task.json",
)
replace_required(
    "2462ad1cf05576bed958c18cc4a01d7cde54d2c566f5a480c235066eb48012ae",
    "220b1fba5c7fd0924991b3203768853571efbf30c0cf836bbc65d8341dad050c",
)
replace_required("wave32", "wave59")
replace_required("range(30762, 31352)", "range(30762, 37022)")
replace_required("parcel_31351", "parcel_37021")
replace_required("MIN_QUALITY = 561", "MIN_QUALITY = 5947")
replace_required('"progress_delta_percentage_points": 11.86', '"progress_delta_percentage_points": 5.43')
replace_required('"accepted_base_candidate_rows": 520', '"accepted_base_candidate_rows": 5920')
replace_required('"incremental_rows_target": 70', '"incremental_rows_target": 340')
replace_required('"incremental_rows_completed": 70', '"incremental_rows_completed": 340')
replace_required(
    "security_public_safety_2_priority_6260row_incremental_evidence_expansion_20260729",
    "security_public_safety_2_priority_6260row_incremental_evidence_expansion_20260730",
)
replace_required(
    "priority_6260row_browser_acceptance_wave59_receipt_20260729.json",
    "priority_6260row_browser_acceptance_wave59_receipt_20260730.json",
)
replace_required(
    "priority_6260row_targeted_retry_wave59_diagnostic_20260729.json",
    "priority_6260row_targeted_retry_wave59_diagnostic_20260730.json",
)

old_gate = '    if any(gate.get("state") != "PASS" for gate in gates[:12]):\n        raise SystemExit("PRE_BROWSER_GATES_FAILED")'
new_gate = '    failed_gates = [gate for gate in gates[:12] if gate.get("state") != "PASS"]\n    if failed_gates:\n        print("PRE_BROWSER_FAILED_GATES=" + __import__("json").dumps(failed_gates, ensure_ascii=False, sort_keys=True))\n        raise SystemExit("PRE_BROWSER_GATES_FAILED")'
replace_required(old_gate, new_gate)

namespace = {"__name__": "__main__", "__file__": str(SOURCE), "__package__": None}
exec(compile(text, str(SOURCE), "exec"), namespace, namespace)
